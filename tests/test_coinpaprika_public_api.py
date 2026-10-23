"""CoinPaprika public API (no key)."""

import pytest

from coinpaprika_public_api import (
    fetch_public_spot_market,
    fetch_ticker_for_asset,
    usage_stats,
    _ticker_from_paprika,
)


def test_ticker_from_paprika():
    row = _ticker_from_paprika(
        {
            "quotes": {
                "USD": {
                    "price": 100.0,
                    "percent_change_24h": 2.5,
                    "volume_24h": 1_000_000.0,
                    "market_cap": 2_000_000_000.0,
                }
            },
            "last_updated": "2026-10-22T00:00:00Z",
        },
        coin_id="btc-bitcoin",
    )
    assert row is not None
    assert row["price"] == 100.0
    assert row["quote_volume"] == 1_000_000.0
    assert row["source"] == "coinpaprika"


@pytest.mark.asyncio
async def test_fetch_ticker_for_asset(monkeypatch):
    async def fake_resolve(asset, *, session):
        return "btc-bitcoin"

    async def fake_get(session, path, *, consume_rps=True):
        if path == "/tickers/btc-bitcoin":
            return {
                "quotes": {
                    "USD": {
                        "price": 50000.0,
                        "percent_change_24h": 1.0,
                        "volume_24h": 5_000_000_000.0,
                    }
                }
            }
        return None

    monkeypatch.setattr("coinpaprika_public_api.resolve_coin_id", fake_resolve)
    monkeypatch.setattr("coinpaprika_public_api._get_json", fake_get)
    monkeypatch.setattr("coinpaprika_public_api._CACHE", {})
    row = await fetch_ticker_for_asset("BTC")
    assert row is not None
    assert row["price"] == 50000.0


@pytest.mark.asyncio
async def test_oracle_quick_coinpaprika_fallback(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def no_binance(pair):
        return None

    async def paprika(pair):
        return {
            "price": 43000.0,
            "change_24h": 0.8,
            "volume": 100.0,
            "quote_volume": 4_300_000.0,
            "source": "coinpaprika",
            "price_history_daily": [{"close": 43000.0, "volume": 1e9}],
            "price_history_source": "coinpaprika_ohlcv_latest",
        }

    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", no_binance)
    monkeypatch.setattr("coinpaprika_public_api.fetch_public_spot_market", paprika)

    async def passthrough_enrich(m, a, session=None):
        return m

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", passthrough_enrich)

    client = TestClient(app)
    res = client.get("/oracle/BTC/quick?lang=en&ux_mode=beginner")
    assert res.status_code == 200
    body = res.json()
    assert body.get("price") == 43000.0
    assert body.get("price_source") == "coinpaprika"
    assert body.get("price_history_daily")


def test_usage_stats():
    stats = usage_stats()
    assert stats["no_api_key"] is True


def test_public_coinpaprika_usage_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/public/market/coinpaprika/usage")
    assert res.status_code == 200
