from typing import Any, Dict, List, Optional

from ..handler.base import BaseProvider
from ..handler.model import (
    ExRightAnnouncementItem,
    ExRightResultItem,
    InstitutionalInvestorItem,
    StockPriceItem,
)
from ..utils import (
    clean_text,
    format_iso_date,
    merge_margin_and_sbl,
    normalize_ex_type,
    to_float,
    to_int,
    to_iso_date,
)


class Base(BaseProvider):
    """TPEx (櫃買中心) 專用基底類別，負責底層 HTTP 請求與 JSON 資料解析。"""

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
    EX_RIGHT_PREPOST_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/bulletin/prePost"
    )
    EX_RIGHT_DAILY_URL: str = (
        "https://www.tpex.org.tw/www/zh-tw/bulletin/exDailyQ"
    )

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

    def _get_margin_trading(self, date: str) -> List[Dict[str, Any]]:
        """抓取並合併指定交易日的上櫃融資融券 (margin/balance) 與借券賣出 (margin/sbl) 明細。"""
        query_date = format_iso_date(date, "%Y/%m/%d")
        iso_date = format_iso_date(date, "%Y-%m-%d")

        margin_json = self._fetch_margin_trading_json(query_date=query_date)
        sbl_json = self._fetch_sbl_json(query_date=query_date)

        margin_map = self._parse_margin_table(data=margin_json)
        sbl_map = self._parse_sbl_table(data=sbl_json)

        return merge_margin_and_sbl(
            margin_map=margin_map,
            sbl_map=sbl_map,
            iso_date=iso_date,
        )

    def _fetch_exright_announcements_json(self) -> Dict[str, Any]:
        """發送 GET 請求至 TPEx bulletin/prePost API 取得上櫃除權除息預告表 JSON。"""
        params = {
            "id": "",
            "response": "json",
        }
        response = self._request("GET", self.EX_RIGHT_PREPOST_URL, params=params)
        return response.json()

    def _parse_exright_announcements(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """解析 TPEx bulletin/prePost 除權除息預告表 JSON 並清洗為 list[dict] 格式。"""
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
            if not isinstance(row, list) or len(row) < 8:
                continue

            iso_date = to_iso_date(row[0])
            symbol = clean_text(row[1])
            name = clean_text(row[2])
            ex_type = normalize_ex_type(row[3])
            if not iso_date or not symbol:
                continue

            item = ExRightAnnouncementItem(
                symbol=symbol,
                name=name,
                date=iso_date,
                ex_type=ex_type,
                stock_dividend_ratio=to_float(row[4]),
                cash_increase_ratio=to_float(row[5]),
                subscription_price=to_float(row[6]),
                cash_dividend=to_float(row[7]),
            )
            results.append(item.to_dict())

        return results

    def _get_exright_announcements(self) -> List[Dict[str, Any]]:
        """抓取並解析上櫃除權除息預告表 (bulletin/prePost)。"""
        raw_json = self._fetch_exright_announcements_json()
        return self._parse_exright_announcements(data=raw_json)

    def _fetch_stock_dividend_json(
        self, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """發送 GET 請求至 TPEx bulletin/exDailyQ API 取得指定日期區間的上櫃除權除息計算結果表 JSON。"""
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "id": "",
            "response": "json",
        }
        response = self._request("GET", self.EX_RIGHT_DAILY_URL, params=params)
        return response.json()

    def _parse_stock_dividend(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """解析 TPEx bulletin/exDailyQ 除權除息計算結果表 JSON 並清洗為 list[dict] 格式。"""
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
            if not isinstance(row, list) or len(row) < 13:
                continue

            iso_date = to_iso_date(row[0])
            symbol = clean_text(row[1])
            name = clean_text(row[2])
            before_close = to_float(row[3])
            reference_price = to_float(row[4])
            right_and_dividend_value = to_float(row[7])
            ex_type = normalize_ex_type(row[8])
            limit_up = to_float(row[9])
            limit_down = to_float(row[10])
            opening_reference_price = to_float(row[11])
            ex_dividend_reference_price = to_float(row[12])

            if (
                not iso_date
                or not symbol
                or before_close is None
                or reference_price is None
                or right_and_dividend_value is None
                or limit_up is None
                or limit_down is None
                or opening_reference_price is None
                or ex_dividend_reference_price is None
            ):
                continue

            item = ExRightResultItem(
                symbol=symbol,
                name=name,
                date=iso_date,
                ex_type=ex_type,
                before_close=before_close,
                reference_price=reference_price,
                right_and_dividend_value=right_and_dividend_value,
                limit_up=limit_up,
                limit_down=limit_down,
                opening_reference_price=opening_reference_price,
                ex_dividend_reference_price=ex_dividend_reference_price,
            )
            results.append(item.to_dict())

        return results

    def _get_stock_dividend(
        self, start_date: str, end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """抓取並解析指定日期區間的上櫃除權除息計算結果表 (bulletin/exDailyQ)。"""
        target_end = end_date if end_date is not None else start_date
        iso_start = format_iso_date(start_date, "%Y-%m-%d")
        iso_end = format_iso_date(target_end, "%Y-%m-%d")
        if iso_start > iso_end:
            raise ValueError(
                f"start_date '{start_date}' cannot be later than end_date '{target_end}'."
            )

        q_start = format_iso_date(start_date, "%Y/%m/%d")
        q_end = format_iso_date(target_end, "%Y/%m/%d")

        raw_json = self._fetch_stock_dividend_json(
            start_date=q_start, end_date=q_end
        )
        return self._parse_stock_dividend(data=raw_json)
