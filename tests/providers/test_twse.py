from unittest.mock import MagicMock
import pytest

from src.providers import TwseClient


def test_twse_get_list_returns_cleaned_list_of_dicts():
    """驗證 TwseClient.get_list() 正確回傳符合 model 定義與 ISO 日期格式的 list[dict]。"""
    sample_html = """
    <html><body><table>
        <tr><td bgcolor=#D5FFD5>有價證券代號及名稱 </td><td>ISIN</td><td>上市日</td><td>市場別</td><td>產業別</td><td>CFICode</td><td>備註</td></tr>
        <tr><td colspan=7><B> 股票 <B></td></tr>
        <tr><td>1101\u3000台泥</td><td>TW0001101004</td><td>1962/02/09</td><td>上市</td><td>水泥工業</td><td>ESVUFR</td><td></td></tr>
        <tr><td colspan=7><B> ETF <B></td></tr>
        <tr><td>0050\u3000元大台灣50</td><td>TW0000050004</td><td>2003/06/30</td><td>上市</td><td></td><td>CEOGEU</td><td></td></tr>
    </table></body></html>
    """
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.content = sample_html.encode("cp950")
    mock_session.request.return_value = mock_response

    client = TwseClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_list(market="twse")

    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0] == {
        "symbol": "1101",
        "name": "台泥",
        "type": "stock",
        "isin_code": "TW0001101004",
        "listing_date": "1962-02-09",
        "market": "上市",
        "industry": "水泥工業",
        "cfi_code": "ESVUFR",
    }
    assert data[1]["symbol"] == "0050"
    assert data[1]["type"] == "etf"
    assert data[1]["industry"] is None


def test_twse_get_stock_price_returns_cleaned_list_of_dicts():
    """驗證 TwseClient.get_stock_price() 正確回傳轉型後的數值與 ISO 日期格式 list[dict]。"""
    sample_json = {
        "stat": "OK",
        "date": "20261028",
        "data": [
            [
                "115/10/01",
                "20,666,092",
                "51,702,445,610",
                "2,490.00",
                "2,510.00",
                "2,485.00",
                "2,510.00",
                "+30.00",
                "57,634",
                "",
            ]
        ],
    }
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = sample_json
    mock_session.request.return_value = mock_response

    client = TwseClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_stock_price(symbol="2330", date="2026-10-28")

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0] == {
        "symbol": "2330",
        "date": "2026-10-01",
        "volume": 20666092,
        "value": 51702445610,
        "open": 2490.0,
        "high": 2510.0,
        "low": 2485.0,
        "close": 2510.0,
        "price_change": 30.0,
        "transaction": 57634,
    }


def test_twse_client_error_handler_invalid_params_and_retries():
    """驗證 TwseClient 的參數檢查與 HTTP 失敗重試 (Error Handler) 行為。"""
    mock_session = MagicMock()
    mock_session.headers = {}
    mock_session.request.side_effect = RuntimeError("Connection timeout")

    client = TwseClient(session=mock_session, sleep_range=(0.0, 0.0), max_retries=3)

    # 1. 非法 market 參數應拋出 ValueError
    with pytest.raises(ValueError):
        client.get_list(market="invalid_market")  # type: ignore[arg-type]

    # 2. 非 ISO 格式 (YYYY-MM-DD) 的 date 或空 symbol 應拋出 ValueError
    with pytest.raises(ValueError):
        client.get_stock_price(symbol="2330", date="2026/10/28")
    with pytest.raises(ValueError):
        client.get_stock_price(symbol="2330", date="20261028")
    with pytest.raises(ValueError):
        client.get_stock_price(symbol="   ", date="2026-10-28")

    # 3. 連線錯誤應重試 max_retries (3) 次後拋出例外
    with pytest.raises(RuntimeError, match="Connection timeout"):
        client.get_stock_price(symbol="2330", date="2026-10-28")

    assert mock_session.request.call_count == 3

