from unittest.mock import MagicMock
import pytest

from src.providers import MopsFinClient


def test_mops_fin_get_eps_and_dataset_supports_multiple_symbols_and_iso_dates():
    """
    驗證 MopsFinClient.get_eps() 與 get_dataset()：
    1. 支援傳入 list[str] 一次查詢多檔股票（以及傳入單一 str 自動轉為 list[str]）
    2. 依據 checkedNameList / showNameList 與 graphData 對應各檔股票代號
    3. 透過 to_iso_date() 將 'YYYYQ1~Q4' 轉為季初 ISO 日期 ('YYYY-01-01', 'YYYY-04-01', 'YYYY-07-01', 'YYYY-10-01')
    """
    sample_json = {
        "xaxisList": [
            "2026Q2",
            "2026Q3",
        ],
        "ylabel": "元",
        "yaxisLabel": "",
        "qnumber": "1",
        "graphData": [
            {
                "data": [
                    [0, 27.25, "C"],
                    [1, 29.43, "C"],
                ],
                "label": "台積電",
            },
            {
                "data": [
                    [0, 4.12, "C"],
                    [1, 5.51, "C"],
                ],
                "label": "鴻海",
            },
        ],
        "showNameList": [
            "2330 台積電 (上市半導體業)",
            "2317 鴻海 (上市其他電子業)",
        ],
        "checkedNameList": [
            "2330 台積電 (上市半導體業)",
            "2317 鴻海 (上市其他電子業)",
        ],
    }

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = sample_json
    mock_session.request.return_value = mock_response

    client = MopsFinClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_eps(symbols=["2330", "2317"])

    mock_session.request.assert_called_once_with(
        method="POST",
        url="https://mopsfin.twse.com.tw/compare/data",
        timeout=client.timeout,
        data=[
            ("compareItem", "EPS"),
            ("quarter", "true"),
            ("ylabel", ""),
            ("ys", "0"),
            ("revenue", "true"),
            ("bcodeAvg", "false"),
            ("companyAvg", "false"),
            ("qnumber", ""),
            ("companyId", "2330"),
            ("companyId", "2317"),
        ],
    )

    assert isinstance(data, list)
    assert len(data) == 4
    assert data == [
        {"symbol": "2330", "date": "2026-04-01", "value": 27.25},
        {"symbol": "2330", "date": "2026-07-01", "value": 29.43},
        {"symbol": "2317", "date": "2026-04-01", "value": 4.12},
        {"symbol": "2317", "date": "2026-07-01", "value": 5.51},
    ]

    # 測試傳入單一字串仍可自動正規化為 list 查詢
    client.get_dataset(symbols="2330", compare_item="ROE")
    sent_data = mock_session.request.call_args.kwargs["data"]
    assert ("compareItem", "ROE") in sent_data
    assert ("companyId", "2330") in sent_data


def test_mops_fin_client_error_handler_invalid_params_and_retries():
    """驗證 MopsFinClient 的參數檢查與 HTTP 失敗重試 (Error Handler) 行為。"""
    mock_session = MagicMock()
    mock_session.headers = {}
    mock_session.request.side_effect = RuntimeError("MopsFin connection failed")

    client = MopsFinClient(session=mock_session, sleep_range=(0.0, 0.0), max_retries=3)

    # 1. 空 symbols 或非法 compare_item 應拋出 ValueError
    with pytest.raises(ValueError):
        client.get_eps(symbols=[])
    with pytest.raises(ValueError):
        client.get_eps(symbols=["   "])
    with pytest.raises(ValueError):
        client.get_dataset(symbols=["2330"], compare_item="InvalidMetric")  # type: ignore[arg-type]

    # 2. 連線失敗應重試 3 次並輪替 User-Agent 後拋出例外
    with pytest.raises(RuntimeError, match="MopsFin connection failed"):
        client.get_eps(symbols=["2330"])

    assert mock_session.request.call_count == 3
    assert "User-Agent" in mock_session.headers
