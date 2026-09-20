"""Launch-57 Batch F — visible derivatives / arbitrage consumer paths (#25–#30, #43)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _derivatives_intel_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_FUTURES_OI")
    end = dash.index("let lastVisibleTrust")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"derivatives-visible-batch-f-{uuid.uuid4().hex[:8]}")
    return client


def test_dashboard_wires_launch57_derivatives_intelligence_routes():
    block = _derivatives_intel_block()
    assert "LAUNCH57_FUTURES_OI = '/api/launch57/futures-oi'" in block
    assert "LAUNCH57_FUNDING_RATE = '/api/launch57/funding-rate'" in block
    assert "LAUNCH57_LIQUIDATION = '/api/launch57/liquidation-intelligence'" in block
    assert "LAUNCH57_TAKER_LEVERAGE = '/api/launch57/taker-leverage'" in block
    assert "LAUNCH57_DERIVATIVES_SENTIMENT = '/api/launch57/derivatives-sentiment'" in block
    assert "LAUNCH57_ORDER_BOOK = '/api/launch57/order-book'" in block
    assert "LAUNCH57_SPOT_PERP_ARBITRAGE = '/api/launch57/spot-perp-arbitrage'" in block
    assert "function loadLaunch57DerivativesIntelligence" in _dash()
    assert 'id="launch57-derivatives-intelligence"' in _dash()


def test_load_oi_uses_launch57_not_legacy_market_open_interest():
    oi = _dash().split("async function loadOI()", 1)[1].split("async function loadArbitrage", 1)[0]
    assert "LAUNCH57_FUTURES_OI" in oi
    assert "LAUNCH57_FUNDING_RATE" in oi
    assert "/api/market/open-interest" not in oi


def test_load_arbitrage_uses_launch57_net_edge_gate_not_legacy_arbitrage_api():
    arb = _dash().split("async function loadArbitrage", 1)[1].split("async function loadInbox", 1)[0]
    assert "LAUNCH57_SPOT_PERP_ARBITRAGE" in arb
    assert "/api/arbitrage/" not in arb
    assert "cost_claim_allowed" in arb
    assert "gross_spread_only" in _dash().split("function launch57QualifiedArbitrageOpportunities", 1)[1].split("function renderLaunch57DerivativesIntel", 1)[0]
    assert "Net-Edge (#5)" in arb


def test_futures_oi_route_launch_25(authed_client):
    res = authed_client.get("/api/launch57/futures-oi", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 25


def test_broken_futures_oi_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("futures_oi_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch1.futures_open_interest_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-25-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/futures-oi", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_funding_rate_route_launch_26(authed_client):
    res = authed_client.get("/api/launch57/funding-rate", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 26


def test_broken_funding_rate_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("funding_rate_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch1.funding_rate_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-26-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/funding-rate", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_liquidation_route_launch_27(authed_client):
    res = authed_client.get("/api/launch57/liquidation-intelligence", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 27


def test_broken_liquidation_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("liquidation_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch1.liquidation_intelligence_light", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-27-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/liquidation-intelligence", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_taker_leverage_route_launch_28(authed_client):
    res = authed_client.get("/api/launch57/taker-leverage", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 28
    assert "taker_buy_sell_pressure" in body
    assert "estimated_leverage_ratio" in body


def test_broken_taker_leverage_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("taker_leverage_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch1.taker_buy_sell_pressure", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-28-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/taker-leverage", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_derivatives_sentiment_route_launch_29(authed_client):
    res = authed_client.get("/api/launch57/derivatives-sentiment", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 29


def test_broken_derivatives_sentiment_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("derivatives_sentiment_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch1.derivatives_sentiment_composite", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-29-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/derivatives-sentiment", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_order_book_route_launch_30(authed_client):
    res = authed_client.get("/api/launch57/order-book", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 30


def test_broken_order_book_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("order_book_handler_removed")

    monkeypatch.setattr("launch57.derivatives_batch2.order_book_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-30-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/order-book", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_spot_perp_arbitrage_route_launch_43(authed_client, monkeypatch):
    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": "quant", "minimum_tier": "quant"},
    )
    res = authed_client.get("/api/launch57/spot-perp-arbitrage", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 43


def test_broken_spot_perp_arbitrage_handler_fails(monkeypatch):
    from dashboard import app

    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": "quant", "minimum_tier": "quant"},
    )

    async def broken(**kwargs):
        raise RuntimeError("spot_perp_arbitrage_handler_removed")

    monkeypatch.setattr("launch57.edge_ui_batch1.spot_perp_arbitrage_scanner", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"derivatives-batch-f-broken-43-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/spot-perp-arbitrage", params={"symbol": "BTC", "tier": "quant"})
    assert res.status_code == 500
