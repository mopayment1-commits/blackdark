"""Launch #2 Oracle — live consumer via /api/launch57/command-home only (no oracle mock)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from failure.freshness import FreshnessState

_DECISION_TIME = "2026-09-17T12:00:00.000Z"


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("bd_token", f"oracle-command-home-live-{uuid.uuid4().hex[:8]}")
    return client


@pytest.fixture
def live_spine(monkeypatch):
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

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)


def _oracle_from_body(body: dict) -> dict:
    home = body.get("six_heroes_command_home") or {}
    return home.get("oracle") or {}


def test_command_home_happy_consumer_real_oracle(authed_client, live_spine):
    res = authed_client.get(
        "/api/launch57/command-home",
        params={
            "symbol": "BTC",
            "decision_action": "WAIT",
            "decision_sentence": "BTC: WAIT — live consumer.",
            "decision_time": _DECISION_TIME,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 1
    home = body.get("six_heroes_command_home") or {}
    assert home.get("oracle_path") == "launch57.trust_batch1:single_sentence_oracle"

    oracle = _oracle_from_body(body)
    assert oracle.get("launch_item_id") == 2
    assert oracle.get("backend_entrypoint") == "single_sentence_oracle"
    sso = oracle.get("single_sentence_oracle") or {}
    assert sso.get("action") == "WAIT"
    assert "WAIT" in (sso.get("sentence") or "")

    assert oracle.get("b4_decision_timing", {}).get("activated") is True
    assert oracle.get("launch57_decision_truth") is not None
    assert oracle["launch57_decision_truth"].get("evaluated_decision") is not None


@pytest.mark.parametrize("action", ["ACT", "WAIT", "ABSTAIN"])
def test_command_home_oracle_act_wait_abstain_visible(authed_client, live_spine, action):
    res = authed_client.get(
        "/api/launch57/command-home",
        params={
            "symbol": "BTC",
            "decision_action": action,
            "decision_sentence": f"BTC: {action} — governed oracle.",
            "decision_time": _DECISION_TIME,
        },
    )
    assert res.status_code == 200
    body = res.json()
    oracle = _oracle_from_body(body)
    sso = oracle.get("single_sentence_oracle") or {}

    assert oracle.get("decision_action") == action
    assert sso.get("action") == action
    assert action in (sso.get("sentence") or "")
    assert oracle.get("b4_decision_timing", {}).get("activated") is True
    assert oracle.get("launch57_decision_truth") is not None


def test_command_home_oracle_kill_switch_fails_visibly(authed_client, live_spine, monkeypatch):
    async def broken_oracle(**kwargs):
        raise RuntimeError("oracle_handler_kill_switch")

    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", broken_oracle)

    res = authed_client.get(
        "/api/launch57/command-home",
        params={"symbol": "BTC", "decision_action": "WAIT", "decision_time": _DECISION_TIME},
    )
    assert res.status_code == 503
    body = res.json()
    assert body.get("error_code")
    assert "command home disabled" in str(body.get("detail") or "").lower()
    assert "six_heroes_command_home" not in body
    assert "single_sentence_oracle" not in str(body)
