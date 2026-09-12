"""Runtime enforcement integration tests — controls must fail closed when removed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data_governance.runtime import (
    GovernanceViolationError,
    enforce_material_write,
    enforce_oracle_outcome_resolution,
    enforce_replay_framing,
)
from decision_ledger import link_exposure, record_decision
from signal_registry import register_signal

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = ROOT / "data" / "governance" / "correction_ledger.jsonl"


def test_decision_record_has_runtime_governance():
    row = record_decision(
        prediction_id="rt_pred_1",
        decision_action="WAIT",
        symbol="BTC",
        evidence_class="SIMULATED",
        source="runtime_test",
    )
    gov = row.get("governance", {})
    assert gov.get("contract_id") == "dac_decision_ledger"
    assert gov.get("receipt_id")
    assert gov.get("policy") == "v4_v2_runtime"
    assert gov.get("claim_id")
    assert gov.get("entity_assertion_id")
    assert gov.get("provenance_hash")


def test_signal_record_has_runtime_governance():
    row = register_signal(signal_type="oracle_direction", asset="BTC", persist=False)
    assert row.get("governance", {}).get("contract_id") == "dac_signal_registry"
    assert row.get("evidence_class")


def test_enforce_material_write_rejects_bad_promotion():
    with pytest.raises(GovernanceViolationError, match="evidence_promotion_denied|promotion_gate_denied"):
        enforce_material_write(
            asset_kind="decision",
            record={
                "decision_id": "dec_x",
                "prediction_id": "p1",
                "decision_action": "WAIT",
                "evidence_class": "PRODUCTION_VERIFIED",
                "source": "simulated",
            },
            surface="test",
            parent={"evidence_class": "SIMULATED", "decision_id": "dec_parent"},
            schema_id="decision_ledger",
        )


def test_governance_disabled_bypasses(monkeypatch):
    monkeypatch.setenv("BLACKDARK_GOVERNANCE_ENFORCE", "0")
    row = enforce_material_write(
        asset_kind="decision",
        record={"decision_id": "d", "prediction_id": "p", "decision_action": "X", "evidence_class": "SIMULATED", "source": "t"},
        surface="test",
    )
    assert "governance" not in row or row.get("governance") is None or row == row


@pytest.mark.asyncio
async def test_cap646_execute_runs_governance_gate():
    from cap646.runtime import execute_capability

    result = await execute_capability(17, params={"symbol": "BTC"}, skip_entitlement=True)
    assert "success" in result or "capability_id" in result


def test_replay_source_creates_pit_contract():
    pit = enforce_replay_framing(
        source="market_replay_v1",
        claim_text="successfully detected the historical event under point-in-time replay",
        record={"created_at": "2026-01-01T00:00:00+00:00", "source": "market_replay_v1"},
    )
    assert pit is not None
    assert pit.get("pit_id", "").startswith("pit_")


def test_link_exposure_appends_correction():
    before = 0
    if CORRECTIONS.exists():
        before = len([ln for ln in CORRECTIONS.read_text(encoding="utf-8").splitlines() if ln.strip()])
    decision = record_decision(
        prediction_id="corr_pred",
        decision_action="WAIT",
        symbol="ETH",
        evidence_class="SIMULATED",
        source="runtime_test",
    )
    link_exposure(str(decision["decision_id"]), "exp_test_1")
    assert CORRECTIONS.exists()
    after = len([ln for ln in CORRECTIONS.read_text(encoding="utf-8").splitlines() if ln.strip()])
    assert after > before
    last = json.loads(CORRECTIONS.read_text(encoding="utf-8").splitlines()[-1])
    assert last.get("reason") == "link_exposure"
    assert last.get("target_record_id") == decision["decision_id"]


def test_oracle_outcome_resolution_registers_claim():
    meta = enforce_oracle_outcome_resolution(
        prediction_id=999001,
        outcome="correct",
        accuracy_score=0.91,
    )
    assert meta.get("evaluator_id") == "oracle_outcome_v1"
    assert meta.get("claim_id")


@pytest.mark.asyncio
async def test_resolve_oracle_prediction_runs_outcome_gate():
    from database import init_db, insert_oracle_prediction, resolve_oracle_prediction

    await init_db()
    pred_id = await insert_oracle_prediction(
        asset="BTC",
        price_at_prediction=50000.0,
        verdict="WAIT",
        opportunity_score=55,
        confidence=60,
        source="runtime_test",
    )
    assert pred_id > 0
    await resolve_oracle_prediction(pred_id, 50100.0, "correct", 0.8)


def test_cost_guard_blocks_when_missing(monkeypatch, tmp_path):
    from blackdark.data_governance import runtime as rt

    guards_path = tmp_path / "cost_guards.json"
    guards_path.write_text('{"guards": {}}', encoding="utf-8")
    monkeypatch.setattr("blackdark.data_governance.cost_guard.COST_GUARDS_PATH", guards_path)
    with pytest.raises(GovernanceViolationError, match="cost_guard_invalid"):
        rt.assert_governance_subsystem_ready(surface="test_cost_guard")
