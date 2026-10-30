from typing import Any, Dict, List
from curl_cffi import requests

from ..handler.base import BaseProvider
from ..handler.model import StockPriceItem
from ..utils import clean_text, format_iso_date, to_float, to_int, to_iso_date


class Base(BaseProvider):
    """TPEx (櫃買中心) 專用基底類別，負責底層 HTTP 請求、重試機制與 JSON 資料解析。"""

    TRADING_STOCK_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"
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

    def _fetch_stock_price_json(self, symbol: str, query_date: str) -> Dict[str, Any]:
        """發送 GET 請求至 TPEx tradingStock API 取得指定月份的個股日成交資訊 JSON。"""
        params = {
            "code": symbol,
            "date": query_date,
            "id": "",
            "response": "json",
        }
        response = self._request("GET", self.TRADING_STOCK_URL, params=params)
        return response.json()

    def _parse_stock_price(
        self, data: Dict[str, Any], symbol: str
    ) -> List[Dict[str, Any]]:
        """
        解析 TPEx tradingStock JSON 並清洗為 list[dict] 格式。
        原始「成交仟股」與「成交仟元」皆乘以 1000 統一轉為「股」與「元」。
        """
        tables = data.get("tables")
        if not isinstance(tables, list) or not tables:
            return []

        first_table = tables[0]
        if not isinstance(first_table, dict):
            return []

        rows = first_table.get("data")
        if not isinstance(rows, list):
            return []

        results: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 9:
                continue

            iso_date = to_iso_date(row[0])
            volume = to_int(row[1], multiplier=1000)
            value = to_int(row[2], multiplier=1000)
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
        """抓取並解析指定上櫃股票代號與日期（所屬月份）的個股日成交資訊。"""
        cleaned_symbol = clean_text(symbol)
        if not cleaned_symbol:
            raise ValueError("symbol cannot be empty.")

        query_date = format_iso_date(date, "%Y/%m/01")
        raw_json = self._fetch_stock_price_json(symbol=cleaned_symbol, query_date=query_date)
        return self._parse_stock_price(data=raw_json, symbol=cleaned_symbol)
