from typing import Any, Dict, List

from .base import Base


class Client(Base):
    """TPEx 櫃買中心資料客戶端，提供對外公開的查詢端口。"""

    def get_stock_price(self, symbol: str, date: str) -> List[Dict[str, Any]]:
        """
        取得指定上櫃股票於該日期所屬月份的各日成交資訊 (tradingStock)。

        Args:
            symbol: 上櫃股票代號，例如 '6118'。
            date: 查詢日期字串，強制使用 ISO 格式 'YYYY-MM-DD' (例如 '2026-10-28')。

        Returns:
            清洗後的個股日成交資訊 list[dict] (成交股數與金額已統一換算為「股」與「元」)。
        """
        return self._get_stock_price(symbol=symbol, date=date)

    def get_institutional_investors(self, date: str) -> List[Dict[str, Any]]:
        """
        取得指定日期的上櫃三大法人買賣超日報 (insti/dailyTrade)。

        Args:
            date: 查詢日期字串，強制使用 ISO 格式 'YYYY-MM-DD' (例如 '2026-11-06')。

        Returns:
            清洗後的三大法人買賣超明細 list[dict]。
        """
        return self._get_institutional_investors(date=date)
