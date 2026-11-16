from dataclasses import dataclass
from typing import Literal

from ..handler.model import BaseModel
from ..utils import clean_text

SideLiteral = Literal["buy", "sell"]


def normalize_symbol(symbol: str) -> str:
    """
    清理並正規化股票代號：
    - 去除前後空白
    - 若帶有 '.TW' 或 '.TWO' 後綴則自動移除，統一回傳純代號（如 '2330'、'8069'）
    """
    cleaned = clean_text(symbol)
    if not cleaned:
        raise ValueError("symbol cannot be empty.")

    upper_symbol = cleaned.upper()
    if upper_symbol.endswith(".TWO"):
        cleaned = cleaned[:-4].strip()
    elif upper_symbol.endswith(".TW"):
        cleaned = cleaned[:-3].strip()

    if not cleaned:
        raise ValueError("symbol cannot be empty.")

    return cleaned


@dataclass
class YahooBrokerTradingItem(BaseModel):
    """Yahoo 奇摩股市個股當日主力分點買賣超排行（Top 15 買超 / 賣超）資料模型。"""

    symbol: str       # 證券代號 (例如 '2330', '8069')
    date: str         # 實際資料日期 (ISO 格式: YYYY-MM-DD)
    side: str         # 買賣超方向 ('buy': 買超排行, 'sell': 賣超排行)
    rank: int         # 該方向名次 (1 ~ 15)
    broker_name: str  # 券商分點名稱 (例如 '凱基台北', '摩根士丹利')
    buy_volume: int   # 買進股數 (單位: 股；原始單位「張」已乘以 1,000)
    sell_volume: int  # 賣出股數 (單位: 股；原始單位「張」已乘以 1,000)
