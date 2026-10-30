from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class BaseModel:
    """所有 Provider 資料模型共用的基底類別。"""

    def to_dict(self) -> Dict[str, Any]:
        """轉換為標準 dict 格式。"""
        return asdict(self)


@dataclass
class StockPriceItem(BaseModel):
    """跨市場共用（上市 TWSE / 上櫃 TPEx）的個股日成交資訊資料模型。"""

    symbol: str          # 證券代號 (例如 '2330', '6118')
    date: str            # 交易日期 (ISO 格式: YYYY-MM-DD)
    volume: int          # 成交股數 (單位: 股；上櫃原始仟股已乘以 1000)
    value: int           # 成交金額 (單位: 新台幣元；上櫃原始仟元已乘以 1000)
    open: float          # 開盤價
    high: float          # 最高價
    low: float           # 最低價
    close: float         # 收盤價
    price_change: float  # 漲跌價差
    transaction: int     # 成交筆數

