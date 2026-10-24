"""CoinMarketCap Basic API helpers."""

import pytest

from coinmarketcap_api import (
    _row_from_quote_payload,
    enrich_market_with_cmc_metadata,
    fetch_spot_ticker,
)


def test_row_from_quote_payload_parses_btc():
    payload = {
        "data": {
            "1": [
                {
                    "symbol": "BTC",
                    "cmc_rank": 1,
                    "quote": {
                        "USD": {
                            "price": 50000.0,
                            "percent_change_24h": 1.5,
                            "volume_24h": 2_000_000_000.0,
                            "market_cap": 900_000_000_000.0,
                        }
                    },
                }
            ]
        }
    }
    row = _row_from_quote_payload(payload, "BTC")
    assert row is not None
    assert row["price"] == 50000.0
    assert row["change_24h"] == 1.5
    assert row["market_cap_usd"] == 900_000_000_000.0
    assert row["source"] == "coinmarketcap"


@pytest.mark.asyncio
async def test_fetch_spot_ticker_without_key(monkeypatch):
    monkeypatch.setattr("coinmarketcap_api._api_key", lambda: "")
    assert await fetch_spot_ticker("BTC") is None


@pytest.mark.asyncio
async def test_enrich_market_with_cmc_metadata(monkeypatch):
    async def fake_ticker(asset, session=None):
        return {
            "market_cap_usd": 1e12,
            "cmc_rank": 1,
            "source": "coinmarketcap",
            "price": 1.0,
            "change_24h": 0.0,
            "quote_volume": 1.0,
            "volume": 1.0,
        }

    monkeypatch.setattr("coinmarketcap_api.is_configured", lambda: True)
    monkeypatch.setattr("coinmarketcap_api.fetch_spot_ticker", fake_ticker)

    base = {"price": 100.0, "change_24h": 1.0, "quote_volume": 1e9, "source": "binance_rest:x"}
    out = await enrich_market_with_cmc_metadata(base, "BTC")
    assert out["price"] == 100.0
    assert out["market_cap_usd"] == 1e12
    assert out["cmc_rank"] == 1


def test_oracle_quick_cmc_fallback(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def no_binance(pair):
        return None

    async def cmc_ticker(asset):
        return {
            "price": 1234.5,
            "change_24h": -2.0,
            "volume": 1000.0,
            "quote_volume": 5_000_000.0,
            "market_cap_usd": 50_000_000_000.0,
            "cmc_rank": 5,
            "source": "coinmarketcap",
        }

    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", no_binance)
    monkeypatch.setattr("coinmarketcap_api.fetch_spot_ticker", cmc_ticker)

    async def noop_enrich(market, asset, session=None):
        return market

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", noop_enrich)

    res = TestClient(app).get("/oracle/ETH/quick?lang=en")
    assert res.status_code == 200
    body = res.json()
    assert body["price"] == 1234.5
    assert body.get("price_source") == "coinmarketcap"
    assert body.get("market_cap_usd") == 50_000_000_000.0
