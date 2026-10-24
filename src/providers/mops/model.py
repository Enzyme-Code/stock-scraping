from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Set


# MOPS t05st03 API 欄位名稱 (isHidden=False) -> 模型欄位名稱對照表
FIELD_MAPPING: Dict[str, str] = {
    "stockId": "symbol",
    "companyName": "company_name",
    "companyAbbreviation": "company_abbreviation",
    "companyEnglishName": "company_english_name",
    "companyEnglishAbbreviation": "company_english_abbreviation",
    "marketName": "market_name",
    "industryCategory": "industry_category",
    "enterpriseUnifiedNumber": "enterprise_unified_number",
    "establishDate": "establish_date",
    "publishDate": "publish_date",
    "listingDate": "listing_date",
    "OTCDate": "otc_date",
    "ROTCDate": "rotc_date",
    "changeApprovedDate": "change_approved_date",
    "oldExpirationDate": "old_expiration_date",
    "chairman": "chairman",
    "president": "president",
    "spokesperson": "spokesperson",
    "spokespersonTitle": "spokesperson_title",
    "spokespersonTelephone": "spokesperson_telephone",
    "subSpokesperson": "sub_spokesperson",
    "address": "address",
    "englishAddress_Street": "english_address_street",
    "englishAddress_County": "english_address_county",
    "telephone": "telephone",
    "faxNumber": "fax_number",
    "email": "email",
    "internetAddress": "internet_address",
    "capitalAmount": "capital_amount",
    "commonStockPrice": "common_stock_price",
    "commonStockAmount": "common_stock_amount",
    "specialStockAmount": "special_stock_amount",
    "haveSpecialStock": "have_special_stock",
    "haveCompanyBonds": "have_company_bonds",
    "commonStockDistribute": "common_stock_distribute",
    "commonStockLevel": "common_stock_level",
    "stockTransferAgency": "stock_transfer_agency",
    "transferAgencyTelephone": "transfer_agency_telephone",
    "transferAddress": "transfer_address",
    "accountingOffice": "accounting_office",
    "accounting1": "accounting_1",
    "accounting2": "accounting_2",
    "accountingYear": "accounting_year",
    "oldAccountingYear": "old_accounting_year",
    "reportType": "report_type",
    "investorLiaison": "investor_liaison",
    "investorLiaisonTitle": "investor_liaison_title",
    "investorLiaisonTelephone": "investor_liaison_telephone",
    "investorLiaisonEmail": "investor_liaison_email",
    "corporateGovernanceLink": "corporate_governance_link",
    "mops_url_2": "mops_url_2",
    "mainBusiness": "main_business",
    "foreignCompanyRegisterPlace": "foreign_company_register_place",
    "beforeChangeName": "before_change_name",
    "beforeChangeAbbreviation": "before_change_abbreviation",
    "note": "note",
}

# 需要轉換為 ISO 格式 (YYYY-MM-DD) 的日期欄位 (API 原始 key)
DATE_FIELDS: Set[str] = {
    "establishDate",
    "publishDate",
    "listingDate",
    "OTCDate",
    "ROTCDate",
    "changeApprovedDate",
    "oldExpirationDate",
    "applyDate",
    "approvedDate",
}


