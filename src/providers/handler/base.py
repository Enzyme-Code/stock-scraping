from abc import ABC
from pathlib import Path
import random
import time
from typing import Any, Dict, List, Optional, Tuple
from curl_cffi import requests
import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yml"


class BaseProvider(ABC):
    """所有資料提供者 (Provider) 共用的抽象基底類別。"""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: Optional[float] = None,
        sleep_range: Optional[Tuple[float, float]] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        impersonate: Optional[str] = None,
        debug: Optional[bool] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        cfg = self._load_config(config_path or DEFAULT_CONFIG_PATH)

        self.timeout: float = timeout if timeout is not None else cfg["timeout"]
        raw_range = sleep_range if sleep_range is not None else cfg["sleep_range"]
        self.sleep_range: Tuple[float, float] = (float(raw_range[0]), float(raw_range[1]))
        self.max_retries: int = max_retries if max_retries is not None else cfg["max_retries"]
        self.backoff_factor: float = (
            backoff_factor if backoff_factor is not None else cfg["backoff_factor"]
        )
        self.impersonate: Optional[str] = (
            impersonate if impersonate is not None else cfg["impersonate"]
        )
        self.debug: bool = debug if debug is not None else cfg["debug"]
        self.user_agents: List[str] = cfg["user_agents"]

        self.session: requests.Session = session or self._create_default_session()

    @staticmethod
    def _load_config(config_path: Path) -> Dict[str, Any]:
        """從同目錄的 config.yml 讀取 provider 設定。"""
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("provider", {})

    def _create_default_session(self) -> requests.Session:
        """建立預設的 curl_cffi Session，並隨機設定初始 User-Agent。"""
        session = requests.Session(
            impersonate=self.impersonate,
            timeout=self.timeout,
        )
        session.headers.update({"User-Agent": self._get_random_user_agent()})
        return session

    def _get_random_user_agent(self) -> str:
        """從 user_agents 清單中隨機取得一個 User-Agent。"""
        return random.choice(self.user_agents)

    def _rotate_user_agent(self) -> str:
        """隨機替換目前 Session 的 User-Agent 並回傳新的值。"""
        new_ua = self._get_random_user_agent()
        self.session.headers["User-Agent"] = new_ua
        self._debug(f"Rotated User-Agent to: {new_ua}")
        return new_ua

    def _debug(self, message: str) -> None:
        """當 debug 開關啟用時輸出除錯訊息。"""
        if self.debug:
            print(f"[{self.__class__.__name__}][DEBUG] {message}")

    def _get_random_sleep_time(self) -> float:
        """從 sleep_range (例如 2~4 秒) 隨機取得一個等待秒數。"""
        return random.uniform(self.sleep_range[0], self.sleep_range[1])

    def _sleep(self, seconds: Optional[float] = None) -> float:
        """執行一般請求間的隨機延遲等待 (預設為 2~4 秒隨機)。"""
        delay = self._get_random_sleep_time() if seconds is None else seconds
        if delay > 0:
            self._debug(f"Sleeping for {delay:.2f}s...")
            time.sleep(delay)
        return delay

    def _retry_sleep(self, attempt: int) -> float:
        """
        執行重試 (retry) 時的指數退避等待 (Exponential Backoff)。
        以隨機基礎秒數 (2~4s) 乘上 2^(attempt-1)：
        - attempt=1: (2~4s) * 1 = 2~4s
        - attempt=2: (2~4s) * 2 = 4~8s
        - attempt=3: (2~4s) * 4 = 8~16s
        """
        base_delay = self._get_random_sleep_time()
        delay = base_delay * (self.backoff_factor ** (attempt - 1))
        if delay > 0:
            self._debug(
                f"Retry {attempt}/{self.max_retries}: sleeping for {delay:.2f}s..."
            )
            time.sleep(delay)
        return delay
