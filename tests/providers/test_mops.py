from unittest.mock import MagicMock
import pytest

from src.providers import MopsClient


def test_mops_get_company_info_filters_hidden_and_formats_dates_and_numbers():
    """驗證 MopsClient.get_company_info() 只保留 isHidden=False 欄位、轉為 ISO 日期，並將金額與股數欄位去除單位轉為數值。"""
    sample_json = {
        "code": 200,
        "message": "查詢成功",
        "result": {
            "stockId": {"isHidden": False, "value": "3673"},
            "companyName": {"isHidden": False, "value": "TPK Holding Co., Ltd."},
            "companyAbbreviation": {"isHidden": False, "value": "TPK-KY"},
            "establishDate": {"isHidden": False, "value": "2005/11/21"},
            "listingDate": {"isHidden": False, "value": "99/10/29"},
            "capitalAmount": {"isHidden": False, "value": "4,066,637,590元"},
            "commonStockPrice": {"isHidden": False, "value": "新台幣                 10.0000元"},
            "commonStockAmount": {"isHidden": False, "value": "406,663,759股（含私募0股）"},
            "specialStockAmount": {"isHidden": False, "value": "0股"},
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
    data = client.get_company_info(symbol="3673")

    assert isinstance(data, list)
    assert len(data) == 1
    info = data[0]
    assert info["symbol"] == "3673"
    assert info["company_name"] == "TPK Holding Co., Ltd."
    assert info["company_abbreviation"] == "TPK-KY"
    assert info["establish_date"] == "2005-11-21"
    assert info["listing_date"] == "2010-10-29"
    assert info["capital_amount"] == 4066637590
    assert info["common_stock_price"] == 10.0
    assert info["common_stock_amount"] == 406663759
    assert info["private_stock_amount"] == 0
    assert info["special_stock_amount"] == 0
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
