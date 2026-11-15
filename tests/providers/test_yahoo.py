import json
from unittest.mock import MagicMock
import pytest

from src.providers import YahooClient


def test_yahoo_get_broker_trading_from_ssr_store_json():
    """
    驗證 YahooClient.get_broker_trading(symbol)：
    1. 正確從 root.App.main (含 :undefined 修補) 提取 QuoteChipStore.brokerTrades.data
    2. 完整解析買超前 15 大與賣超前 15 大分點 (共 30 筆)
    3. 提取實際資料日期 (2026-11-13)，並將買賣張數乘以 1,000 轉為股數
    """
    buyer_rank_list = [
        {
            "buyVolK": "3,653" if i == 1 else str(100 - i),
            "name": "凱基－台北 " if i == 1 else f"買超分點{i}",
            "sellVolK": "880" if i == 1 else "10",
            "rank": i,
            "volume": 2773 if i == 1 else (90 - i),
        }
        for i in range(1, 16)
    ]
    seller_rank_list = [
        {
            "buyVolK": "807" if i == 1 else "5",
            "name": "摩根士丹利" if i == 1 else f"賣超分點{i}",
            "sellVolK": "3,962" if i == 1 else str(200 - i),
            "rank": i,
            "volume": 3155 if i == 1 else (195 - i),
        }
        for i in range(1, 16)
    ]

    store_payload = {
        "context": {
            "dispatcher": {
                "stores": {
                    "QuoteChipStore": {
                        "brokerTrades": {
                            "data": {
                                "date": "2026-11-13T00:00:00+08:00",
                                "buyerRankList": buyer_rank_list,
                                "sellerRankList": seller_rank_list,
                                "totalDifferenceVolK": 848,
                                "totalOverbuyVolK": 11074,
                                "totalOversellVolK": 10226,
                            }
                        }
                    }
                }
            }
        }
    }
    raw_json_with_undefined = (
        json.dumps(store_payload, ensure_ascii=False)[:-1]
        + ',"extraConfig":undefined}'
    )
    sample_html = (
        "<html><body><script>\n"
        "(function (root) {\n"
        f"root.App.main = {raw_json_with_undefined};\n"
        "}(this));\n"
        "</script></body></html>"
    )

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = sample_html
    mock_session.request.return_value = mock_response

    client = YahooClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_broker_trading(symbol="2330")

    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://tw.stock.yahoo.com/quote/2330/broker-trading",
        timeout=client.timeout,
    )
    assert isinstance(data, list)
    assert len(data) == 30

    # 驗證買超第 1 名 (含全形連字號正規化與千分位張轉股)
    assert data[0] == {
        "symbol": "2330",
        "date": "2026-11-13",
        "side": "buy",
        "rank": 1,
        "broker_name": "凱基-台北",
        "buy_volume": 3653000,
        "sell_volume": 880000,
    }
    # 驗證賣超第 1 名 (索引 15)
    assert data[15] == {
        "symbol": "2330",
        "date": "2026-11-13",
        "side": "sell",
        "rank": 1,
        "broker_name": "摩根士丹利",
        "buy_volume": 807000,
        "sell_volume": 3962000,
    }


def test_yahoo_get_broker_trading_html_dom_fallback_and_suffix_stripping():
    """驗證當 root.App.main 不存在時，可退回解析 SSR HTML DOM 表格與 <time> 日期，並自動正規化 .TW / .TWO 後綴。"""
    sample_fallback_html = """
    <html><body>
      <div>
        <time datatime="2026/11/13"><span>資料時間：</span><span>2026/11/13</span></time>
      </div>
      <section>
        <div>
          <div>
            <div>
              <span>買超券商</span><span>買進</span><span>賣出</span><span>買超張數</span>
            </div>
            <div>
              <span>凱基台北</span><span>1,200</span><span>200</span><span>1,000</span>
            </div>
          </div>
          <div>
            <div>
              <span>賣超券商</span><span>買進</span><span>賣出</span><span>賣超張數</span>
            </div>
            <div>
              <span>美林證券</span><span>150</span><span>1,050</span><span>-900</span>
            </div>
          </div>
        </div>
      </section>
    </body></html>
    """
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = sample_fallback_html
    mock_session.request.return_value = mock_response

    client = YahooClient(session=mock_session, sleep_range=(0.0, 0.0))
    data = client.get_broker_trading(symbol="8069")

    mock_session.request.assert_called_once_with(
        method="GET",
        url="https://tw.stock.yahoo.com/quote/8069/broker-trading",
        timeout=client.timeout,
    )
    assert len(data) == 2
    assert data[0] == {
        "symbol": "8069",
        "date": "2026-11-13",
        "side": "buy",
        "rank": 1,
        "broker_name": "凱基台北",
        "buy_volume": 1200000,
        "sell_volume": 200000,
    }
    assert data[1] == {
        "symbol": "8069",
        "date": "2026-11-13",
        "side": "sell",
        "rank": 1,
        "broker_name": "美林證券",
        "buy_volume": 150000,
        "sell_volume": 1050000,
    }

    # 測試傳入帶 .TWO 後綴的 symbol，仍自動清理為純代號 '8069'
    data_with_suffix = client.get_broker_trading(symbol="8069.TWO")
    assert data_with_suffix[0]["symbol"] == "8069"


def test_yahoo_get_broker_trading_empty_data_returns_empty_list():
    """驗證當個股無分點進出資料時，安全回傳空清單 []。"""
    empty_store_html = (
        "<html><body><script>\n"
        'root.App.main = {"context":{"dispatcher":{"stores":{"QuoteChipStore":{"brokerTrades":{"data":{}}}}}}};\n'
        "</script></body></html>"
    )
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = empty_store_html
    mock_session.request.return_value = mock_response

    client = YahooClient(session=mock_session, sleep_range=(0.0, 0.0))
    assert client.get_broker_trading(symbol="2330") == []


def test_yahoo_client_error_handler_invalid_params_and_retries():
    """驗證 YahooClient 的參數檢查與 HTTP 失敗重試 (Error Handler) 行為。"""
    mock_session = MagicMock()
    mock_session.headers = {}
    mock_session.request.side_effect = RuntimeError("Yahoo connection error")

    client = YahooClient(session=mock_session, sleep_range=(0.0, 0.0), max_retries=3)

    # 1. 空 symbol 應拋出 ValueError
    with pytest.raises(ValueError):
        client.get_broker_trading(symbol="   ")
    with pytest.raises(ValueError):
        client.get_broker_trading(symbol=".TW")

    # 2. 連線失敗應重試 3 次並輪替 User-Agent 後拋出例外
    with pytest.raises(RuntimeError, match="Yahoo connection error"):
        client.get_broker_trading(symbol="2330")

    assert mock_session.request.call_count == 3
    assert "User-Agent" in mock_session.headers
