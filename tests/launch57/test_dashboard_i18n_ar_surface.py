"""Authenticated Arabic dashboard must localize static chrome (not English leaks)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from i18n_service import t
from security_csrf import mint_csrf_token


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app)
    client.cookies.set("bd_token", "dashboard-i18n-ar-surface")
    token = mint_csrf_token()
    client.cookies.set("bd_csrf", token)
    client._bd_csrf = token  # type: ignore[attr-defined]
    return client


def test_dashboard_ar_localizes_static_chrome(authed_client, monkeypatch):
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

    reg = authed_client.post(
        "/api/auth/register",
        json={
            "email": f"dash-i18n-ar-{uuid.uuid4().hex[:10]}@example.com",
            "password": "SecurePass1234!",
            "accepted_terms": True,
        },
        headers={
            "Origin": "http://127.0.0.1",
            "X-CSRF-Token": authed_client._bd_csrf,
        },
    )
    assert reg.status_code == 200, reg.text

    res = authed_client.get("/dashboard?lang=ar", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'lang="ar"' in res.text
    assert 'dir="rtl"' in res.text
    assert t("dash.intent.question", "ar") in res.text
    assert t("dash.arb.title", "ar") in res.text
    assert t("oracle.get_decision", "ar") in res.text
    assert 'id="askBtn">Get Decision<' not in res.text
    assert "<h2>Arbitrage Engine</h2>" not in res.text
    assert "What do you need?" not in res.text
