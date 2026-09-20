"""Launch-57 Batch I — upgrade PARTIAL rows #1, #2, #6 only."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"batch-i-{uuid.uuid4().hex[:8]}")
    return client


def test_dashboard_wires_batch_i_trust_pulse_routes():
    dash = _dash()
    assert "LAUNCH57_COMMAND_HOME = '/api/launch57/command-home'" in dash
    assert "LAUNCH57_SINGLE_SENTENCE_ORACLE = '/api/launch57/single-sentence-oracle'" in dash
    assert "LAUNCH57_EVIDENCE_CLASS = '/api/launch57/evidence-class'" in dash
    assert 'id="tpCommandQuestion"' in dash
    assert "resolveLaunch57OracleBinding" in dash
    assert "fetchLaunch57EvidenceClass" in dash
    assert 'data-launch-item-id="6"' in dash


def test_command_home_exposes_question_launch_1(authed_client, monkeypatch):
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
            "launch_item_id": 2,
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "BTC: WAIT — governed."},
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 1
    assert body.get("command_question")
    assert (body.get("six_heroes_command_home") or {}).get("question")


def test_broken_command_home_handler_fails_launch_1(authed_client, monkeypatch):
    async def broken(*args, **kwargs):
        raise RuntimeError("kill_switch_edge_ui_batch2")

    monkeypatch.setattr("launch57.edge_ui_batch2.six_heroes_command_home", broken)
    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 503


def test_single_sentence_oracle_route_launch_2(authed_client):
    res = authed_client.get(
        "/api/launch57/single-sentence-oracle",
        params={"symbol": "BTC", "decision_action": "ACT", "decision_sentence": "BTC: ACT"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 2
    sso = body.get("single_sentence_oracle") or {}
    assert sso.get("action") in {"ACT", "WAIT", "ABSTAIN"}
    assert sso.get("sentence")


def test_broken_single_sentence_oracle_handler_fails_launch_2(authed_client, monkeypatch):
    async def broken(**kwargs):
        raise RuntimeError("kill_switch_trust_batch1")

    monkeypatch.setattr("launch57.trust_batch1.single_sentence_oracle", broken)
    res = authed_client.get("/api/launch57/single-sentence-oracle", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_oracle_route_survives_command_home_failure(authed_client, monkeypatch):
    async def broken_home(*args, **kwargs):
        raise RuntimeError("kill_switch_edge_ui_batch2")

    async def fake_oracle(**kwargs):
        return {
            "launch_item_id": 2,
            "decision_action": "ACT",
            "single_sentence_oracle": {"action": "ACT", "sentence": "BTC: ACT — standalone route."},
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.six_heroes_command_home", broken_home)
    monkeypatch.setattr("launch57.trust_batch1.single_sentence_oracle", fake_oracle)

    home_res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert home_res.status_code == 503
    oracle_res = authed_client.get("/api/launch57/single-sentence-oracle", params={"symbol": "BTC"})
    assert oracle_res.status_code == 200
    assert oracle_res.json().get("launch_item_id") == 2


def test_evidence_class_route_launch_6():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/evidence-class", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 6
    assert body.get("user_facing_label") in {"LIVE", "DELAYED", "SIM"}
    display = body.get("evidence_display") or {}
    assert display.get("launch_item_id") == 6


def test_broken_evidence_class_handler_fails_launch_6(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("kill_switch_trust_batch1")

    monkeypatch.setattr("launch57.trust_batch1.evidence_class_surface", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/evidence-class", params={"symbol": "BTC"})
    assert res.status_code == 500
