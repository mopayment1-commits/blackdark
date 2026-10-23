"""Coinbase Exchange public API (no key)."""

import pytest

from coinbase_public_api import (
    fetch_public_spot_market,
    pair_to_product_id,
)


def test_pair_to_product_id():
    assert pair_to_product_id("BTCUSDT") == "BTC-USD"
    assert pair_to_product_id("ETH-USD") == "ETH-USD"


@pytest.mark.asyncio
async def test_fetch_public_spot_market(monkeypatch):
    ticker = {
        "price": "50000",
        "volume": "100",
        "bid": "49999",
        "ask": "50001",
        "time": "2026-01-01T00:00:00Z",
    }
    stats = {"open": "49000", "high": "51000", "low": "48000", "last": "50000", "volume": "100"}

    async def fake_get(session, path):
        if path.endswith("/ticker"):
            return ticker
        if path.endswith("/stats"):
            return stats
        if "/book" in path:
            return {"bids": [["49999", "1", 1]], "asks": [["50001", "1", 1]]}
        return None

    monkeypatch.setattr("coinbase_public_api._get_json", fake_get)
    async def fake_book(*args, **kwargs):
        return {
            "best_bid": 49999.0,
            "best_ask": 50001.0,
            "spread_bps": 0.4,
            "source": "coinbase_book",
        }

    monkeypatch.setattr("coinbase_public_api.fetch_order_book", fake_book)

    snap = await fetch_public_spot_market("BTCUSDT")
    assert snap is not None
    assert snap["price"] == 50000.0
    assert snap["volume"] == 100.0
    assert snap["quote_volume"] == 5_000_000.0
    assert snap["source"] == "coinbase_exchange"
    assert snap["order_book"]["best_bid"] == 49999.0


@pytest.mark.asyncio
async def test_oracle_quick_coinbase_fallback(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def no_binance(pair):
        return None

    async def no_cmc(asset, session=None):
        return None

    async def coinbase(pair):
        return {
            "price": 42000.0,
            "change_24h": 1.5,
            "volume": 200.0,
            "quote_volume": 8_400_000.0,
            "source": "coinbase_exchange",
            "order_book": {"best_bid": 41999.0, "best_ask": 42001.0, "spread_bps": 0.5},
        }

    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", no_binance)
    monkeypatch.setattr("coinmarketcap_api.fetch_spot_ticker", no_cmc)
    async def passthrough_enrich(m, a, session=None):
        return m

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", passthrough_enrich)
    monkeypatch.setattr("coinbase_public_api.fetch_public_spot_market", coinbase)

    client = TestClient(app)
    res = client.get("/oracle/BTC/quick?lang=en&ux_mode=beginner")
    assert res.status_code == 200
    body = res.json()
    assert body.get("price") == 42000.0
    assert body.get("price_source") == "coinbase"
    assert body.get("order_book", {}).get("best_bid") == 41999.0
