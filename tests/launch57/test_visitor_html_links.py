"""Visitor-visible links must return HTML — never raw anonymous JSON errors."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    return TestClient(app)


def test_home_pricing_section_present(client):
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'id="pricing"' in res.text
    assert 'id="trust-pulse"' in res.text
    assert "real-time-prices" in res.text


def test_pricing_route_redirects_to_home_anchor(client):
    res = client.get("/pricing", headers={"Accept": "text/html"}, follow_redirects=False)
    assert res.status_code == 302
    assert res.headers.get("location") == "/#pricing"


def test_refund_public_html_200(client):
    res = client.get("/refund", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "text/html" in (res.headers.get("content-type") or "")
    assert "Anonymous access denied" not in res.text


def test_identity_standards_public_html_200(client):
    res = client.get("/identity-standards", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "text/html" in (res.headers.get("content-type") or "")
    assert "Identity standards" in res.text
    assert "Anonymous access denied" not in res.text


def test_profile_anonymous_html_login_gate_not_json(client):
    res = client.get("/profile", headers={"Accept": "text/html"})
    assert res.status_code == 401
    assert "text/html" in (res.headers.get("content-type") or "")
    assert "Account required" in res.text or "Profile" in res.text
    assert "Anonymous access denied" not in res.text
    assert "/login?next=" in res.text


def test_dashboard_anonymous_html_login_gate_not_json(client):
    res = client.get("/dashboard?lens=operate", headers={"Accept": "text/html"})
    assert res.status_code == 401
    assert "text/html" in (res.headers.get("content-type") or "")
    assert "Anonymous access denied" not in res.text
    assert "/login" in res.text


def test_launch22_real_time_prices_public_json_for_page_fetch(client, monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 42000.0, "source": "binance:api.binance.com", "age_sec": 1.0, "change_24h": 0.5}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    res = client.get("/api/launch57/real-time-prices", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body["launch_item_id"] == 22
    assert body["freshness_state"] in {"LIVE", "NEAR_LIVE", "DELAYED", "STALE"}


@pytest.mark.asyncio
async def test_kill_real_time_prices_not_live_badge(monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 100.0, "source": "binance:api.binance.com", "age_sec": 120.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    from launch57.data_batch1 import real_time_prices

    out = await real_time_prices(symbol="BTC", params={})
    assert out["presented_as_live"] is False
    assert out["freshness_state"] == "STALE"
