from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


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


@dataclass
class MarginTradingItem(BaseModel):
    """跨市場共用（上市 TWSE / 上櫃 TPEx）的融資融券與借券賣出盤後明細資料模型（單位統一為：股）。"""

    symbol: str                # 證券代號 (例如 '2330', '3673')
    name: str                  # 證券名稱 (例如 '台積電', 'TPK-KY')
    date: str                  # 交易日期 (ISO 格式: YYYY-MM-DD)
    margin_buy: int            # 融資買進股數 (原始單位「張」已乘以 1,000)
    margin_sell: int           # 融資賣出股數 (原始單位「張」已乘以 1,000)
    margin_cash_repay: int     # 融資現金償還股數 (原始單位「張」已乘以 1,000)
    margin_prev_balance: int   # 融資前日餘額股數 (原始單位「張」已乘以 1,000)
    margin_balance: int        # 融資今日餘額股數 (原始單位「張」已乘以 1,000)
    margin_limit: int          # 融資次一營業日限額股數 (原始單位「張」已乘以 1,000)
    short_buy: int             # 融券買進股數 (原始單位「張」已乘以 1,000)
    short_sell: int            # 融券賣出股數 (原始單位「張」已乘以 1,000)
    short_stock_repay: int     # 融券現券償還股數 (原始單位「張」已乘以 1,000)
    short_prev_balance: int    # 融券前日餘額股數 (原始單位「張」已乘以 1,000)
    short_balance: int         # 融券今日餘額股數 (原始單位「張」已乘以 1,000)
    short_limit: int           # 融券次一營業日限額股數 (原始單位「張」已乘以 1,000)
    offset: int                # 資券互抵股數 (原始單位「張」已乘以 1,000)
    sbl_prev_balance: int      # 借券賣出前日餘額股數 (單位: 股)
    sbl_sell: int              # 借券賣出當日賣出股數 (單位: 股)
    sbl_repay: int             # 借券賣出當日還券股數 (單位: 股)
    sbl_adjust: int            # 借券賣出當日調整股數 (單位: 股)
    sbl_balance: int           # 借券賣出當日餘額股數 (單位: 股)
    sbl_limit: int             # 借券賣出次一營業日可借券賣出限額股數 (單位: 股)


@dataclass
class ExRightAnnouncementItem(BaseModel):
    """跨市場共用（上市 TWSE TWT48U / 上櫃 TPEx prePost）的除權除息預告表資料模型。"""

    symbol: str                            # 證券代號 (例如 '0051', '006201')
    name: str                              # 證券名稱 (例如 '元大中型100', '元大富櫃50')
    date: str                              # 除權除息日期 (ISO 格式: YYYY-MM-DD)
    ex_type: str                           # 除權息類別 (統一正規化為 '息' / '權' / '權息')
    stock_dividend_ratio: Optional[float]  # 無償配股率
    cash_increase_ratio: Optional[float]   # 現金增資配股率
    subscription_price: Optional[float]    # 現金增資認購價 (單位: 元)
    cash_dividend: Optional[float]         # 現金股利 (單位: 元/股；若為「待公告...」則為 None)


@dataclass
class ExRightResultItem(BaseModel):
    """跨市場共用（上市 TWSE TWT49U / 上櫃 TPEx exDailyQ）的除權除息計算結果表資料模型。"""

    symbol: str                         # 證券代號 (例如 '1101', '2230')
    name: str                           # 證券名稱 (例如 '台泥', '泰茂')
    date: str                           # 除權除息日期 (ISO 格式: YYYY-MM-DD)
    ex_type: str                        # 除權息類別 (統一正規化為 '息' / '權' / '權息')
    before_close: float                 # 除權息前收盤價 (單位: 元)
    reference_price: float              # 除權息參考價 (單位: 元)
    right_and_dividend_value: float     # 權值+息值 (單位: 元)
    limit_up: float                     # 漲停價格 (單位: 元)
    limit_down: float                   # 跌停價格 (單位: 元)
    opening_reference_price: float      # 開盤競價基準 / 開始交易基準價 (單位: 元)
    ex_dividend_reference_price: float  # 減除股利參考價 (單位: 元)
