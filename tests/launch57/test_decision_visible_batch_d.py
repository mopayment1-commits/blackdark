"""Launch-57 Batch D — visible decision + disclosure consumer paths (#7–#12, #47–#48)."""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _decision_intel_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_MARKET_REGIME")
    end = dash.index("const LAUNCH57_PRIMARY_INTENTS")
    return dash[start:end]


def _visible_disclosure_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_RISK_DISCLOSURE")
    end = dash.index("let lastVisibleTrust")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"decision-visible-batch-d-{uuid.uuid4().hex[:8]}")
    return client


def test_dashboard_wires_launch57_decision_intelligence_routes():
    block = _decision_intel_block()
    assert "LAUNCH57_MARKET_REGIME = '/api/launch57/market-regime'" in block
    assert "LAUNCH57_BEGINNER_MODE = '/api/launch57/beginner-mode'" in block
    assert "LAUNCH57_CROSS_SIGNAL = '/api/launch57/cross-signal-confirmation'" in block
    assert "LAUNCH57_CONTRADICTION = '/api/launch57/contradiction-detection'" in block
    assert "LAUNCH57_ACTIONABILITY = '/api/launch57/actionability-score'" in block
    assert "LAUNCH57_CONVICTION = '/api/launch57/conviction-engine'" in block
    assert "function loadLaunch57DecisionIntelligence" in _dash()
    assert 'id="launch57-decision-intelligence"' in _dash()


def test_dashboard_wires_risk_disclosure_click_and_abstain_reasons():
    dash = _dash()
    assert "LAUNCH57_RISK_DISCLOSURE = '/api/launch57/risk-disclosure'" in dash
    assert "LAUNCH57_ABSTAIN_REASONS = '/api/launch57/abstain-reasons'" in dash
    assert 'data-bd-call="openRiskDisclosure"' in dash
    assert "function openRiskDisclosure()" in dash
    assert 'id="tpAbstainReasons"' in dash
    assert "function renderAbstainReasonsBlock" in dash
    assert "function fetchLaunch48AbstainReasons" in dash
    assert "function gatePulseWithLaunch48Reasons" in dash
    abstain_render = dash.split("function renderAbstainReasonsBlock", 1)[1].split("async function prefetchVisibleDisclosure", 1)[0]
    assert "launch48_reasons" in abstain_render
    assert "pulse.why" not in abstain_render
    assert "#48" in abstain_render
    load_home = dash.split("async function loadCommandHome", 1)[1].split("function renderLaunch57Decision", 1)[0]
    assert "fetchLaunch48AbstainReasons" in load_home
    assert "gatePulseWithLaunch48Reasons" in load_home


def test_beginner_mode_wired_to_ux_mode_selector():
    dash = _dash()
    on_change = dash.split("function onUxModeChange()", 1)[1].split("function copyLastCertShare", 1)[0]
    assert "loadLaunch57DecisionIntelligence" in on_change
    load_intel = dash.split("async function loadLaunch57DecisionIntelligence", 1)[1].split("async function prefetchShareProof", 1)[0]
    assert "mode === 'beginner'" in load_intel
    assert "LAUNCH57_BEGINNER_MODE" in load_intel


