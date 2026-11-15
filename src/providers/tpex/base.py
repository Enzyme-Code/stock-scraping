from typing import Any, Dict, List
from curl_cffi import requests

from ..handler.base import BaseProvider
from ..handler.model import InstitutionalInvestorItem, MarginTradingItem, StockPriceItem
from ..utils import clean_text, format_iso_date, to_float, to_int, to_iso_date


class Base(BaseProvider):
    """TPEx (櫃買中心) 專用基底類別，負責底層 HTTP 請求、重試機制與 JSON 資料解析。"""

    TRADING_STOCK_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"
    )
    INSTI_DAILY_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade"
    )
    MARGIN_BALANCE_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/margin/balance"
    )
    MARGIN_SBL_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/margin/sbl"
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

    def _fetch_institutional_investors_json(self, query_date: str) -> Dict[str, Any]:
        """發送 GET 請求至 TPEx insti/dailyTrade API 取得指定日期的三大法人買賣超日報 JSON。"""
        params = {
            "type": "Daily",
            "sect": "AL",
            "date": query_date,
            "id": "",
            "response": "json",
        }
        response = self._request("GET", self.INSTI_DAILY_URL, params=params)
        return response.json()

    def _parse_institutional_investors(
        self, data: Dict[str, Any], iso_date: str
    ) -> List[Dict[str, Any]]:
        """
        解析 TPEx insti/dailyTrade JSON 並清洗為 list[dict] 格式。
        略過 row[8..10] (外資合計)、row[20..22] (自營商合計) 與 row[23] (三大法人合計) 欄位。
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
            if not isinstance(row, list) or len(row) < 20:
                continue

            symbol = clean_text(row[0])
            name = clean_text(row[1])
            vals = [
                to_int(row[2]),   # foreign_buy
                to_int(row[3]),   # foreign_sell
                to_int(row[5]),   # foreign_dealer_buy
                to_int(row[6]),   # foreign_dealer_sell
                to_int(row[11]),  # trust_buy
                to_int(row[12]),  # trust_sell
                to_int(row[14]),  # dealer_self_buy
                to_int(row[15]),  # dealer_self_sell
                to_int(row[17]),  # dealer_hedge_buy
                to_int(row[18]),  # dealer_hedge_sell
            ]
            if not symbol or any(v is None for v in vals):
                continue

            item = InstitutionalInvestorItem(
                symbol=symbol,
                name=name,
                date=iso_date,
                foreign_buy=vals[0],          # type: ignore[arg-type]
                foreign_sell=vals[1],         # type: ignore[arg-type]
                foreign_dealer_buy=vals[2],   # type: ignore[arg-type]
                foreign_dealer_sell=vals[3],  # type: ignore[arg-type]
                trust_buy=vals[4],            # type: ignore[arg-type]
                trust_sell=vals[5],           # type: ignore[arg-type]
                dealer_self_buy=vals[6],      # type: ignore[arg-type]
                dealer_self_sell=vals[7],     # type: ignore[arg-type]
                dealer_hedge_buy=vals[8],     # type: ignore[arg-type]
                dealer_hedge_sell=vals[9],    # type: ignore[arg-type]
            )
            results.append(item.to_dict())

        return results

    def _get_institutional_investors(self, date: str) -> List[Dict[str, Any]]:
        """抓取並解析指定交易日的上櫃三大法人買賣超日報。"""
        query_date = format_iso_date(date, "%Y/%m/%d")
        iso_date = format_iso_date(date, "%Y-%m-%d")
        raw_json = self._fetch_institutional_investors_json(query_date=query_date)
        return self._parse_institutional_investors(data=raw_json, iso_date=iso_date)

    def _fetch_margin_trading_json(self, query_date: str) -> Dict[str, Any]:
        """發送 GET 請求至 TPEx margin/balance API 取得指定日期的上櫃股票融資融券餘額 JSON。"""
        params = {
            "date": query_date,
            "id": "",
            "response": "json",
        }
        response = self._request("GET", self.MARGIN_BALANCE_URL, params=params)
        return response.json()

    def _fetch_sbl_json(self, query_date: str) -> Dict[str, Any]:
        """發送 GET 請求至 TPEx margin/sbl API 取得指定日期的上櫃股票融券借券賣出餘額 JSON。"""
        params = {
            "date": query_date,
            "id": "",
            "response": "json",
        }
        response = self._request("GET", self.MARGIN_SBL_URL, params=params)
        return response.json()

    def _parse_margin_table(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        解析 TPEx margin/balance JSON 的個股融資融券明細 (tables[0]['data'])。
        原始單位皆為「張」，統一乘以 1,000 換算為「股」。
        注意：上櫃融券的「券賣 (row[11])」在「券買 (row[12])」前面。
        """
        tables = data.get("tables")
        if not isinstance(tables, list) or not tables:
            return {}

        first_table = tables[0]
        if not isinstance(first_table, dict):
            return {}

        rows = first_table.get("data")
        if not isinstance(rows, list):
            return {}

        margin_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, list) or len(row) < 19:
                continue

            symbol = clean_text(row[0])
            name = clean_text(row[1])
            if not symbol or "合計" in symbol or "總計" in symbol or "合計" in name:
                continue

            margin_map[symbol] = {
                "name": name,
                "margin_prev_balance": to_int(row[2], multiplier=1000) or 0,
                "margin_buy": to_int(row[3], multiplier=1000) or 0,
                "margin_sell": to_int(row[4], multiplier=1000) or 0,
                "margin_cash_repay": to_int(row[5], multiplier=1000) or 0,
                "margin_balance": to_int(row[6], multiplier=1000) or 0,
                "margin_limit": to_int(row[9], multiplier=1000) or 0,
                "short_prev_balance": to_int(row[10], multiplier=1000) or 0,
                "short_sell": to_int(row[11], multiplier=1000) or 0,
                "short_buy": to_int(row[12], multiplier=1000) or 0,
                "short_stock_repay": to_int(row[13], multiplier=1000) or 0,
                "short_balance": to_int(row[14], multiplier=1000) or 0,
                "short_limit": to_int(row[17], multiplier=1000) or 0,
                "offset": to_int(row[18], multiplier=1000) or 0,
            }

        return margin_map

    def _parse_sbl_table(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        解析 TPEx margin/sbl JSON 的個股融券借券賣出明細 (tables[0]['data'])。
        注意：同一列內單位混用！
        - 索引 2~7 的融券欄位原始單位為「張」，乘以 1,000 換算為「股」。
        - 索引 8~13 的借券賣出欄位原始單位即為「股」，不需額外換算。
        """
        tables = data.get("tables")
        if not isinstance(tables, list) or not tables:
            return {}

        first_table = tables[0]
        if not isinstance(first_table, dict):
            return {}

        rows = first_table.get("data")
        if not isinstance(rows, list):
            return {}

        sbl_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, list) or len(row) < 14:
                continue

            symbol = clean_text(row[0])
            name = clean_text(row[1])
            if not symbol or "合計" in symbol or "總計" in symbol or "合計" in name:
                continue

            sbl_map[symbol] = {
                "name": name,
                "short_prev_balance": to_int(row[2], multiplier=1000) or 0,
                "short_sell": to_int(row[3], multiplier=1000) or 0,
                "short_buy": to_int(row[4], multiplier=1000) or 0,
                "short_stock_repay": to_int(row[5], multiplier=1000) or 0,
                "short_balance": to_int(row[6], multiplier=1000) or 0,
                "short_limit": to_int(row[7], multiplier=1000) or 0,
                "sbl_prev_balance": to_int(row[8]) or 0,
                "sbl_sell": to_int(row[9]) or 0,
                "sbl_repay": to_int(row[10]) or 0,
                "sbl_adjust": to_int(row[11]) or 0,
                "sbl_balance": to_int(row[12]) or 0,
                "sbl_limit": to_int(row[13]) or 0,
            }

        return sbl_map

    def _merge_margin_and_sbl(
        self,
        margin_map: Dict[str, Dict[str, Any]],
        sbl_map: Dict[str, Dict[str, Any]],
        iso_date: str,
    ) -> List[Dict[str, Any]]:
        """
        以 symbol 進行融資融券表與借券賣出表的 Outer Join：
        - 融券相關欄位優先取自融資融券表 (margin_map)，若無信用交易資格則由借券賣出表 (sbl_map) 補齊。
        - 借券賣出相關欄位取自借券賣出表 (sbl_map)。
        """
        all_symbols = list(dict.fromkeys(list(margin_map.keys()) + list(sbl_map.keys())))
        results: List[Dict[str, Any]] = []

        for symbol in all_symbols:
            m = margin_map.get(symbol)
            s = sbl_map.get(symbol)
            short_src = m if m is not None else (s or {})

            name = (m["name"] if m and m.get("name") else (s["name"] if s else "")) or ""

            item = MarginTradingItem(
                symbol=symbol,
                name=name,
                date=iso_date,
                margin_buy=m["margin_buy"] if m else 0,
                margin_sell=m["margin_sell"] if m else 0,
                margin_cash_repay=m["margin_cash_repay"] if m else 0,
                margin_prev_balance=m["margin_prev_balance"] if m else 0,
                margin_balance=m["margin_balance"] if m else 0,
                margin_limit=m["margin_limit"] if m else 0,
                short_buy=short_src.get("short_buy", 0),
                short_sell=short_src.get("short_sell", 0),
                short_stock_repay=short_src.get("short_stock_repay", 0),
                short_prev_balance=short_src.get("short_prev_balance", 0),
                short_balance=short_src.get("short_balance", 0),
                short_limit=short_src.get("short_limit", 0),
                offset=m["offset"] if m else 0,
                sbl_prev_balance=s["sbl_prev_balance"] if s else 0,
                sbl_sell=s["sbl_sell"] if s else 0,
                sbl_repay=s["sbl_repay"] if s else 0,
                sbl_adjust=s["sbl_adjust"] if s else 0,
                sbl_balance=s["sbl_balance"] if s else 0,
                sbl_limit=s["sbl_limit"] if s else 0,
            )
            results.append(item.to_dict())

        return results

    def _get_margin_trading(self, date: str) -> List[Dict[str, Any]]:
        """抓取並合併指定交易日的上櫃融資融券 (margin/balance) 與借券賣出 (margin/sbl) 明細。"""
        query_date = format_iso_date(date, "%Y/%m/%d")
        iso_date = format_iso_date(date, "%Y-%m-%d")

        margin_json = self._fetch_margin_trading_json(query_date=query_date)
        sbl_json = self._fetch_sbl_json(query_date=query_date)

        margin_map = self._parse_margin_table(data=margin_json)
        sbl_map = self._parse_sbl_table(data=sbl_json)

        return self._merge_margin_and_sbl(
            margin_map=margin_map,
            sbl_map=sbl_map,
            iso_date=iso_date,
        )
