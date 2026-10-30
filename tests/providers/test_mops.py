from unittest.mock import MagicMock
import pytest

from src.providers import MopsClient


def test_mops_get_company_info_filters_hidden_and_formats_dates():
    """驗證 MopsClient.get_company_info() 只保留 isHidden=False 欄位並轉為 ISO 日期。"""
    sample_json = {
        "code": 200,
        "message": "查詢成功",
        "result": {
            "stockId": {"isHidden": False, "value": "2330"},
            "companyName": {"isHidden": False, "value": "台灣積體電路製造股份有限公司"},
            "companyAbbreviation": {"isHidden": False, "value": "台積電"},
            "establishDate": {"isHidden": False, "value": "76/02/21"},
            "listingDate": {"isHidden": False, "value": "83/09/05"},
            "commonStockPrice": {"isHidden": False, "value": "新台幣                 10.0000元"},
            "note": {"isHidden": False, "value": "\u3000"},
            # isHidden=True 的欄位不應被取出
            "mops_url_2": {"isHidden": True, "value": "https://should.be.hidden"},
        },
    }
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = sample_json
    mock_session.request.return_value = mock_response

    client = MopsClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_company_info(symbol="2330")

    assert isinstance(data, list)
    assert len(data) == 1
    info = data[0]
    assert info["symbol"] == "2330"
    assert info["company_name"] == "台灣積體電路製造股份有限公司"
    assert info["company_abbreviation"] == "台積電"
    assert info["establish_date"] == "1987-02-21"
    assert info["listing_date"] == "1994-09-05"
    assert info["common_stock_price"] == "新台幣 10.0000元"
    assert info["note"] is None
    assert info["mops_url_2"] is None


def test_mops_client_error_handler_retries():
    """驗證 MopsClient 發生 HTTP 錯誤時會執行重試機制並最終拋出例外。"""
    mock_session = MagicMock()
    mock_session.headers = {}
    mock_session.request.side_effect = RuntimeError("MOPS 500 error")

    client = MopsClient(session=mock_session, sleep_range=(0.0, 0.0), max_retries=3)

    with pytest.raises(RuntimeError, match="MOPS 500 error"):
        client.get_company_info(symbol="2330")

    assert mock_session.request.call_count == 3

