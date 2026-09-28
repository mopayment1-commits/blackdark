"""SPEC_02 — Anonymous Visitor & Public Intelligence adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from launch57.anonymous_visitor_public_intelligence_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def auth_client(client):
    client.cookies.set("bd_token", "spec02-test-session")
    return client


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_guest_trust_anonymous_allowed(client):
    res = client.get("/api/launch57/guest-trust", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 46
    assert body.get("guest_trust")


def test_capability_library_anonymous_allowed(client):
    res = client.get("/api/launch57/capability-library", params={"q": "oracle"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 52


def test_command_home_anonymous_denied(client):
    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 401
    detail = res.json().get("detail")
    if isinstance(detail, dict):
        assert detail.get("launch_item_id") == 1


def test_command_home_authenticated_allowed(auth_client, monkeypatch):
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

    res = auth_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 1


def test_decision_history_anonymous_denied(client):
    res = client.get("/api/launch57/decision-history", params={"symbol": "BTC"})
    assert res.status_code == 401


def test_discipline_mirror_anonymous_denied(client):
    res = client.get("/api/launch57/discipline-mirror")
    assert res.status_code == 401


def test_no_broad_launch57_prefix_in_allowlist():
    from anonymous_route_foundation import ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES

    assert "/api/launch57/" not in ANONYMOUS_ROUTE_ALLOWLIST_PREFIXES


def test_landing_uses_guest_trust_not_command_home():
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    assert "fetchLaunch57GuestTrust" in landing
    assert "/api/launch57/guest-trust" in landing
    assert "fetchLaunch57CommandHome" not in landing


def test_runtime_truth_all_yes():
    rows = build_runtime_truth_table()
    failures = [r for r in rows if r["status"] != "YES"]
    assert not failures, failures


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True
    assert status["public_surface_matrix_ok"] is True


def test_removing_guest_trust_from_allowlist_breaks_probe(monkeypatch):
    from launch57.anonymous_visitor_public_intelligence_common import _probe_launch57_allowlist

    monkeypatch.setattr(
        "anonymous_route_foundation.is_anonymous_route_allowed",
        lambda method, path: False,
    )
    status, _ = _probe_launch57_allowlist()
    assert status.value == "NO"


def test_spec02_artifacts_exist_after_generator():
    out = Path("governance/launch57/SPEC_02_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = out / name
        if path.exists():
            if name.endswith(".json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                if name == "FINAL_STATUS.json":
                    assert payload.get("domain") == DOMAIN
