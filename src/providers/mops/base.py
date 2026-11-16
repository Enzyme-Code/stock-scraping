import re
from typing import Any, Dict, List, Optional, Tuple

from ..handler.base import BaseProvider
from ..utils import clean_text, to_float, to_int, to_iso_date
from .model import (
    DATE_FIELDS,
    FIELD_MAPPING,
    FLOAT_FIELDS,
    INT_FIELDS,
    MopsCompanyInfo,
)


class Base(BaseProvider):
    """MOPS (公開資訊觀測站) 專用基底類別，負責底層 HTTP 請求與 JSON 資料清洗。"""

    COMPANY_INFO_URL: str = "https://mops.twse.com.tw/mops/api/t05st03"

    @staticmethod
    def _extract_first_int(raw_val: Any) -> Optional[int]:
        """從帶有單位與千分位的字串（如 '4,066,637,590元'、'0股'）中提取第一個整數。"""
        if raw_val is None:
            return None
        match = re.search(r"[-+]?\d[\d,]*", str(raw_val))
        if not match:
            return None
        return to_int(match.group(0))

    @classmethod
    def _parse_common_stock_amount(
        cls, raw_val: Any
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        將普通股股數字串（如 '406,663,759股（含私募0股）'）拆解為：
        (已發行普通股數 common_stock_amount, 私募股數 private_stock_amount)。
        """
        common_amount = cls._extract_first_int(raw_val)
        if common_amount is None:
            return None, None

        priv_match = re.search(r"私募\s*([\d,]+)\s*股", str(raw_val))
        private_amount = to_int(priv_match.group(1)) if priv_match else 0
        return common_amount, private_amount

    def _fetch_company_info_json(self, symbol: str) -> Dict[str, Any]:
        """發送 POST 請求至 MOPS t05st03 API 取得指定公司基本資料 JSON。"""
        payload = {"companyId": str(symbol).strip()}
        response = self._request("POST", self.COMPANY_INFO_URL, json=payload)
        return response.json()

    def _parse_company_info(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析 MOPS t05st03 回應資料：
        - 僅擷取 "isHidden": false (前端有呈現) 的欄位
        - 日期欄位統一轉為 ISO 格式 (YYYY-MM-DD)
        - 金額與股數欄位去除單位與標點符號並轉為 int / float
        - 輸出為 list[dict]
        """
        result = data.get("result")
        if not isinstance(result, dict) or not result:
            return []

        parsed_kwargs: Dict[str, Any] = {}

        for raw_key, model_attr in FIELD_MAPPING.items():
            field_obj = result.get(raw_key)
            if not isinstance(field_obj, dict):
                continue

            # 只抓取 isHidden 為 False 的前端顯示欄位
            if field_obj.get("isHidden") is not False:
                continue

            raw_val = field_obj.get("value")

            if raw_key == "commonStockAmount":
                common_amt, private_amt = self._parse_common_stock_amount(raw_val)
                parsed_kwargs["common_stock_amount"] = common_amt
                parsed_kwargs["private_stock_amount"] = private_amt
            elif raw_key in INT_FIELDS:
                parsed_kwargs[model_attr] = self._extract_first_int(raw_val)
            elif raw_key in FLOAT_FIELDS:
                parsed_kwargs[model_attr] = (
                    to_float(str(raw_val)) if raw_val is not None else None
                )
            elif raw_key in DATE_FIELDS:
                parsed_kwargs[model_attr] = (
                    to_iso_date(str(raw_val)) if raw_val is not None else None
                )
            elif isinstance(raw_val, bool):
                parsed_kwargs[model_attr] = raw_val
            elif isinstance(raw_val, str):
                cleaned = re.sub(r"\s+", " ", clean_text(raw_val))
                parsed_kwargs[model_attr] = cleaned if cleaned else None
            else:
                parsed_kwargs[model_attr] = raw_val

        item = MopsCompanyInfo(**parsed_kwargs)
        return [item.to_dict()]

    def _get_company_info(self, symbol: str) -> List[Dict[str, Any]]:
        """抓取並解析指定股票代號的公司基本資料。"""
        raw_json = self._fetch_company_info_json(symbol=symbol)
        return self._parse_company_info(data=raw_json)
