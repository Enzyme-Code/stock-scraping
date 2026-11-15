import json
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from curl_cffi import requests

from ..handler.base import BaseProvider
from ..utils import clean_text, to_int, to_iso_date
from .model import (
    SideLiteral,
    YahooBrokerTradingItem,
    normalize_symbol,
)


class Base(BaseProvider):
    """Yahoo 奇摩股市專用基底類別，負責底層 HTTP 請求、SSR Store JSON 提取與 HTML Fallback 解析。"""

    BROKER_TRADING_URL_TEMPLATE: str = (
        "https://tw.stock.yahoo.com/quote/{symbol}/broker-trading"
    )

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """發送帶有自動重試、User-Agent 輪替與延遲等待的 HTTP 請求。"""
        for attempt in range(1, self.max_retries + 1):
            try:
                self._debug(f"{method.upper()} {url} (attempt {attempt}/{self.max_retries})")
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs,
                )
                response.raise_for_status()
                self._sleep()
                return response
            except Exception as exc:
                self._debug(f"Request failed on attempt {attempt}: {exc}")
                if attempt == self.max_retries:
                    raise
                self._rotate_user_agent()
                self._retry_sleep(attempt)

        raise RuntimeError(f"Unreachable retry state for {url}")

    @staticmethod
    def _normalize_broker_name(raw_name: Optional[str]) -> str:
        """正規化券商分點名稱：清除前後全半形空白，並將全形連字號統一轉為半形 '-'。"""
        cleaned = clean_text(raw_name)
        if not cleaned:
            return ""
        cleaned = re.sub(r"[－—–﹣]", "-", cleaned)
        cleaned = re.sub(r"\s*-\s*", "-", cleaned)
        return cleaned

    @staticmethod
    def _extract_iso_date(raw_date: Optional[str]) -> Optional[str]:
        """從 Yahoo 的日期字串（如 '2026-11-13T00:00:00+08:00' 或 '2026/11/13'）提取 YYYY-MM-DD。"""
        cleaned = clean_text(raw_date)
        if not cleaned:
            return None
        if "T" in cleaned:
            cleaned = cleaned.split("T", 1)[0]
        date_match = re.search(r"\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}", cleaned)
        if date_match:
            return to_iso_date(date_match.group(0))
        return to_iso_date(cleaned)

    def _fetch_broker_trading_html(self, symbol: str) -> str:
        """發送 GET 請求取得指定股票的 Yahoo 主力進出頁面 HTML。"""
        url = self.BROKER_TRADING_URL_TEMPLATE.format(symbol=symbol)
        response = self._request("GET", url)
        return response.text

    def _parse_from_app_main(
        self, html: str, symbol: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        優先從頁面內嵌的 `root.App.main` SSR JSON 提取 `QuoteChipStore.brokerTrades.data`。
        若頁面不存在 `root.App.main` 結構則回傳 None 以觸發 HTML DOM Fallback。
        """
        match = re.search(r"root\.App\.main\s*=\s*(\{.*?\});\s*\n", html)
        if not match:
            match = re.search(r"root\.App\.main\s*=\s*(\{.*\});", html)
        if not match:
            return None

        raw_json = re.sub(r":\s*undefined\b", ":null", match.group(1))
        try:
            app_data = json.loads(raw_json)
        except json.JSONDecodeError:
            return None

        try:
            broker_data = (
                app_data["context"]["dispatcher"]["stores"]["QuoteChipStore"][
                    "brokerTrades"
                ]["data"]
            )
        except (KeyError, TypeError):
            return None

        if not isinstance(broker_data, dict) or not broker_data:
            return []

        iso_date = self._extract_iso_date(broker_data.get("date"))
        if not iso_date:
            return []

        results: List[Dict[str, Any]] = []
        side_configs: List[tuple[SideLiteral, str]] = [
            ("buy", "buyerRankList"),
            ("sell", "sellerRankList"),
        ]

        for side, list_key in side_configs:
            rank_list = broker_data.get(list_key)
            if not isinstance(rank_list, list):
                continue

            for idx, entry in enumerate(rank_list, start=1):
                if not isinstance(entry, dict):
                    continue

                broker_name = self._normalize_broker_name(entry.get("name"))
                if not broker_name:
                    continue

                rank = to_int(entry.get("rank")) or idx
                buy_volume = to_int(entry.get("buyVolK"), multiplier=1000) or 0
                sell_volume = to_int(entry.get("sellVolK"), multiplier=1000) or 0

                item = YahooBrokerTradingItem(
                    symbol=symbol,
                    date=iso_date,
                    side=side,
                    rank=rank,
                    broker_name=broker_name,
                    buy_volume=buy_volume,
                    sell_volume=sell_volume,
                )
                results.append(item.to_dict())

        return results

    def _parse_from_html_dom(self, html: str, symbol: str) -> List[Dict[str, Any]]:
        """
        當 `root.App.main` 不存在或結構異動時的備援解析器：直接解析 SSR HTML 的 `<time>` 與買賣超券商列表。
        """
        soup = BeautifulSoup(html, "lxml")

        iso_date: Optional[str] = None
        for time_tag in soup.find_all("time"):
            raw_attr = time_tag.get("datatime") or time_tag.get("datetime") or time_tag.get_text()
            iso_date = self._extract_iso_date(str(raw_attr))
            if iso_date:
                break

        if not iso_date:
            return []

        results: List[Dict[str, Any]] = []
        header_configs: List[tuple[SideLiteral, str]] = [
            ("buy", "買超券商"),
            ("sell", "賣超券商"),
        ]

        for side, header_label in header_configs:
            header_span = soup.find("span", string=re.compile(rf"^\s*{header_label}\s*$"))
            if not header_span:
                continue

            header_row = header_span.find_parent("div")
            if not header_row:
                continue

            rank = 0
            for row_div in header_row.find_next_siblings("div"):
                spans = row_div.find_all("span", recursive=False)
                if len(spans) < 3:
                    continue

                broker_name = self._normalize_broker_name(spans[0].get_text())
                if not broker_name:
                    continue

                rank += 1
                buy_volume = to_int(spans[1].get_text(), multiplier=1000) or 0
                sell_volume = to_int(spans[2].get_text(), multiplier=1000) or 0

                item = YahooBrokerTradingItem(
                    symbol=symbol,
                    date=iso_date,
                    side=side,
                    rank=rank,
                    broker_name=broker_name,
                    buy_volume=buy_volume,
                    sell_volume=sell_volume,
                )
                results.append(item.to_dict())

        return results

    def _parse_broker_trading(self, html: str, symbol: str) -> List[Dict[str, Any]]:
        """解析 Yahoo 股市主力進出頁面（優先使用 SSR Store JSON，失敗時退回 HTML DOM 解析）。"""
        store_results = self._parse_from_app_main(html=html, symbol=symbol)
        if store_results is not None:
            return store_results
        return self._parse_from_html_dom(html=html, symbol=symbol)

    def _get_broker_trading(self, symbol: str) -> List[Dict[str, Any]]:
        """抓取並解析指定上市或上櫃股票的當日主力分點買賣超排行。"""
        clean_symbol = normalize_symbol(symbol=symbol)
        html = self._fetch_broker_trading_html(symbol=clean_symbol)
        return self._parse_broker_trading(html=html, symbol=clean_symbol)
