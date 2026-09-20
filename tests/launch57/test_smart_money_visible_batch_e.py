"""Launch-57 Batch E — visible smart money consumer paths (#13–#20)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _smart_money_intel_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_ACCUMULATION")
    end = dash.index("let lastVisibleTrust")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"smart-money-visible-batch-e-{uuid.uuid4().hex[:8]}")
    return client


def test_dashboard_wires_launch57_smart_money_intelligence_routes():
    block = _smart_money_intel_block()
    assert "LAUNCH57_ACCUMULATION = '/api/launch57/accumulation-distribution'" in block
    assert "LAUNCH57_TOKEN_SCREENER = '/api/launch57/token-screener'" in block
    assert "LAUNCH57_ENTITY_WALLET = '/api/launch57/entity-wallet'" in block
    assert "LAUNCH57_EXCHANGE_FLOW = '/api/launch57/exchange-flow'" in block
    assert "LAUNCH57_WHALE_RATIO_FILTER = '/api/launch57/whale-ratio-filter'" in block
    assert "LAUNCH57_WHALE_ALERTS = '/api/launch57/whale-alerts'" in block
    assert "LAUNCH57_INTER_ENTITY_FLOW = '/api/launch57/inter-entity-flow'" in block
    assert "LAUNCH57_ADDRESS_LABELS = '/api/launch57/address-labels'" in block
    assert "function loadLaunch57SmartMoneyIntelligence" in _dash()
    assert 'id="launch57-smart-money-intelligence"' in _dash()


def test_load_whales_uses_launch57_not_legacy_whale_api():
    whales = _dash().split("async function loadWhales", 1)[1].split("function coversPlanBit", 1)[0]
    assert "LAUNCH57_ACCUMULATION" in whales
    assert "LAUNCH57_TOKEN_SCREENER" in whales
    assert "LAUNCH57_WHALE_RATIO_FILTER" in whales
    assert "/api/whale/" not in whales


def test_load_inbox_uses_launch57_whale_alerts_not_legacy_inbox():
    inbox = _dash().split("async function loadInbox", 1)[1].split("const launch57InboxDismissed", 1)[0]
    assert "LAUNCH57_WHALE_ALERTS" in inbox
    assert "/api/alerts/inbox" not in inbox


def test_accumulation_route_launch_13(authed_client):
    res = authed_client.get("/api/launch57/accumulation-distribution", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 13


def test_broken_accumulation_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("accumulation_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch1.accumulation_distribution_detection", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-13-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/accumulation-distribution", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_token_screener_route_launch_14(authed_client):
    res = authed_client.get("/api/launch57/token-screener", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 14


def test_broken_token_screener_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("token_screener_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch1.smart_money_token_screener", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-14-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/token-screener", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_entity_wallet_route_launch_15(authed_client):
    res = authed_client.get("/api/launch57/entity-wallet", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 15


def test_broken_entity_wallet_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("entity_wallet_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch2.entity_aware_wallet_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-15-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/entity-wallet", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_exchange_flow_route_launch_16(authed_client):
    res = authed_client.get("/api/launch57/exchange-flow", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 16


def test_broken_exchange_flow_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("exchange_flow_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch1.exchange_flow_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-16-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/exchange-flow", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_whale_ratio_filter_route_launch_17(authed_client):
    res = authed_client.get("/api/launch57/whale-ratio-filter", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 17
    assert "exchange_whale_ratio" in body
    assert "internal_flow_filter" in body


def test_broken_whale_ratio_filter_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("whale_ratio_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch1.exchange_whale_ratio", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-17-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/whale-ratio-filter", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_whale_alerts_route_launch_18(authed_client):
    res = authed_client.get("/api/launch57/whale-alerts", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 18


def test_broken_whale_alerts_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("whale_alerts_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch2.whale_accumulation_distribution_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-18-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/whale-alerts", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_inter_entity_flow_route_launch_19(authed_client):
    res = authed_client.get("/api/launch57/inter-entity-flow", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 19


def test_broken_inter_entity_flow_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("inter_entity_flow_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch2.inter_entity_flow_intelligence", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-19-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/inter-entity-flow", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_address_labels_route_launch_20(authed_client):
    res = authed_client.get("/api/launch57/address-labels", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 20


def test_broken_address_labels_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("address_labels_handler_removed")

    monkeypatch.setattr("launch57.smart_money_batch1.address_labels_cohorts", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"smart-money-batch-e-broken-20-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/address-labels", params={"symbol": "BTC"})
    assert res.status_code == 500
