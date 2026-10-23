"""Public chart bars for Lightweight Charts."""

import pytest


@pytest.mark.asyncio
async def test_public_chart_bars_binance(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_bars(pair, interval="1h", limit=200):
        return (
            [
                {
                    "open_time_ms": 1_700_000_000_000,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.5,
                    "volume": 10.0,
                }
            ],
            "data-api.binance.vision",
        )

    monkeypatch.setattr("market_context.fetch_binance_klines_bars", fake_bars)
    client = TestClient(app)
    res = client.get("/api/public/market/chart-bars?symbol=BTC&interval=1h&limit=50")
    assert res.status_code == 200
    body = res.json()
    assert body.get("ok") is True
    assert body.get("library") == "TradingView Lightweight Charts"
    assert len(body.get("bars") or []) == 1
    assert "binance" in str(body.get("source"))


@pytest.mark.asyncio
async def test_public_chart_bars_unavailable(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def empty_bars(pair, interval="1h", limit=200):
        return [], "none"

    async def no_ohlcv(asset, session=None):
        return []

    monkeypatch.setattr("market_context.fetch_binance_klines_bars", empty_bars)
    monkeypatch.setattr("coinpaprika_public_api.fetch_ohlcv_latest", no_ohlcv)
    client = TestClient(app)
    res = client.get("/api/public/market/chart-bars?symbol=BTC")
    assert res.status_code == 503
