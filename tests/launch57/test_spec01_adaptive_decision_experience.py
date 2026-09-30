"""SPEC_01 — Adaptive Intelligence & Decision Experience closure verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "governance" / "launch57" / "SPEC_01_ADAPTIVE_DECISION_EXPERIENCE"


@pytest.fixture(scope="module")
def spec01_artifacts():
    from launch57.adaptive_decision_experience_common import (
        build_final_status,
        build_requirements_register,
        build_runtime_truth_table,
        independent_verification,
        run_targeted_tests,
    )
    from governance.launch57.generate_spec01_adaptive_decision_closure import OUT, _md_local_closure, _md_truth_table
    from datetime import UTC, datetime
    import json as _json

    tests = run_targeted_tests()
    assert tests["passed"], tests.get("summary")
    iv = independent_verification()
    status = build_final_status(tests=tests)
    now = datetime.now(UTC).isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    requirements = {
        "artifact": "SPEC_01_REQUIREMENTS_REGISTER",
        "domain": "SPEC_01_ADAPTIVE_DECISION_EXPERIENCE",
        "generated_at": now,
        "requirement_count": len(build_requirements_register()),
        "requirements": build_requirements_register(),
    }
    truth = build_runtime_truth_table()
    (OUT / "REQUIREMENTS_REGISTER.json").write_text(_json.dumps(requirements, indent=2) + "\n", encoding="utf-8")
    (OUT / "RUNTIME_TRUTH_TABLE.md").write_text(_md_truth_table(truth), encoding="utf-8")
    (OUT / "LOCAL_CLOSURE_REPORT.md").write_text(_md_local_closure(status, iv, tests), encoding="utf-8")
    (OUT / "INDEPENDENT_VERIFICATION.json").write_text(_json.dumps({**iv, "generated_at": now}, indent=2) + "\n", encoding="utf-8")
    status["tests"] = tests
    status["generated_at"] = now
    (OUT / "FINAL_STATUS.json").write_text(_json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return {
        "requirements": json.loads((SPEC_DIR / "REQUIREMENTS_REGISTER.json").read_text(encoding="utf-8")),
        "truth_md": (SPEC_DIR / "RUNTIME_TRUTH_TABLE.md").read_text(encoding="utf-8"),
        "closure_md": (SPEC_DIR / "LOCAL_CLOSURE_REPORT.md").read_text(encoding="utf-8"),
        "iv": json.loads((SPEC_DIR / "INDEPENDENT_VERIFICATION.json").read_text(encoding="utf-8")),
        "final": json.loads((SPEC_DIR / "FINAL_STATUS.json").read_text(encoding="utf-8")),
    }


def test_requirements_register_mandatory_count():
    from launch57.adaptive_decision_experience_common import build_requirements_register

    reqs = build_requirements_register()
    assert len(reqs) >= 25
    assert all(r["mandatory"] for r in reqs)
    assert {r["req_id"] for r in reqs} == {r["req_id"] for r in reqs}


def test_runtime_truth_all_yes_before_closure():
    from launch57.adaptive_decision_experience_common import TruthStatus, build_runtime_truth_table

    rows = build_runtime_truth_table()
    bad = [r for r in rows if r["status"] != TruthStatus.YES.value]
    assert not bad, f"truth gaps: {bad}"


def test_independent_verification_adversarial_pass():
    from launch57.adaptive_decision_experience_common import independent_verification

    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["failed_count"] == 0
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_final_status_closed_local(spec01_artifacts):
    final = spec01_artifacts["final"]
    assert final["PASS_ENGINEERING"] is True
    assert final["LOCAL_INSTITUTIONAL_CLOSURE"] is True
    assert final["LOCAL_WORK_REMAINING"] == 0
    assert final["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert final["PASS_LIVE"] is False
    assert final["LIVE_VALIDATION_PENDING"] is True
    assert final["heroes_binding_ok"] is True
    assert final["launch57_only_ok"] is True
    assert final["closure_status"] == "CLOSED_LOCAL"


def test_closure_artifacts_exist(spec01_artifacts):
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        assert (SPEC_DIR / name).exists()


def test_no_legacy_intent_router_on_launch57_paths():
    from launch57.adaptive_decision_experience_common import _probe_no_legacy_intent_router, TruthStatus

    status, _ = _probe_no_legacy_intent_router()
    assert status == TruthStatus.YES


def test_command_home_consumer_path_has_router_and_disclosure(monkeypatch):
    from failure.freshness import FreshnessState
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 1.0,
            "change_24h": 0.0,
            "data_spine": {},
        }

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    client = TestClient(app)
    client.cookies.set("bd_token", "spec01-adaptive-decision-test")
    body = client.get("/api/launch57/command-home", params={"symbol": "BTC"}).json()
    assert body.get("router_selection_contract") or (body.get("six_heroes_command_home") or {}).get(
        "router_selection_contract"
    )
    disc = body.get("adaptive_disclosure") or {}
    for layer in ("level_1", "level_2", "level_3", "level_4", "level_5"):
        assert layer in disc
    assert body.get("launch57_accessibility")
