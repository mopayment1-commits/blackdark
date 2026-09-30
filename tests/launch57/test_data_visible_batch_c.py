"""Launch-57 Batch C — visible data consumer paths (#22–#24, #39–#42)."""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _data_spine_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_REAL_TIME_PRICES")
    end = dash.index("function renderMarketAssets")
    return dash[start:end]


def test_dashboard_wires_launch57_data_spine_routes():
    block = _data_spine_block()
    assert "LAUNCH57_REAL_TIME_PRICES = '/api/launch57/real-time-prices'" in block
    assert "LAUNCH57_OHLCV = '/api/launch57/ohlcv'" in block
    assert "LAUNCH57_QUOTE = '/api/launch57/quote'" in block
    assert "LAUNCH57_PIT_METRICS = '/api/launch57/point-in-time-metrics'" in block
    assert "LAUNCH57_DATA_PROVENANCE = '/api/launch57/data-provenance'" in block
    assert "LAUNCH57_FRESHNESS = '/api/launch57/freshness'" in block
    assert "LAUNCH57_UNIFIED_EXCHANGE = '/api/launch57/unified-exchange'" in block
    assert "function loadLaunch57DataSpine" in block
    assert "/api/market/klines" not in _dash().split("async function loadChart()", 1)[1].split("function renderMarketAssets", 1)[0]


def test_chart_hidden_when_ohlcv_unavailable():
    chart = _dash().split("async function loadChart()", 1)[1].split("async function renderMarketAssets", 1)[0]
    assert "LAUNCH57_OHLCV" in chart
    assert "!payload.success" in chart
    assert "series.setData([])" in chart


def test_freshness_chip_fail_closed_not_live_for_stale():
    block = _data_spine_block()
    assert "function launch57FreshnessChipLabel" in block
    assert "state === 'STALE'" in block
    assert "presented_as_live === true" in block
    assert re.search(r"['\"]LIVE['\"]", block.split("function launch57FreshnessChipLabel", 1)[1].split("function renderLaunch57DataSpine", 1)[0]) is None


def test_real_time_prices_route_launch_22():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/real-time-prices", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 22


def test_broken_real_time_prices_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("real_time_prices_handler_removed")

    monkeypatch.setattr("launch57.data_batch1.real_time_prices", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/real-time-prices", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_ohlcv_route_launch_23():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/ohlcv", params={"symbol": "BTC", "interval": "1h", "limit": 5})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 23


def test_broken_ohlcv_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("ohlcv_handler_removed")

    monkeypatch.setattr("launch57.data_batch1.ohlcv", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/ohlcv", params={"symbol": "BTC", "interval": "1h", "limit": 5})
    assert res.status_code == 500


def test_quote_route_launch_24():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/quote", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 24
    assert "quote" in body and "metadata" in body


def test_broken_quote_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("quote_handler_removed")

    monkeypatch.setattr("launch57.data_batch1.quote_data", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/quote", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_pit_metrics_route_launch_39():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/point-in-time-metrics", params={"symbol": "BTC", "price": 42000})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 39


def test_broken_pit_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("pit_handler_removed")

    monkeypatch.setattr("launch57.data_batch2.point_in_time_immutable_metrics", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/point-in-time-metrics", params={"symbol": "BTC", "price": 42000})
    assert res.status_code == 500


def test_data_provenance_route_launch_40():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/data-provenance", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 40


def test_broken_provenance_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("provenance_handler_removed")

    monkeypatch.setattr("launch57.data_batch2.data_quality_provenance_layer", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/data-provenance", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_freshness_route_launch_41_stale_not_live():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/freshness", params={"symbol": "BTC", "quote_age_ms": 120000, "quote_fresh": True})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 41
    assert body.get("freshness_state") == "STALE"
    assert body.get("presented_as_live") is False


def test_broken_freshness_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("freshness_handler_removed")

    monkeypatch.setattr("launch57.data_batch2.freshness_update_assurance", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/freshness", params={"symbol": "BTC", "quote_age_ms": 1000})
    assert res.status_code == 500


def test_unified_exchange_route_launch_42():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/unified-exchange", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 42


def test_broken_unified_exchange_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("unified_exchange_handler_removed")

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/unified-exchange", params={"symbol": "BTC"})
    assert res.status_code == 500
