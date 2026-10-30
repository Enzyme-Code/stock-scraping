from typing import Any, Dict, List

from .base import Base
from .model import MarketLiteral


class Client(Base):
    """TWSE 證交所資料客戶端，提供對外公開的查詢端口。"""

    def get_list(
        self,
        market: MarketLiteral = "all",
    ) -> List[Dict[str, Any]]:
        """
        取得本國上市 (strMode=2)、上櫃 (strMode=4)、興櫃 (strMode=5) 有價證券清單。

        Args:
            market: 市場別篩選，預設為 'all' (同時抓取上市、上櫃、興櫃)。
                    可選值:
                    - 'all': 全部市場 (strMode=2, 4, 5)
                    - 'twse': 上市 (strMode=2)
                    - 'tpex': 上櫃 (strMode=4)
                    - 'esb': 興櫃 (strMode=5)

        Returns:
            清洗後的證券清單 list[dict]，每筆資料包含 'type' 欄位供下游 pipeline 篩選。
        """
        return self._get_list(market=market)

    def get_stock_price(self, symbol: str, date: str) -> List[Dict[str, Any]]:
        """
        取得指定上市股票於該日期所屬月份的各日成交資訊 (STOCK_DAY)。

        Args:
            symbol: 上市股票代號，例如 '2330'。
            date: 查詢日期字串，強制使用 ISO 格式 'YYYY-MM-DD' (例如 '2026-10-28')。

        Returns:
            清洗後的個股日成交資訊 list[dict]。
        """
        return self._get_stock_price(symbol=symbol, date=date)
