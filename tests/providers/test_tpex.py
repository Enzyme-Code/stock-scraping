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


def test_tpex_get_institutional_investors_returns_cleaned_list_of_dicts():
    """驗證 TpexClient.get_institutional_investors() 正確回傳三大法人明細 list[dict] (排除小計/合計)。"""
    sample_json = {
        "tables": [
            {
                "title": "三大法人買賣明細資訊",
                "date": "115/11/06",
                "data": [
                    [
                        "00411A",
                        "主動統一前沿科技",
                        "1,931,000",   # [2] foreign_buy
                        "1,328,000",   # [3] foreign_sell
                        "603,000",     # [4] foreign_net
                        "0",           # [5] foreign_dealer_buy
                        "0",           # [6] foreign_dealer_sell
                        "0",           # [7] foreign_dealer_net
                        "1,931,000",   # [8] 外資合計買進 (略過)
                        "1,328,000",   # [9] 外資合計賣出 (略過)
                        "603,000",     # [10] 外資合計買賣超 (略過)
                        "0",           # [11] trust_buy
                        "0",           # [12] trust_sell
                        "0",           # [13] trust_net
                        "0",           # [14] dealer_self_buy
                        "0",           # [15] dealer_self_sell
                        "0",           # [16] dealer_self_net
                        "1,568,795",   # [17] dealer_hedge_buy
                        "4,207,408",   # [18] dealer_hedge_sell
                        "-2,638,613",  # [19] dealer_hedge_net
                        "1,568,795",   # [20] 自營商合計買進 (略過)
                        "4,207,408",   # [21] 自營商合計賣出 (略過)
                        "-2,638,613",  # [22] 自營商合計買賣超 (略過)
                        "-2,035,613",  # [23] 三大法人買賣超合計 (略過)
                    ]
                ],
            }
        ]
    }
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = sample_json
    mock_session.request.return_value = mock_response

    client = TpexClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_institutional_investors(date="2026-11-06")

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0] == {
        "symbol": "00411A",
        "name": "主動統一前沿科技",
        "date": "2026-11-06",
        "foreign_buy": 1931000,
        "foreign_sell": 1328000,
        "foreign_dealer_buy": 0,
        "foreign_dealer_sell": 0,
        "trust_buy": 0,
        "trust_sell": 0,
        "dealer_self_buy": 0,
        "dealer_self_sell": 0,
        "dealer_hedge_buy": 1568795,
        "dealer_hedge_sell": 4207408,
    }


def test_tpex_get_margin_trading_handles_column_order_and_mixed_units():
    """
    驗證 TpexClient.get_margin_trading()：
    1. margin/balance：全表單位為「張」(* 1000 轉股)，且注意 row[11] 為「券賣」、row[12] 為「券買」
    2. margin/sbl：同一列內單位混用 (row[2..7] 融券為「張」* 1000，row[8..13] 借券賣出為「股」* 1)
    3. 支援 Outer Join 合併、過濾 '合計' 彙總列與休市空資料處理
    """
    sample_balance = {
        "tables": [
            {
                "title": "上櫃股票融資融券餘額",
                "date": "115/11/13",
                "data": [
                    [
                        "6488 ",
                        "環球晶 ",
                        "3,200",   # [2] 前資餘額(張)
                        "150",     # [3] 資買(張)
                        "100",     # [4] 資賣(張)
                        "10",      # [5] 現償(張)
                        "3,240",   # [6] 資餘額(張)
                        "0",       # [7] 資屬證金
                        "2.95",    # [8] 資使用率(%)
                        "109,500", # [9] 資限額(張)
                        "200",     # [10] 前券餘額(張)
                        "45",      # [11] 券賣(張) -> short_sell = 45,000
                        "30",      # [12] 券買(張) -> short_buy = 30,000
                        "5",       # [13] 券償(張)
                        "210",     # [14] 券餘額(張)
                        "0",       # [15] 券屬證金
                        "0.19",    # [16] 券使用率(%)
                        "109,500", # [17] 券限額(張)
                        "8",       # [18] 資券互抵(張)
                    ]
                ],
            }
        ]
    }
    sample_sbl = {
        "tables": [
            {
                "title": "上櫃股票融券借券賣出餘額",
                "date": "115/11/13",
                "data": [
                    [
                        "6488",
                        "環球晶",
                        "200",        # [2] 融券前日餘額(張)
                        "45",         # [3] 融券賣出(張)
                        "30",         # [4] 融券買進(張)
                        "5",          # [5] 融券現券(張)
                        "210",        # [6] 融券今日餘額(張)
                        "109,500",    # [7] 融券限額(張)
                        "6,500,000",  # [8] 借券賣出前日餘額(股)
                        "120,000",    # [9] 借券賣出當日賣出(股)
                        "80,000",     # [10] 借券賣出當日還券(股)
                        "--",         # [11] 借券賣出當日調整(股) -> 0
                        "6,540,000",  # [12] 借券賣出當日餘額(股)
                        "43,800,000", # [13] 借券賣出次一營業日可限額(股)
                        "",           # [14] 備註
                    ],
                    [
                        "8069",
                        "元太",
                        "10",         # [2] 僅在 SBL 表出現時，融券單位為「張」(* 1000)
                        "2",          # [3] 融券賣出(張)
                        "1",          # [4] 融券買進(張)
                        "0",          # [5] 融券現券(張)
                        "11",         # [6] 融券今日餘額(張)
                        "50,000",     # [7] 融券限額(張)
                        "1,200,000",  # [8] 借券賣出前日餘額(股)
                        "30,000",     # [9]
                        "10,000",     # [10]
                        "0",          # [11]
                        "1,220,000",  # [12]
                        "20,000,000", # [13]
                        "",
                    ],
                ],
            }
        ]
    }

    mock_session = MagicMock()
    resp_balance = MagicMock()
    resp_balance.json.return_value = sample_balance
    resp_sbl = MagicMock()
    resp_sbl.json.return_value = sample_sbl
    mock_session.request.side_effect = [resp_balance, resp_sbl]

    client = TpexClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_margin_trading(date="2026-11-13")

    assert len(data) == 2
    assert data[0] == {
        "symbol": "6488",
        "name": "環球晶",
        "date": "2026-11-13",
        "margin_buy": 150000,
        "margin_sell": 100000,
        "margin_cash_repay": 10000,
        "margin_prev_balance": 3200000,
        "margin_balance": 3240000,
        "margin_limit": 109500000,
        "short_buy": 30000,
        "short_sell": 45000,
        "short_stock_repay": 5000,
        "short_prev_balance": 200000,
        "short_balance": 210000,
        "short_limit": 109500000,
        "offset": 8000,
        "sbl_prev_balance": 6500000,
        "sbl_sell": 120000,
        "sbl_repay": 80000,
        "sbl_adjust": 0,
        "sbl_balance": 6540000,
        "sbl_limit": 43800000,
    }
    # 8069 僅出現在 SBL 表：融券欄位已由「張」乘以 1000 轉為「股」，借券欄位保持「股」
    assert data[1]["symbol"] == "8069"
    assert data[1]["short_balance"] == 11000
    assert data[1]["sbl_balance"] == 1220000

    # 休市空資料應安全回傳空清單
    resp_empty = MagicMock()
    resp_empty.json.return_value = {"tables": [{"data": []}]}
    mock_session.request.side_effect = [resp_empty, resp_empty]
    assert client.get_margin_trading(date="2026-11-14") == []


