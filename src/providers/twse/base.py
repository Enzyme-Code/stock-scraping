from typing import Any, Dict, List
from bs4 import BeautifulSoup
from curl_cffi import requests

from ..handler.base import BaseProvider
from ..handler.model import StockPriceItem
from ..utils import clean_text, format_iso_date, split_symbol_name, to_float, to_int, to_iso_date
from .model import (
    MarketLiteral,
    SECTION_TO_TYPE,
    TwseSecurityItem,
    resolve_str_modes,
)


class Base(BaseProvider):
    """TWSE 專用基底類別，負責底層 HTTP 請求、重試機制與 HTML/JSON 資料解析。"""

    ISIN_URL: str = "https://isin.twse.com.tw/isin/C_public.jsp"
    STOCK_DAY_URL: str = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"

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

    def _fetch_isin_html(self, str_mode: int) -> str:
        """
        抓取國際證券辨識號碼一覽表 HTML：
        - str_mode=2: 本國上市證券 (twse)
        - str_mode=4: 本國上櫃證券 (tpex)
        - str_mode=5: 本國興櫃證券 (esb)
        """
        response = self._request("GET", self.ISIN_URL, params={"strMode": str_mode})
        return response.content.decode("cp950", errors="replace")

    def _parse_isin_table(
        self, html: str, str_mode: int = 2
    ) -> List[Dict[str, Any]]:
        """解析 ISIN 網頁表格並清洗為 list[dict] 格式。"""
        soup = BeautifulSoup(html, "lxml")

        results: List[Dict[str, Any]] = []
        # 興櫃 (strMode=5) 表格沒有 <td colspan=7> 分類標題列，整張表皆為股票 ('stock')
        current_type: str = "stock" if str_mode == 5 else ""

        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue

            # 分類標題列 (例如 <td colspan="7"><B> 股票 <B></td>)
            if len(tds) == 1 or tds[0].get("colspan"):
                section_title = clean_text(tds[0].get_text())
                current_type = SECTION_TO_TYPE.get(section_title, "")
                continue

            # 資料列共有 7 個欄位，且略過表頭列
            if len(tds) != 7:
                continue

            first_col_text = clean_text(tds[0].get_text())
            if first_col_text.startswith("有價證券代號"):
                continue

            # 若目前區塊不在定義的分類內則跳過
            if not current_type:
                continue

            symbol, name = split_symbol_name(tds[0].get_text())
            isin_code = clean_text(tds[1].get_text())
            listing_date = to_iso_date(tds[2].get_text())
            market = clean_text(tds[3].get_text())
            industry = clean_text(tds[4].get_text()) or None
            cfi_code = clean_text(tds[5].get_text())

            item = TwseSecurityItem(
                symbol=symbol,
                name=name,
                type=current_type,
                isin_code=isin_code,
                listing_date=listing_date,
                market=market,
                industry=industry,
                cfi_code=cfi_code,
            )
            results.append(item.to_dict())

        return results

    def _get_list(
        self,
        market: MarketLiteral = "all",
    ) -> List[Dict[str, Any]]:
        """依 market 抓取並解析對應的 ISIN 清單。"""
        str_modes = resolve_str_modes(market)
        results: List[Dict[str, Any]] = []

        for mode in str_modes:
            html = self._fetch_isin_html(str_mode=mode)
            items = self._parse_isin_table(html=html, str_mode=mode)
            results.extend(items)

        return results

    def _fetch_stock_price_json(self, symbol: str, query_date: str) -> Dict[str, Any]:
        """發送 GET 請求至 TWSE STOCK_DAY API 取得指定月份的個股日成交資訊 JSON。"""
        params = {
            "date": query_date,
            "stockNo": symbol,
            "response": "json",
        }
        response = self._request("GET", self.STOCK_DAY_URL, params=params)
        return response.json()

    def _parse_stock_price(
        self, data: Dict[str, Any], symbol: str
    ) -> List[Dict[str, Any]]:
        """解析 TWSE STOCK_DAY JSON 並清洗為 list[dict] 格式。"""
        if data.get("stat") != "OK":
            return []

        rows = data.get("data")
        if not isinstance(rows, list):
            return []

        results: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 9:
                continue

            iso_date = to_iso_date(row[0])
            volume = to_int(row[1])
            value = to_int(row[2])
            open_p = to_float(row[3])
            high_p = to_float(row[4])
            low_p = to_float(row[5])
            close_p = to_float(row[6])
            change = to_float(row[7])
            transaction = to_int(row[8])

            if (
                iso_date is None
                or volume is None
                or value is None
                or open_p is None
                or high_p is None
                or low_p is None
                or close_p is None
                or change is None
                or transaction is None
            ):
                continue

            item = StockPriceItem(
                symbol=symbol,
                date=iso_date,
                volume=volume,
                value=value,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                price_change=change,
                transaction=transaction,
            )
            results.append(item.to_dict())

        return results

    def _get_stock_price(self, symbol: str, date: str) -> List[Dict[str, Any]]:
        """抓取並解析指定上市股票代號與日期（所屬月份）的個股日成交資訊。"""
        cleaned_symbol = clean_text(symbol)
        if not cleaned_symbol:
            raise ValueError("symbol cannot be empty.")

        query_date = format_iso_date(date, "%Y%m01")
        raw_json = self._fetch_stock_price_json(symbol=cleaned_symbol, query_date=query_date)
        return self._parse_stock_price(data=raw_json, symbol=cleaned_symbol)