def test_market_regime_route_launch_7(authed_client):
    res = authed_client.get("/api/launch57/market-regime", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 7


def test_broken_market_regime_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("market_regime_handler_removed")

    monkeypatch.setattr("launch57.decision_batch1.market_regime_compass", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-7-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/market-regime", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_beginner_mode_route_launch_8(authed_client):
    res = authed_client.get(
        "/api/launch57/beginner-mode",
        params={"symbol": "BTC", "verdict": "Neutral", "risk_score": 5.0},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 8
    assert body.get("beginner_mode") is True


def test_broken_beginner_mode_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("beginner_mode_handler_removed")

    monkeypatch.setattr("launch57.decision_batch1.beginner_decision_mode", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-8-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/beginner-mode", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_cross_signal_route_launch_9(authed_client):
    res = authed_client.get("/api/launch57/cross-signal-confirmation", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 9
    assert "cross_signal_confirmation" in body


def test_broken_cross_signal_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("cross_signal_handler_removed")

    monkeypatch.setattr("launch57.decision_batch1.cross_signal_confirmation", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-9-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/cross-signal-confirmation", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_contradiction_route_launch_10(authed_client):
    res = authed_client.get("/api/launch57/contradiction-detection", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 10
    assert "contradiction_detection" in body


def test_broken_contradiction_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("contradiction_handler_removed")

    monkeypatch.setattr("launch57.decision_batch1.contradiction_detection", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-10-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/contradiction-detection", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_actionability_route_launch_11(authed_client):
    res = authed_client.get("/api/launch57/actionability-score", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 11


def test_broken_actionability_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("actionability_handler_removed")

    monkeypatch.setattr("launch57.decision_batch1.smart_money_actionability_score", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-11-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/actionability-score", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_conviction_route_launch_12(authed_client):
    res = authed_client.get("/api/launch57/conviction-engine", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 12


def test_broken_conviction_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("conviction_handler_removed")

    monkeypatch.setattr("launch57.decision_batch2.smart_money_conviction_engine", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-12-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/conviction-engine", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_risk_disclosure_route_launch_47(authed_client):
    res = authed_client.get(
        "/api/launch57/risk-disclosure",
        params={"symbol": "BTC", "decision_action": "WAIT", "decision_truth_state": "ABSTAINED"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 47
    assert body.get("risk_disclosure", {}).get("one_click") is True


def test_broken_risk_disclosure_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("risk_disclosure_handler_removed")

    monkeypatch.setattr("launch57.trust_batch2.one_click_risk_disclosure", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-47-{uuid.uuid4().hex[:8]}")
    res = client.get(
        "/api/launch57/risk-disclosure",
        params={"symbol": "BTC", "decision_action": "WAIT"},
    )
    assert res.status_code == 500


def test_abstain_reasons_route_launch_48(authed_client):
    res = authed_client.get(
        "/api/launch57/abstain-reasons",
        params={"symbol": "BTC", "decision_action": "ABSTAIN", "decision_truth_state": "ABSTAINED"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 48
    assert body.get("hidden_as_error") is False
    assert isinstance(body.get("visible_reasons"), list)
    assert len(body["visible_reasons"]) > 0
    assert body.get("reasons_visible") is True


def test_wait_abstain_with_visible_reasons_from_api_only(authed_client):
    """Mandatory #48: WAIT/ABSTAIN with reasons → visible_reasons populated from #48 API only."""
    for action in ("WAIT", "ABSTAIN"):
        res = authed_client.get(
            "/api/launch57/abstain-reasons",
            params={"symbol": "BTC", "decision_action": action, "decision_truth_state": "ABSTAINED"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("launch_item_id") == 48
        reasons = body.get("visible_reasons") or []
        assert len(reasons) > 0
        assert body.get("reasons_visible") is True
        assert "fresh_inputs_required" in reasons or "sufficient_evidence_grade" in reasons


def test_no_orphan_wait_when_handler_killed_or_reasons_empty(monkeypatch):
    """Mandatory #48: kill handler or empty visible_reasons → no complete WAIT/ABSTAIN badge."""
    dash = _dash()
    gate = dash.split("function gatePulseWithLaunch48Reasons", 1)[1].split("function renderAbstainReasonsBlock", 1)[0]
    assert "action: 'UNAVAILABLE'" in gate
    assert "launch48_gated" in gate
    assert "!abstainFetch.reasons.length" in gate

    from dashboard import app

    async def empty_reasons(**kwargs):
        return {
            "launch_item_id": 48,
            "visible_reasons": [],
            "abstention_reject_disclosure": {"visible_reasons": []},
            "reasons_visible": False,
            "success": False,
            "binding_source": "launch57_phase2_trust_batch2",
        }

    monkeypatch.setattr("launch57.trust_batch2.abstain_reject_reasons_visible", empty_reasons)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-empty-48-{uuid.uuid4().hex[:8]}")
    res = client.get(
        "/api/launch57/abstain-reasons",
        params={"symbol": "BTC", "decision_action": "WAIT"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("visible_reasons") == []
    assert body.get("reasons_visible") is False


def test_broken_abstain_reasons_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("abstain_reasons_handler_removed")

    monkeypatch.setattr("launch57.trust_batch2.abstain_reject_reasons_visible", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"decision-visible-batch-d-broken-48-{uuid.uuid4().hex[:8]}")
    res = client.get(
        "/api/launch57/abstain-reasons",
        params={"symbol": "BTC", "decision_action": "WAIT"},
    )
    assert res.status_code == 500


def test_abstain_reasons_sourced_in_load_command_home_not_prefetch_disclosure():
    dash = _dash()
    load_home = dash.split("async function loadCommandHome", 1)[1].split("function renderLaunch57Decision", 1)[0]
    prefetch = dash.split("async function prefetchVisibleDisclosure", 1)[1].split("function renderLaunch57DecisionIntel", 1)[0]
    assert "fetchLaunch48AbstainReasons" in load_home
    assert "LAUNCH57_ABSTAIN_REASONS" not in prefetch
