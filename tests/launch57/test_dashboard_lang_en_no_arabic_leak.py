"""English dashboard must not leak Arabic command-home question text."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

ARABIC_INTENT_QUESTION = "ماذا أفعل الآن؟"


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app)
    client.cookies.set("bd_token", "dashboard-lang-en-no-arabic-leak")
    client.cookies.set("bd_lang", "en")
    return client


def test_dashboard_html_en_cookie_has_no_arabic_intent_question(authed_client, monkeypatch):
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
            "email": f"dash-lang-en-{uuid.uuid4().hex[:10]}@example.com",
            "password": "SecurePass1234!",
            "accepted_terms": True,
            "accepted_privacy": True,
        },
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200, reg.text

    res = authed_client.get("/dashboard", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'lang="en"' in res.text
    assert ARABIC_INTENT_QUESTION not in res.text
    assert "What do you need?" in res.text


def test_command_home_en_cookie_returns_english_question(authed_client, monkeypatch):
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

    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    home = res.json().get("six_heroes_command_home") or {}
    assert home.get("question") == "What do you need?"
    assert ARABIC_INTENT_QUESTION not in home.get("question", "")
