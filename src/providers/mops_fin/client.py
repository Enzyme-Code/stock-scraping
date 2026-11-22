from typing import Any, Dict, List

from .base import Base, SymbolsInput
from .model import CompareItemLiteral


class Client(Base):
    """MOPS 財務比較e點通 (mopsfin.twse.com.tw) 資料客戶端，提供對外公開的查詢端口。"""

    def get_dataset(
        self,
        symbols: SymbolsInput,
        compare_item: CompareItemLiteral,
    ) -> List[Dict[str, Any]]:
        """
        取得單檔或多檔股票於指定財務指標（compare_item）自 2013Q1 至今的歷季（單季）財務數據。

        Args:
            symbols: 股票代號清單 list[str]（如 ['2330', '2317']）或單一代號字串（如 '2330'）。
            compare_item: 財務指標名稱（如 'EPS', 'Revenue', 'GrossProfit', 'OperatingIncome',
                          'NetProfit', 'NAV', 'GrossMargin', 'OperatingMargin', 'NetIncomeMargin',
                          'ROE', 'ROA', 'DebtRatio' 等）。

        Returns:
            清洗後的歷季財務指標 list[dict]（季度已轉為季底 ISO 日期 YYYY-MM-DD）。
        """
        return self._get_dataset(symbols=symbols, compare_item=compare_item)

    def get_eps(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「每股盈餘 (EPS，單位：元)」。"""
        return self._get_dataset(symbols=symbols, compare_item="EPS")

    def get_revenue(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「營業收入 (Revenue，單位：仟元)」。"""
        return self._get_dataset(symbols=symbols, compare_item="Revenue")

    def get_gross_profit(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「營業毛利 (GrossProfit，單位：仟元)」。"""
        return self._get_dataset(symbols=symbols, compare_item="GrossProfit")

    def get_operating_income(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「營業利益 (OperatingIncome，單位：仟元)」。"""
        return self._get_dataset(symbols=symbols, compare_item="OperatingIncome")

    def get_net_profit(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「稅後純益 (NetProfit，單位：仟元)」。"""
        return self._get_dataset(symbols=symbols, compare_item="NetProfit")

    def get_nav(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「每股淨值 (NAV，單位：元)」。"""
        return self._get_dataset(symbols=symbols, compare_item="NAV")

    def get_gross_margin(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「毛利率 (GrossMargin，單位：%)」。"""
        return self._get_dataset(symbols=symbols, compare_item="GrossMargin")

    def get_operating_margin(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「營業利益率 (OperatingMargin，單位：%)」。"""
        return self._get_dataset(symbols=symbols, compare_item="OperatingMargin")

    def get_net_income_margin(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「稅後純益率 (NetIncomeMargin，單位：%)」。"""
        return self._get_dataset(symbols=symbols, compare_item="NetIncomeMargin")

    def get_roe(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「權益報酬率 (ROE，單位：%)」。"""
        return self._get_dataset(symbols=symbols, compare_item="ROE")

    def get_roa(self, symbols: SymbolsInput) -> List[Dict[str, Any]]:
        """取得單檔或多檔股票的歷季「資產報酬率 (ROA，單位：%)」。"""
        return self._get_dataset(symbols=symbols, compare_item="ROA")
