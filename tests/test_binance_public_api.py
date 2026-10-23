"""Binance public REST helpers (no API key)."""

import pytest

from binance_public_api import (
    _ticker_from_24hr,
    fetch_public_spot_market,
    fetch_ticker_24hr,
)


def test_ticker_from_24hr_parses_fields():
    row = _ticker_from_24hr(
        {
            "lastPrice": "50000.5",
            "priceChangePercent": "1.25",
            "volume": "1200",
            "quoteVolume": "60000000",
            "closeTime": 1700000000000,
        },
        host="data-api.binance.vision",
    )
    assert row["price"] == 50000.5
    assert row["change_24h"] == 1.25
    assert row["quote_volume"] == 60000000.0
    assert "binance_rest" in row["source"]


@pytest.mark.asyncio
async def test_fetch_public_spot_market(monkeypatch):
    ticker = {
        "price": 100.0,
        "change_24h": -0.5,
        "volume": 10.0,
        "quote_volume": 1000.0,
        "source": "binance_rest:api.binance.com",
    }
    depth = {
        "best_bid": 99.9,
        "best_ask": 100.1,
        "spread_bps": 20.0,
        "source": "binance_depth:api.binance.com",
    }

    async def fake_ticker(pair, session=None):
        return ticker

    async def fake_depth(pair, limit=20, session=None):
        return depth

    monkeypatch.setattr("binance_public_api.fetch_ticker_24hr", fake_ticker)
    monkeypatch.setattr("binance_public_api.fetch_order_book", fake_depth)

    snap = await fetch_public_spot_market("BTCUSDT")
    assert snap is not None
    assert snap["price"] == 100.0
    assert snap["order_book"]["spread_bps"] == 20.0


def test_oracle_quick_uses_binance_snapshot(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_spot(pair):
        return {
            "price": 42000.0,
            "change_24h": 2.0,
            "volume": 100.0,
            "quote_volume": 4_200_000.0,
            "source": "binance_rest:data-api.binance.vision",
            "order_book": {"best_bid": 41999.0, "best_ask": 42001.0, "spread_bps": 0.5},
        }

    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", fake_spot)

    c = TestClient(app)
    res = c.get("/oracle/BTC/quick?lang=en&ux_mode=beginner")
    assert res.status_code == 200
    body = res.json()
    assert body.get("price") == 42000.0
    assert body.get("change_24h") == 2.0
    assert body.get("quote_volume") == 4_200_000.0
    assert body.get("order_book", {}).get("spread_bps") == 0.5
