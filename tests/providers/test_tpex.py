from unittest.mock import MagicMock
import pytest

from src.providers import TpexClient


def test_tpex_get_stock_price_returns_cleaned_list_of_dicts():
    """驗證 TpexClient.get_stock_price() 正確回傳 list[dict]，且仟股/仟元已乘以 1000 統一為股/元。"""
    sample_json = {
        "tables": [
            {
                "title": "個股日成交資訊",
                "subtitle": "6118 建達 115年10月",
                "date": "20261001",
                "data": [
                    [
                        "115/10/01",
                        "858",
                        "14,278",
                        "16.20",
                        "17.30",
                        "16.20",
                        "16.30",
                        "0.25",
                        "733",
                    ],
                    [
                        "115/10/02",
                        "210",
                        "3,403",
                        "16.35",
                        "16.35",
                        "16.15",
                        "16.15",
                        "-0.15",
                        "179",
                    ],
                ],
            }
        ]
    }
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = sample_json
    mock_session.request.return_value = mock_response

    client = TpexClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_stock_price(symbol="6118", date="2026-10-28")

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0] == {
        "symbol": "6118",
        "date": "2026-10-01",
        "volume": 858000,
        "value": 14278000,
        "open": 16.2,
        "high": 17.3,
        "low": 16.2,
        "close": 16.3,
        "price_change": 0.25,
        "transaction": 733,
    }
    assert data[1]["date"] == "2026-10-02"
    assert data[1]["price_change"] == -0.15


def test_tpex_client_error_handler_invalid_params_and_retries():
    """驗證 TpexClient 的參數檢查與 HTTP 失敗重試 (Error Handler) 行為。"""
    mock_session = MagicMock()
    mock_session.headers = {}
    mock_session.request.side_effect = RuntimeError("TPEx network error")

    client = TpexClient(session=mock_session, sleep_range=(0.0, 0.0), max_retries=3)

    # 1. 非 ISO 格式 (YYYY-MM-DD) 的 date 或空 symbol 應拋出 ValueError
    with pytest.raises(ValueError):
        client.get_stock_price(symbol="6118", date="2026/10/01")
    with pytest.raises(ValueError):
        client.get_stock_price(symbol="6118", date="20261001")
    with pytest.raises(ValueError):
        client.get_stock_price(symbol="", date="2026-10-01")

    # 2. 連線失敗應重試 3 次並輪替 User-Agent 後拋出例外
    with pytest.raises(RuntimeError, match="TPEx network error"):
        client.get_stock_price(symbol="6118", date="2026-10-01")

    assert mock_session.request.call_count == 3
    assert "User-Agent" in mock_session.headers

