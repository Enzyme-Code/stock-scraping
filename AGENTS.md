# Stock Scraping 專案開發規範 (AGENTS.md)

本文件定義 `stock-scraping` 專案的架構設計、目錄規範與程式碼慣例，所有新增或修改的 Provider、Pipeline、Storage 模組皆須遵循以下準則。

---

## 1. 專案目錄架構

```text
stock-scraping/
├── tests/                   # Pytest 自動化測試目錄
│   └── providers/           # 各 Provider 對應的單元與整合測試 (test_<provider>.py)
└── src/
    ├── pipelines/           # 資料處理與篩選流程 (決定要存取或過濾哪些欄位/類別)
    ├── storage/             # 資料輸出與持久化層 (資料庫、Excel、CSV 等匯出邏輯)
    ├── utils/               # 全專案通用工具
    └── providers/           # 外部資料源爬蟲層 (僅負責抓取與基礎格式清洗)
        ├── __init__.py      # 統一匯出各資料源 Client (例如 TwseClient, MopsClient)
        ├── handler/         # 所有 Provider 共用的底層抽象類別與設定
        │   ├── base.py      # 定義 BaseProvider (Session、Timeout、Sleep、Retry、UA 輪替、Debug)
        │   └── config.yml   # 集中管理 Provider 預設參數 (Single Source of Truth)
        ├── utils/           # 跨 Provider 共用的清洗工具
        │   ├── __init__.py
        │   └── utils.py     # clean_text(), split_symbol_name(), to_iso_date() 等
        ├── twse/            # 證交所 (TWSE / ISIN) Provider
        │   ├── __init__.py
        │   ├── base.py      # 定義 Base(BaseProvider)：處理 HTTP 請求、重試與 HTML/JSON 解析
        │   ├── client.py    # 定義 Client(Base)：保持精簡，僅暴露對外公開查詢方法
        │   └── model.py     # 定義資料模型 (@dataclass)、欄位映射與參數型別 (Literal)
        └── mops/            # 公開資訊觀測站 (MOPS) Provider
            ├── __init__.py
            ├── base.py
            ├── client.py
            └── model.py
```

---

## 2. Provider 層設計規範

### 2.1 職責分離 (Four-File Pattern)
每個新增的資料提供者（`src/providers/<provider_name>/`）應拆分為以下結構：

1. **`handler/base.py` & `handler/config.yml`（共用基底層）**
   - 使用 `curl_cffi.requests.Session` 取代標準 `requests`，預設帶入 `impersonate="chrome"`。
   - 所有預設參數（`timeout`、`sleep_range: [2.0, 4.0]`、`max_retries: 3`、`backoff_factor: 2.0`、`debug`、`user_agents`）統一由 `src/providers/handler/config.yml` 管理，不在程式碼內重複寫死常數。
   - 提供受保護的輔助方法供子類別呼叫：
     - `self._sleep()`：一般請求間隨機延遲 `2 ~ 4` 秒。
     - `self._retry_sleep(attempt)`：失敗重試時採指數退避（第 1 次 `1x`、第 2 次 `2x`、第 3 次 `4x`）。
     - `self._rotate_user_agent()`：隨機替換 Session 的 `User-Agent`。
     - `self._debug(message)`：由 `self.debug` 開關控制除錯訊息輸出。

2. **`<provider>/model.py`（資料模型與型別控制）**
   - 使用 `@dataclass` 定義輸出結構，並實作 `to_dict(self) -> Dict[str, Any]`（使用 `asdict(self)`）。
   - 所有輸出的 `dict` 欄位統一使用英文 `snake_case` 命名（例如證券代號統一命名為 `symbol`），並在每個欄位旁加上繁體中文註解說明該欄位代表的業務意義。
   - 若公開方法有固定選項參數，使用 `typing.Literal` 嚴格限制可傳入的英文小寫鍵值（例如 `MarketLiteral = Literal["all", "twse", "tpex", "esb"]`）。

3. **`<provider>/base.py`（內部請求與解析層）**
   - 類別固定命名為 `Base`，繼承自 `..handler.base.BaseProvider`（使用相對路徑匯入避免循環依賴）。
   - 所有內部方法以單底線 `_` 開頭（例如 `_request`、`_fetch_*`、`_parse_*`、`_get_*`）。
   - `_request()` 必須整合 `max_retries` 重試迴圈：請求成功後呼叫 `self._sleep()`；請求失敗時呼叫 `self._rotate_user_agent()` 與 `self._retry_sleep(attempt)`。

4. **`<provider>/client.py`（對外公開介面層）**
   - 類別固定命名為 `Client`，繼承自同目錄的 `.base.Base`。
   - **保持極簡**：不包含爬蟲解析細節或迴圈邏輯，方法主體僅負責呼叫 `Base` 層對應的 `return self._get_xxx(...)`，並附上清楚的 Docstring。
   - 完成後於 `src/providers/__init__.py` 以別名匯出：`from .<provider>.client import Client as <Provider>Client`。

---

## 3. 資料清洗與輸出格式規範

1. **統一輸出格式：` list[dict] `**
   - 所有 Provider 的公開查詢方法回傳型別一律為 `List[Dict[str, Any]]`，以便下游 `pipeline` 或 `pandas.DataFrame(data)` 可無縫接軌。
2. **日期格式標準化：ISO 8601 (`YYYY-MM-DD`)**
   - 不論原始資料為西元斜線（`1962/02/09`）、無分隔（`19620209`）或台灣民國年（`83/09/05`、`113/02/09`），一律透過 `src/providers/utils` 的 `to_iso_date()` 轉換為 `YYYY-MM-DD`（例如 `1994-09-05`）；若為空值則轉為 `None`。
3. **空白與空值清理**
   - 使用 `clean_text()` 清除前後半形與全形空白（`\u3000`），空字串統一轉為 `None`（必要識別欄位除外）。
   - 若其他 Provider 也會用到的通用清洗函式，應提取至 `src/providers/utils/utils.py`。
4. **篩選職責邊界**
   - Provider 只負責「依請求條件抓取並完整清洗回傳」，不在 Provider 端過度綁定細部業務過濾（例如 `twse.get_list` 僅保留 `market` 參數並標記好 `type` 欄位，細部類別篩選交由 `pipeline` 層決定）。

---

## 4. 測試與驗證規範 (Pytest)

1. **Provider 完成後必須通過 `pytest` 測試**
   - 每當新增或修改任何 Provider 時，必須在 `tests/providers/test_<provider>.py` 撰寫或更新對應的 `pytest` 測試案例，並實際執行 `pytest` 確保全數通過後才算完成開發。
   - **僅測試 `Client` 對外公開方法**：因為 `Client` 直接繼承 `Base`，測試時只需呼叫 `<Provider>Client` 的公開方法即可（`base.py` 內部私有方法、`handler` 與 `providers/utils` 皆不需額外獨立測試）。
2. **必測項目（僅針對 Client 回吐資料與 Error Handler）**
   - **Client 回吐資料驗證**：驗證呼叫 `<Provider>Client` 的公開方法能正確回傳 `list[dict]`，且欄位符合 `model.py` 定義、日期為 `YYYY-MM-DD` ISO 格式、空值或隱藏欄位（如 `isHidden=True`）已正確處理。
   - **Error Handler 驗證**：驗證對 `<Provider>Client` 傳入非法參數或發生連線/HTTP 錯誤時，重試機制與例外拋出行為符合預期。



