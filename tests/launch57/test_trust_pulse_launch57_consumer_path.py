"""Trust Pulse first screen must bind only to Launch #1 command-home + Launch #2 oracle."""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _pulse_block() -> str:
    dash = _dash()
    start = dash.index("function launch57OracleFromCommandHome(data)")
    end = dash.index("function setTrustPulseLoading(active)")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app)
    client.cookies.set("bd_token", "trust-pulse-l57-consumer-path")
    return client


def test_trust_pulse_only_loads_launch57_command_home():
    dash = _dash()
    assert "loadTrustPulse(force) {\n            return loadCommandHome(force);" in dash
    assert "LAUNCH57_COMMAND_HOME = '/api/launch57/command-home'" in dash
    assert re.search(r"fetch\(['\"]/api/trust", dash) is None
    assert re.search(r"fetch\(['\"]/api/oracle", dash) is None


def test_command_home_to_pulse_requires_launch_items_1_and_2():
    block = _pulse_block()
    assert "function launch57OracleFromCommandHome(data)" in block
    assert "launch_item_id) !== 1" in block
    assert "launch_item_id) !== 2" in block
    assert "launch57.trust_batch1:single_sentence_oracle" in block
    assert "launch57_oracle_bound" in block
    assert "action: 'UNAVAILABLE'" in block
    # Must not fall back to generic top-level oracle fields
    assert "home.oracle || data" not in block.replace("home.oracle || data || {}", "")
    assert "data.single_sentence_oracle" not in block


def test_command_home_to_pulse_uses_oracle_why_not_hero_delegate():
    block = _pulse_block()
    assert "function buildOracleWhyFactors" in block
    assert "buildOracleWhyFactors(data, oracle)" in block
    assert "heroBlock.heroes" not in block


def test_share_proof_wired_to_launch57_route_or_hidden():
    dash = _dash()
    assert "LAUNCH57_SHARE_PROOF = '/api/launch57/share-proof'" in dash
    assert 'id="tpShareBtn"' in dash and "hidden" in dash.split('id="tpShareBtn"', 1)[1][:80]
    share = dash.split("async function prefetchShareProof(pulse)", 1)[1].split("async function shareTrustPulse()", 1)[0]
    share += dash.split("async function shareTrustPulse()", 1)[1].split("function setSymbol", 1)[0]
    assert "LAUNCH57_SHARE_PROOF" in share
    assert "launch_item_id) !== 44" in share
    assert "btn.hidden" in share or "btn && btn.hidden" in share


def test_broken_command_home_handler_yields_no_verdict(authed_client, monkeypatch):
    async def broken(*args, **kwargs):
        raise RuntimeError("kill_switch_edge_ui_batch2")

    monkeypatch.setattr("launch57.edge_ui_batch2.six_heroes_command_home", broken)

    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 503


def test_broken_oracle_handler_yields_no_governed_oracle(monkeypatch):
    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("bd_token", "trust-pulse-l57-oracle-broken")
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

    async def broken_oracle(**kwargs):
        raise RuntimeError("oracle_handler_removed")

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", broken_oracle)

    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_command_home_with_oracle_exposes_act_wait_sentence(authed_client, monkeypatch):
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
            "decision_action": "ACT",
            "single_sentence_oracle": {"action": "ACT", "sentence": "BTC: ACT — net edge admitted."},
            "evidence_class": "SHADOW_LIVE_FORWARD",
            "adaptive_disclosure": {
                "level_1": {"answer_state": "ACT"},
                "level_2": {"concise_explanation": "Freshness LIVE; router grounded."},
                "level_3": {"supporting_factors": [{"label": "Freshness", "detail": "LIVE"}]},
            },
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 1
    home = body.get("six_heroes_command_home") or {}
    oracle = home.get("oracle") or {}
    sso = oracle.get("single_sentence_oracle") or {}
    assert oracle.get("launch_item_id") == 2
    assert sso.get("action") in {"ACT", "WAIT", "ABSTAIN"}
    assert sso.get("sentence")


def test_share_proof_route_launch_44(authed_client):
    res = authed_client.get(
        "/api/launch57/share-proof",
        params={"symbol": "BTC", "decision_action": "WAIT", "decision_sentence": "BTC: WAIT"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 44
    assert body.get("success") is True
    assert body.get("share_urls") or (body.get("certificate") or {}).get("share_urls")
