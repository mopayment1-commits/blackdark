"""Live refresh policy — entitlements-driven poll intervals (Trust Pulse / Oracle / Ledger)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-live-refresh")

from dashboard import app
from live_refresh_policy import live_refresh_policy_for_plan


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_anonymous_refresh_policy_free_interval(client):
    res = client.get("/api/entitlements/refresh-policy")
    assert res.status_code == 200
    data = res.json()
    assert 30 <= int(data["poll_interval_sec"]) <= 60
    assert data["live_stream_enabled"] is False
    assert data.get("server_enforced") is True


def test_paid_plan_faster_poll_and_stream():
    pro = live_refresh_policy_for_plan("pro")
    free = live_refresh_policy_for_plan("free")
    assert pro["poll_interval_sec"] < free["poll_interval_sec"]
    assert pro["live_stream_enabled"] is True
    assert free["live_stream_enabled"] is False
    assert pro["trust_pulse_stream"] == "/api/trust-pulse/stream"


def test_dashboard_includes_live_refresh_script():
    html = open("templates/dashboard.html", encoding="utf-8").read()
    assert "bd_live_refresh.js" in html
    assert "BDLiveRefresh" in html


def test_landing_and_ledger_wire_live_refresh():
    landing = open("templates/landing.html", encoding="utf-8").read()
    ledger = open("templates/oracle_accuracy.html", encoding="utf-8").read()
    assert "bd_live_refresh.js" in landing
    assert "BDLiveRefresh" in landing
    assert "bd_live_refresh.js" in ledger
    assert "BDLiveRefresh" in ledger
