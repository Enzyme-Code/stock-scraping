from typing import Any, Dict, List, Optional

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

    def get_margin_trading(self, date: str) -> List[Dict[str, Any]]:
        """
        取得指定日期的上櫃融資融券餘額 (margin/balance) 與融券借券賣出餘額 (margin/sbl) 合併明細。

        Args:
            date: 查詢日期字串，強制使用 ISO 格式 'YYYY-MM-DD' (例如 '2026-11-13')。

        Returns:
            清洗並以代號 Outer Join 合併後的融資融券與借券賣出明細 list[dict] (單位統一為「股」)。
        """
        return self._get_margin_trading(date=date)

    def get_exright_announcements(self) -> List[Dict[str, Any]]:
        """
        取得上櫃除權除息預告表 (bulletin/prePost)。

        Returns:
            清洗後的上櫃除權除息預告明細 list[dict]。
        """
        return self._get_exright_announcements()

    def get_stock_dividend(
        self, start_date: str, end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        取得指定日期（或日期區間）的上櫃除權除息計算結果表 (bulletin/exDailyQ)。

        Args:
            start_date: 起始日期字串，強制使用 ISO 格式 'YYYY-MM-DD' (例如 '2026-07-01')。
            end_date: 結束日期字串，強制使用 ISO 格式 'YYYY-MM-DD'；若未傳入則預設與 start_date 相同。

        Returns:
            清洗後的上櫃除權除息計算結果明細 list[dict]。
        """
        return self._get_stock_dividend(start_date=start_date, end_date=end_date)
