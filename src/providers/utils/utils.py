from datetime import datetime
import re
from typing import Optional, Tuple


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
    roc_match = re.match(r"^(\d{2,3})[/\-.](\d{1,2})[/\-.](\d{1,2})$", cleaned)
    if roc_match:
        year = int(roc_match.group(1)) + 1911
        month = int(roc_match.group(2))
        day = int(roc_match.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None

