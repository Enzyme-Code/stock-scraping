import re
from typing import Any, Dict, List
from curl_cffi import requests

from ..handler.base import BaseProvider
from ..utils import clean_text, to_iso_date
from .model import DATE_FIELDS, FIELD_MAPPING, MopsCompanyInfo


class Base(BaseProvider):
    """MOPS (公開資訊觀測站) 專用基底類別，負責底層 HTTP 請求、重試機制與 JSON 資料清洗。"""

    COMPANY_INFO_URL: str = "https://mops.twse.com.tw/mops/api/t05st03"

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

            if raw_key in DATE_FIELDS:
                parsed_kwargs[model_attr] = to_iso_date(str(raw_val)) if raw_val is not None else None
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

class Base(BaseProvider):
    """MOPS (公開資訊觀測站) 專用基底類別，負責底層 HTTP 請求、重試機制與 JSON 資料清洗。"""

    COMPANY_INFO_URL: str = "https://mops.twse.com.tw/mops/api/t05st03"

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

            if raw_key in DATE_FIELDS:
                parsed_kwargs[model_attr] = to_iso_date(str(raw_val)) if raw_val is not None else None
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