def test_tpex_get_exright_announcements_and_stock_dividend():
    """
    驗證 TpexClient.get_exright_announcements() 與 get_stock_dividend()：
    1. 正確將民國斜線日期 ('115/11/20', '115/07/01') 轉為 ISO 格式 ('2026-11-20', '2026-07-01')
    2. 將櫃買中心 '除息' / '除權' / '除權息' 統一正規化為 '息' / '權' / '權息'
    3. 結果表正確提取索引 7 的 '權值+息值' 及價格欄位
    """
    sample_prepost = {
        "tables": [
            {
                "data": [
                    [
                        "115/11/20",
                        "006201",
                        "元大富櫃50",
                        "除息",
                        "0.00000000",
                        "0.00000000",
                        "0.00",
                        "0.90000000",
                        "0",
                        "0",
                        "0",
                        "0.00000000",
                        "",
                    ]
                ]
            }
        ],
        "stat": "ok",
    }
    sample_ex_daily = {
        "tables": [
            {
                "data": [
                    [
                        "115/07/01",
                        "2230",
                        "泰茂              ",
                        "25.55",
                        "24.94",
                        "0.000000",
                        "0.608951",
                        "0.608951",
                        "除息",
                        "27.40",
                        "22.45",
                        "24.95",
                        "24.94",
                        "0.60895126",
                        "0.00000000",
                        "0",
                        "0.00",
                        "0",
                        "0",
                        "0",
                        "0.00000000",
                    ]
                ]
            }
        ],
        "stat": "ok",
    }

    mock_session = MagicMock()
    resp_prepost = MagicMock()
    resp_prepost.json.return_value = sample_prepost
    resp_daily = MagicMock()
    resp_daily.json.return_value = sample_ex_daily
    mock_session.request.side_effect = [resp_prepost, resp_daily]

    client = TpexClient(session=mock_session, sleep_range=(0.0, 0.0))

    announcements = client.get_exright_announcements()
    assert len(announcements) == 1
    assert announcements[0] == {
        "symbol": "006201",
        "name": "元大富櫃50",
        "date": "2026-11-20",
        "ex_type": "息",
        "stock_dividend_ratio": 0.0,
        "cash_increase_ratio": 0.0,
        "subscription_price": 0.0,
        "cash_dividend": 0.9,
    }

    results = client.get_stock_dividend(
        start_date="2026-07-01", end_date="2026-07-15"
    )
    assert len(results) == 1
    assert results[0] == {
        "symbol": "2230",
        "name": "泰茂",
        "date": "2026-07-01",
        "ex_type": "息",
        "before_close": 25.55,
        "reference_price": 24.94,
        "right_and_dividend_value": 0.608951,
        "limit_up": 27.4,
        "limit_down": 22.45,
        "opening_reference_price": 24.95,
        "ex_dividend_reference_price": 24.94,
    }


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
    with pytest.raises(ValueError):
        client.get_institutional_investors(date="20261106")
    with pytest.raises(ValueError):
        client.get_margin_trading(date="2026/11/13")
    with pytest.raises(ValueError):
        client.get_stock_dividend(start_date="2026-07-10", end_date="2026-07-01")

    # 2. 連線失敗應重試 3 次並輪替 User-Agent 後拋出例外
    with pytest.raises(RuntimeError, match="TPEx network error"):
        client.get_stock_price(symbol="6118", date="2026-10-01")

    assert mock_session.request.call_count == 3
    assert "User-Agent" in mock_session.headers
