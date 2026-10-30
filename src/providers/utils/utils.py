from datetime import datetime
import re
from typing import Optional, Tuple, Union


def clean_text(text: Optional[str]) -> str:
    """清除字串前後的半形與全形空白 (\u3000)。"""
    if not text:
        return ""
    return text.replace("\u3000", " ").strip()


def split_symbol_name(raw_text: str) -> Tuple[str, str]:
    """
    將「代號　名稱」(例如 '1101　台泥' 或 '0050  元大台灣50') 拆分為 (symbol, name)。
    支援全形空白 (\u3000) 與一般空白分隔。
    """
    cleaned = raw_text.strip()
    parts = re.split(r"[\u3000\s]+", cleaned, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return cleaned, ""


def to_iso_date(date_str: Optional[str]) -> Optional[str]:
    """
    將常見日期字串轉換為 ISO 格式 (YYYY-MM-DD)。
    支援：
    - 西元斜線/橫線/無分隔：'1962/02/09', '1962-02-09', '19620209'
    - 民國年斜線/橫線：'113/02/09', '113-02-09'
    若無法解析或為空字串則回傳 None。
    """
    cleaned = clean_text(date_str)
    if not cleaned:
        return None

    # 1. 嘗試標準西元格式
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # 2. 嘗試民國年格式 (例如 113/02/09 或 98-05-01)
    roc_match = re.match(r"^(\d{1,3})[/\-.](\d{1,2})[/\-.](\d{1,2})$", cleaned)
    if roc_match:
        year = int(roc_match.group(1)) + 1911
        month = int(roc_match.group(2))
        day = int(roc_match.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def format_iso_date(date_str: str, output_format: str) -> str:
    """
    強制驗證傳入的 date_str 為嚴格 ISO 格式 (YYYY-MM-DD)，並轉換為指定的 strftime 格式
    (例如 TWSE 的 '%Y%m01' 或 TPEx 的 '%Y/%m/01')。
    若不符合 YYYY-MM-DD 格式則拋出 ValueError。
    """
    cleaned = clean_text(date_str)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
        raise ValueError(
            f"Invalid date '{date_str}'. Expected ISO format 'YYYY-MM-DD' (e.g. '2026-10-28')."
        )
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"Invalid date '{date_str}'. Expected ISO format 'YYYY-MM-DD' (e.g. '2026-10-28')."
        ) from exc

    return dt.strftime(output_format)


def to_int(val: Optional[Union[str, int, float]], multiplier: int = 1) -> Optional[int]:
    """
    將含有千分位逗號的數字字串轉為整數，並可乘上指定倍率（如仟股/仟元乘以 1000）。
    若為 '--'、空字串或無法解析則回傳 None。
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(round(val * multiplier))

    cleaned = clean_text(str(val)).replace(",", "")
    if not cleaned or cleaned in ("--", "-", "---"):
        return None

    try:
        return int(round(float(cleaned) * multiplier))
    except ValueError:
        return None


def to_float(val: Optional[Union[str, int, float]]) -> Optional[float]:
    """
    將含有千分位逗號、正負號或 'X' 標記的價格/漲跌字串轉為 float。
    例如 '2,490.00' -> 2490.0, '+30.00' -> 30.0, 'X0.00' -> 0.0。
    若為 '--'、空字串或無法解析則回傳 None。
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    cleaned = clean_text(str(val)).replace(",", "")
    if not cleaned or cleaned in ("--", "-", "---"):
        return None

    # 處理除權息不比價如 'X0.00' 或帶有特殊前綴的數值
    cleaned = cleaned.lstrip("Xx")
    try:
        return float(cleaned)
    except ValueError:
        match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
        if match:
            return float(match.group(0))
        return None