@dataclass
class MopsCompanyInfo:
    """公開資訊觀測站 (MOPS) 公司基本資料 (t05st03) 資料模型 (僅包含 isHidden=False 的前端顯示欄位)。"""

    symbol: Optional[str] = None                          # 股票代號 (例如 '2330')
    company_name: Optional[str] = None                    # 公司名稱 (例如 '台灣積體電路製造股份有限公司')
    company_abbreviation: Optional[str] = None            # 公司簡稱 (例如 '台積電')
    company_english_name: Optional[str] = None            # 英文名稱
    company_english_abbreviation: Optional[str] = None    # 英文簡稱 (例如 'TSMC')
    market_name: Optional[str] = None                     # 產業類別/市場別 (例如 '上市公司')
    industry_category: Optional[str] = None               # 產業類別 (例如 '半導體業')
    enterprise_unified_number: Optional[str] = None       # 營利事業統一編號
    establish_date: Optional[str] = None                  # 成立日期 (ISO 格式: YYYY-MM-DD)
    publish_date: Optional[str] = None                    # 公開發行日期 (ISO 格式: YYYY-MM-DD)
    listing_date: Optional[str] = None                    # 上市日期 (ISO 格式: YYYY-MM-DD)
    otc_date: Optional[str] = None                        # 上櫃日期 (ISO 格式: YYYY-MM-DD)
    rotc_date: Optional[str] = None                       # 興櫃日期 (ISO 格式: YYYY-MM-DD)
    change_approved_date: Optional[str] = None            # 變更核准日期 (ISO 格式: YYYY-MM-DD)
    old_expiration_date: Optional[str] = None             # 變更前營業年度截止日
    chairman: Optional[str] = None                        # 董事長
    president: Optional[str] = None                       # 總經理 / 總裁
    spokesperson: Optional[str] = None                    # 發言人
    spokesperson_title: Optional[str] = None              # 發言人職稱
    spokesperson_telephone: Optional[str] = None          # 發言人電話
    sub_spokesperson: Optional[str] = None                # 代理發言人
    address: Optional[str] = None                         # 住址 (總公司地址)
    english_address_street: Optional[str] = None          # 英文住址 (街道門牌)
    english_address_county: Optional[str] = None          # 英文住址 (縣市國別與郵遞區號)
    telephone: Optional[str] = None                       # 總機電話
    fax_number: Optional[str] = None                      # 傳真機號碼
    email: Optional[str] = None                           # 電子郵件信箱
    internet_address: Optional[str] = None                # 公司網址
    capital_amount: Optional[str] = None                  # 實收資本額 (例如 '259,323,700,670元')
    common_stock_price: Optional[str] = None              # 普通股每股面額 (例如 '新台幣 10.0000元')
    common_stock_amount: Optional[str] = None             # 已發行普通股數或TDR原股發行股數
    special_stock_amount: Optional[str] = None            # 特別股股數 (例如 '0股')
    have_special_stock: Optional[bool] = None             # 是否發行特別股
    have_company_bonds: Optional[bool] = None             # 普通股盈餘分派或虧損撥補頻率/是否發行公司債
    common_stock_distribute: Optional[str] = None         # 普通股盈餘分派或虧損撥補頻率 (例如 '每季' / '每年')
    common_stock_level: Optional[str] = None              # 普通股年度(含第4季或後半年度)現金股息及紅利決議層級 (例如 '董事會' / '股東會')
    stock_transfer_agency: Optional[str] = None           # 股票過戶機構
    transfer_agency_telephone: Optional[str] = None       # 過戶機構電話
    transfer_address: Optional[str] = None                # 過戶機構地址
    accounting_office: Optional[str] = None               # 簽證會計師事務所
    accounting_1: Optional[str] = None                    # 簽證會計師 1
    accounting_2: Optional[str] = None                    # 簽證會計師 2
    accounting_year: Optional[str] = None                 # 變更後會計年度
    old_accounting_year: Optional[str] = None             # 變更前會計年度
    report_type: Optional[str] = None                     # 財報編製類型 (例如 '合併' / '個別')
    investor_liaison: Optional[str] = None                # 投資人關係聯絡人
    investor_liaison_title: Optional[str] = None          # 投資人關係聯絡人職稱
    investor_liaison_telephone: Optional[str] = None      # 投資人關係聯絡電話
    investor_liaison_email: Optional[str] = None          # 投資人關係聯絡電子郵件
    corporate_governance_link: Optional[str] = None       # 公司治理專區網址
    mops_url_2: Optional[str] = None                      # 利害關係人專區網址 / ESG 網址
    main_business: Optional[str] = None                   # 主要經營業務
    foreign_company_register_place: Optional[str] = None  # 外國企業註冊地國
    before_change_name: Optional[str] = None              # 變更前名稱
    before_change_abbreviation: Optional[str] = None      # 變更前簡稱
    note: Optional[str] = None                            # 備註

    def to_dict(self) -> Dict[str, Any]:
        """轉換為標準 dict 格式。"""
        return asdict(self)
