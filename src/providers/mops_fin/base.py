from typing import Any, Dict, List, Sequence, Tuple, Union

from ..handler.base import BaseProvider
from ..utils import clean_text, split_symbol_name, to_float, to_int, to_iso_date
from .model import (
    CompareItemLiteral,
    MopsFinItem,
    VALID_COMPARE_ITEMS,
)

SymbolsInput = Union[str, Sequence[str]]


class Base(BaseProvider):
    """MOPS 財務比較e點通 (mopsfin.twse.com.tw) 專用基底類別，負責底層 HTTP 請求與 JSON 資料解析。"""

    COMPARE_DATA_URL: str = "https://mopsfin.twse.com.tw/compare/data"

    @staticmethod
    def _normalize_symbols(symbols: SymbolsInput) -> List[str]:
        """
        將傳入的單一股票代號 (str) 或多檔股票代號清單 (list[str]) 正規化為去重且非空的 list[str]。
        若清單為空或皆為空白字串則拋出 ValueError。
        """
        raw_list: Sequence[str] = [symbols] if isinstance(symbols, str) else symbols
        if not isinstance(raw_list, Sequence):
            raise ValueError("symbols must be a str or list[str].")

        cleaned_list: List[str] = []
        for sym in raw_list:
            cleaned = clean_text(str(sym)) if sym is not None else ""
            if cleaned and cleaned not in cleaned_list:
                cleaned_list.append(cleaned)

        if not cleaned_list:
            raise ValueError("symbols cannot be empty.")

        return cleaned_list

    def _fetch_dataset_json(
        self,
        symbols: List[str],
        compare_item: str,
    ) -> Dict[str, Any]:
        """發送 POST 請求至 mopsfin compare/data API，支援一次帶入多筆 companyId。"""
        payload: List[Tuple[str, str]] = [
            ("compareItem", compare_item),
            ("quarter", "true"),
            ("ylabel", ""),
            ("ys", "0"),
            ("revenue", "true"),
            ("bcodeAvg", "false"),
            ("companyAvg", "false"),
            ("qnumber", ""),
        ]
        for sym in symbols:
            payload.append(("companyId", sym))

        response = self._request("POST", self.COMPARE_DATA_URL, data=payload)
        return response.json()

    def _parse_dataset(
        self, data: Dict[str, Any], fallback_symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """
        解析 mopsfin compare/data 回傳的多公司 xaxisList 與 graphData：
        - 依據 checkedNameList / showNameList (如 '2330 台積電 (上市半導體業)') 對照各條線的股票代號
        - 透過 point[0] 索引對照 xaxisList[x_idx] 取得季度字串（如 '2026Q3'）
        - 使用 to_iso_date() 統一轉換為季初 ISO 日期（如 '2026-07-01'）
        """
        xaxis_list = data.get("xaxisList")
        graph_data = data.get("graphData")
        if (
            not isinstance(xaxis_list, list)
            or not isinstance(graph_data, list)
            or not graph_data
        ):
            return []

        name_list = (
            data.get("checkedNameList")
            or data.get("showNameList")
            or data.get("displayCompanyId")
            or []
        )

        results: List[Dict[str, Any]] = []
        for series_idx, series in enumerate(graph_data):
            if not isinstance(series, dict):
                continue

            series_symbol = ""
            if (
                isinstance(name_list, list)
                and series_idx < len(name_list)
                and name_list[series_idx]
            ):
                series_symbol, _ = split_symbol_name(str(name_list[series_idx]))
            elif series_idx < len(fallback_symbols):
                series_symbol = fallback_symbols[series_idx]

            if not series_symbol:
                continue

            points = series.get("data")
            if not isinstance(points, list):
                continue

            for point in points:
                if not isinstance(point, list) or len(point) < 2:
                    continue

                x_idx = to_int(point[0])
                if x_idx is None or x_idx < 0 or x_idx >= len(xaxis_list):
                    continue

                iso_date = to_iso_date(str(xaxis_list[x_idx]))
                value = to_float(point[1])
                if iso_date is None or value is None:
                    continue

                item = MopsFinItem(
                    symbol=series_symbol,
                    date=iso_date,
                    value=value,
                )
                results.append(item.to_dict())

        return results

    def _get_dataset(
        self,
        symbols: SymbolsInput,
        compare_item: CompareItemLiteral,
    ) -> List[Dict[str, Any]]:
        """
        共用底層查詢方法：抓取並解析單檔或多檔股票於指定財務指標的歷季數據。

        Args:
            symbols: 股票代號清單 list[str]（如 ['2330', '2317']）或單一代號字串（如 '2330'）。
            compare_item: 財務指標代號，例如 'EPS', 'Revenue', 'NAV', 'ROE' 等。
        """
        cleaned_symbols = self._normalize_symbols(symbols)

        if compare_item not in VALID_COMPARE_ITEMS:
            raise ValueError(
                f"Invalid compare_item '{compare_item}'. Expected one of: {sorted(VALID_COMPARE_ITEMS)}"
            )

        raw_json = self._fetch_dataset_json(
            symbols=cleaned_symbols,
            compare_item=compare_item,
        )
        return self._parse_dataset(data=raw_json, fallback_symbols=cleaned_symbols)
