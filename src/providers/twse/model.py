from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal, Optional, Union


MarketLiteral = Literal[
    "all",
    "twse",
    "tpex",
    "esb",
    "上市",
    "上櫃",
    "興櫃",
]

# 市場別對應 ISIN 網頁的 strMode 參數
# strMode=2: 上市 (TWSE)
# strMode=4: 上櫃 (TPEx / OTC)
# strMode=5: 興櫃 (ESB / Emerging)
MARKET_TO_STR_MODES: Dict[str, List[int]] = {
    "all": [2, 4, 5],
    "twse": [2],
    "listed": [2],
    "上市": [2],
    "2": [2],
    "tpex": [4],
    "otc": [4],
    "上櫃": [4],
    "4": [4],
    "esb": [5],
    "emerging": [5],
    "興櫃": [5],
    "5": [5],
}

# 網頁上的中文分類標題 -> 對應的英文 type 名稱 (涵蓋上市 strMode=2 與上櫃 strMode=4)
SECTION_TO_TYPE: Dict[str, str] = {
    "股票": "stock",
    "上市認購(售)權證": "warrant",
    "上櫃認購(售)權證": "warrant",
    "特別股": "preferred_stock",
    "創新板": "innovation_board",
    "ETF": "etf",
    "ETN": "etn",
    "臺灣存託憑證(TDR)": "tdr",
    "受益證券-不動產投資信託": "reit",
    "受益證券-資產基礎證券": "abs",
}


def resolve_str_modes(market: Union[str, int]) -> List[int]:
    """
    將傳入的 market 參數轉換為對應的 strMode 清單。
    支援 'all', 'twse'/'上市'/2, 'tpex'/'上櫃'/4, 'esb'/'興櫃'/5。
    """
    key = str(market).strip().lower()
    if key in MARKET_TO_STR_MODES:
        return MARKET_TO_STR_MODES[key]

    raise ValueError(
        f"Invalid market '{market}'. Expected one of: 'all', 'twse' (上市), 'tpex' (上櫃), 'esb' (興櫃)"
    )


@dataclass
class TwseSecurityItem:
    """本國上市/上櫃/興櫃證券國際證券辨識號碼一覽表 (ISIN) 資料模型。"""

    symbol: str                  # 證券代號 (例如 '1101')
    name: str                    # 證券名稱 (例如 '台泥')
    type: str                    # 證券類別 (例如 'stock', 'etf', 'etn')
    isin_code: str               # 國際證券辨識號碼 (ISIN Code)
    listing_date: Optional[str]  # 上市/上櫃/興櫃日 (ISO 格式: YYYY-MM-DD)
    market: str                  # 市場別 ('上市', '上櫃', '興櫃')
    industry: Optional[str]      # 產業別 (例如 '水泥工業'，若無則為 None)
    cfi_code: str                # CFICode (例如 'ESVUFR')

    def to_dict(self) -> Dict[str, Any]:
        """轉換為標準 dict 格式。"""
        return asdict(self)
