from dataclasses import dataclass
from typing import Literal, Set

from ..handler.model import BaseModel

# MOPS 財務比較e點通 (mopsfin.twse.com.tw/compare/data) 支援的財務趨勢指標代號
CompareItemLiteral = Literal[
    # 綜合損益與資產負債規模 (單位: 仟元 / 元)
    "Revenue",                                # 營業收入 (單位: 仟元)
    "GrossProfit",                            # 營業毛利 (單位: 仟元)
    "OperatingIncome",                        # 營業利益 (單位: 仟元)
    "NetProfit",                              # 稅後純益 (單位: 仟元)
    "EPS",                                    # 每股盈餘 (單位: 元)
    "CommonStock",                            # 股本 (單位: 仟元)
    "Equity",                                 # 歸屬於母公司業主之權益 (單位: 仟元)
    "NAV",                                    # 每股淨值 (單位: 元)
    # 現金流量趨勢 (單位: 仟元)
    "OperatingCashflow",                      # 營業活動現金流量 (單位: 仟元)
    "InvestingCashflow",                      # 投資活動現金流量 (單位: 仟元)
    "FinancingCashflow",                      # 籌資活動現金流量 (單位: 仟元)
    # 財務結構与償債能力 (單位: % / 倍)
    "DebtRatio",                              # 負債佔資產比率 (單位: %)
    "LongTermLiabilitiesRatio",               # 長期資金佔不動產、廠房及設備比率 (單位: %)
    "CurrentRatio",                           # 流動比率 (單位: %)
    "QuickRatio",                             # 速動比率 (單位: %)
    "InterestCoverage",                       # 利息保障倍數 (單位: 倍)
    # 經營能力 (單位: 次 / 日)
    "AccountsReceivableTurnover",             # 應收款項週轉率 (單位: 次)
    "AccountsReceivableTurnoverDay",          # 平均收現日數 (單位: 日)
    "InventoryTurnover",                      # 存貨週轉率 (單位: 次)
    "InventoryTurnoverDay",                   # 平均銷貨日數 (單位: 日)
    "TotalAssetTurnover",                     # 總資產週轉率 (單位: 次)
    # 獲利能力 (單位: %)
    "GrossMargin",                            # 毛利率 (單位: %)
    "OperatingMargin",                        # 營業利益率 (單位: %)
    "NetIncomeMargin",                        # 稅後純益率 (單位: %)
    "ROA",                                    # 資產報酬率 (單位: %)
    "ROE",                                    # 權益報酬率 (單位: %)
    # 成長能力 (單位: %)
    "RevenueYOY",                             # 營業收入年增率 (單位: %)
    "GrossProfitYOY",                         # 營業毛利年增率 (單位: %)
    "OperatingIncomeYOY",                     # 營業利益年增率 (單位: %)
    "NetProfitYOY",                           # 稅後純益年增率 (單位: %)
    "EPSYOY",                                 # 每股盈餘年增率 (單位: %)
    # 現金流量比率 (單位: %)
    "OperatingCashflowToCurrentLiability",    # 營業現金對流動負債比 (單位: %)
    "OperatingCashflowToLiability",           # 營業現金對負債比 (單位: %)
    "OperatingCashflowToNetProfit",           # 營業現金對稅後純益比 (單位: %)
]

VALID_COMPARE_ITEMS: Set[str] = {
    "Revenue",
    "GrossProfit",
    "OperatingIncome",
    "NetProfit",
    "EPS",
    "CommonStock",
    "Equity",
    "NAV",
    "OperatingCashflow",
    "InvestingCashflow",
    "FinancingCashflow",
    "DebtRatio",
    "LongTermLiabilitiesRatio",
    "CurrentRatio",
    "QuickRatio",
    "InterestCoverage",
    "AccountsReceivableTurnover",
    "AccountsReceivableTurnoverDay",
    "InventoryTurnover",
    "InventoryTurnoverDay",
    "TotalAssetTurnover",
    "GrossMargin",
    "OperatingMargin",
    "NetIncomeMargin",
    "ROA",
    "ROE",
    "RevenueYOY",
    "GrossProfitYOY",
    "OperatingIncomeYOY",
    "NetProfitYOY",
    "EPSYOY",
    "OperatingCashflowToCurrentLiability",
    "OperatingCashflowToLiability",
    "OperatingCashflowToNetProfit",
}


@dataclass
class MopsFinItem(BaseModel):
    """財務比較e點通 (mopsfin.twse.com.tw) 單一季度財務指標資料模型。"""

    symbol: str   # 證券代號 (例如 '2330')
    date: str     # 財報季度起始日 (ISO 格式: YYYY-MM-DD，例如 '2026Q3' -> '2026-07-01')
    value: float  # 該季單季財務指標數值 (保留 API 原始數值；如 EPS 為元、營收為仟元、比率為 %)
