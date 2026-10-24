"""Kraken public API (no key)."""

import pytest

from kraken_public_api import fetch_public_spot_market, pair_to_kraken_pair


def test_pair_to_kraken_pair():
    assert pair_to_kraken_pair("BTCUSDT") == "XBTUSD"
    assert pair_to_kraken_pair("ETHUSDT") == "ETHUSD"


@pytest.mark.asyncio
async def test_fetch_public_spot_market(monkeypatch):
    ticker_payload = {
        "error": [],
        "result": {
            "XXBTZUSD": {
                "a": ["50001", "1", "1"],
                "b": ["50000", "1", "1"],
                "c": ["50000.5", "0.1"],
                "v": ["10", "200"],
                "o": "49000",
            }
        },
    }

    async def fake_get(session, path, *, params=None):
        if path == "Ticker":
            return ticker_payload
        if path == "Depth":
            return {
                "error": [],
                "result": {
                    "XXBTZUSD": {
                        "bids": [["50000", "1", 1]],
                        "asks": [["50001", "1", 1]],
                    }
                },
            }
        return None

    monkeypatch.setattr("kraken_public_api._get_json", fake_get)

    snap = await fetch_public_spot_market("BTCUSDT")
    assert snap is not None
    assert snap["price"] == 50000.5
    assert snap["volume"] == 200.0
    assert snap["quote_volume"] == 200.0 * 50000.5
    assert snap["source"] == "kraken_public"
    assert snap["order_book"]["best_bid"] == 50000.0


@pytest.mark.asyncio
async def test_oracle_quick_kraken_fallback(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def no_binance(pair):
        return None

    async def no_cmc(asset, session=None):
        return None

    async def no_coinbase(pair):
        return None

    async def kraken(pair):
        return {
            "price": 41000.0,
            "change_24h": -0.5,
            "volume": 150.0,
            "quote_volume": 6_150_000.0,
            "source": "kraken_public",
            "order_book": {"best_bid": 40999.0, "best_ask": 41001.0, "spread_bps": 0.49},
        }

    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", no_binance)
    monkeypatch.setattr("coinmarketcap_api.fetch_spot_ticker", no_cmc)
    monkeypatch.setattr("coinbase_public_api.fetch_public_spot_market", no_coinbase)
    monkeypatch.setattr("kraken_public_api.fetch_public_spot_market", kraken)

    async def passthrough_enrich(m, a, session=None):
        return m

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", passthrough_enrich)

    client = TestClient(app)
    res = client.get("/oracle/BTC/quick?lang=en&ux_mode=beginner")
    assert res.status_code == 200
    body = res.json()
    assert body.get("price") == 41000.0
    assert body.get("price_source") == "kraken"
    assert body.get("quote_volume") == 6_150_000.0
