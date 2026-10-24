from typing import Any, Dict, List

from .base import Base


class Client(Base):
    """MOPS 公開資訊觀測站資料客戶端，提供對外公開的查詢端口。"""

    def get_company_info(self, symbol: str) -> List[Dict[str, Any]]:
        """
        取得指定公司代號於公開資訊觀測站的基本資料 (僅包含前端顯示 isHidden=False 的欄位)。

        Args:
            symbol: 股票/公司代號字串，例如 "2330"。

        Returns:
            清洗後的公司基本資料 list[dict] (日期已轉換為 YYYY-MM-DD ISO 格式)。
        """
        return self._get_company_info(symbol=symbol)

