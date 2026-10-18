from typing import Any, Dict, List, Union

from .base import TwseBaseProvider
from .model import MarketLiteral, SecurityTypeLiteral


class TwseClient(TwseBaseProvider):
    """TWSE 證交所資料客戶端，提供對外公開的查詢端口。"""

    def get_list(
        self,
        type: SecurityTypeLiteral = "all",
        market: Union[MarketLiteral, int] = "all",
    ) -> List[Dict[str, Any]]:
        """
        取得本國上市 (strMode=2)、上櫃 (strMode=4)、興櫃 (strMode=5) 有價證券清單。

        Args:
            type: 證券類別篩選，預設為 'all'。
                  可選值: 'all', 'stock', 'etf', 'etn', 'warrant',
                         'preferred_stock', 'innovation_board', 'tdr', 'reit', 'abs'
                         (亦支援直接傳入中文名稱如 '股票', 'ETF' 等)
            market: 市場別篩選，預設為 'all' (同時抓取上市、上櫃、興櫃)。
                    可選值:
                    - 'all': 全部市場 (strMode=2, 4, 5)
                    - 'twse' / '上市' / 2: 上市 (strMode=2)
                    - 'tpex' / '上櫃' / 4: 上櫃 (strMode=4)
                    - 'esb'  / '興櫃' / 5: 興櫃 (strMode=5)

        Returns:
            清洗後的證券清單 list[dict]。
        """
        return self._get_list(type=type, market=market)