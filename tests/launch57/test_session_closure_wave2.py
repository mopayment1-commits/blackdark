"""Wave 2 — full session closure (logout, forgot password, expired session)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from dashboard import app

    return TestClient(app)


def test_logout_clears_bd_token_cookie(client):
    client.cookies.set("bd_token", "wave2-logout-test-token")
    res = client.post(
        "/api/auth/logout",
        headers={"Origin": "https://testserver"},
    )
    assert res.status_code == 200
    assert res.json().get("success") is True
    set_cookie = res.headers.get("set-cookie", "")
    assert "bd_token=" in set_cookie.lower()
    assert "max-age=0" in set_cookie.lower() or 'expires=Thu, 01 Jan 1970' in set_cookie


def test_forgot_password_returns_ok_not_500(client):
    res = client.post("/api/auth/forgot-password", json={"email": "nobody-wave2@example.com"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("ok") is True
    assert "reset link" in body.get("message", "").lower()


def test_expired_session_dashboard_denied(client):
    client.cookies.set("bd_token", "expired-or-invalid-session-token")
    res = client.get("/dashboard", headers={"Accept": "text/html"})
    assert res.status_code == 401
    assert "auth_required" in res.text or "Sign in" in res.text or "login" in res.text.lower()


def test_register_then_dashboard_with_valid_session(client, monkeypatch):
    from failure.freshness import FreshnessState

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 50000.0,
            "change_24h": 1.0,
            "data_spine": {},
        }

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "BTC: WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    email = f"wave2-session-{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True,
            "accepted_privacy": True},
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200, reg.text
    dash = client.get("/dashboard", headers={"Accept": "text/html"})
    assert dash.status_code == 200
    home = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert home.status_code == 200, home.text
