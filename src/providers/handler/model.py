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


@dataclass
class InstitutionalInvestorItem(BaseModel):
    """跨市場共用（上市 TWSE / 上櫃 TPEx）的三大法人買賣超日報明細資料模型（僅保留買進與賣出，買賣超與合計由 pipeline 計算）。"""

    symbol: str               # 證券代號 (例如 '2330', '00411A')
    name: str                 # 證券名稱 (例如 '台積電')
    date: str                 # 交易日期 (ISO 格式: YYYY-MM-DD)
    foreign_buy: int          # 外陸資買進股數 (不含外資自營商)
    foreign_sell: int         # 外陸資賣出股數 (不含外資自營商)
    foreign_dealer_buy: int   # 外資自營商買進股數
    foreign_dealer_sell: int  # 外資自營商賣出股數
    trust_buy: int            # 投信買進股數
    trust_sell: int           # 投信賣出股數
    dealer_self_buy: int      # 自營商買進股數 (自行買賣)
    dealer_self_sell: int     # 自營商賣出股數 (自行買賣)
    dealer_hedge_buy: int     # 自營商買進股數 (避險)
    dealer_hedge_sell: int    # 自營商賣出股數 (避險)
