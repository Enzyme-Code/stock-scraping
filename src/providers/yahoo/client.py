from typing import Any, Dict, List

from .base import Base


class Client(Base):
    """Yahoo 奇摩股市資料客戶端，提供對外公開的查詢端口。"""

    def get_broker_trading(self, symbol: str) -> List[Dict[str, Any]]:
        """
        取得指定上市或上櫃股票的當日主力／券商分點買賣超排行（買超前 15 名與賣超前 15 名）。

        Args:
            symbol: 股票代號（如 '2330'、'8069'，若傳入 '2330.TW' 或 '8069.TWO' 亦會自動正規化為純代號）。

        Returns:
            清洗後的當日主力分點買賣超排行 list[dict]（買賣股數已統一由「張」乘以 1,000 轉為「股」）。
        """
        return self._get_broker_trading(symbol=symbol)
