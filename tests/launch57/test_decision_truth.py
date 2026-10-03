"""Launch-57 Decision Truth baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.decision_truth_common import (
    INTERNAL_DECISION_TRUTH_COMPONENTS,
    AbstainReason,
    DecisionState,
    acceptance_criteria_status,
    attach_decision_truth_envelope,
    build_decision_contract,
    build_decision_truth_gate,
    evaluate_decision_state,
    record_decision_truth_signal,
    verify_no_stale_as_live,
)


def test_internal_components_registry():
    from launch57.decision_truth_common import build_decision_truth_component_registry

    registry = build_decision_truth_component_registry()
    assert len(registry) == len(INTERNAL_DECISION_TRUTH_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"


def test_stale_cannot_appear_live():
    check = verify_no_stale_as_live(
        freshness_state="STALE",
        presented_as_live=True,
        evidence_label="LIVE",
    )
    assert check["ok"] is False
    assert check["stale_as_live_blocked"] is True


def test_live_freshness_passes_stale_check():
    check = verify_no_stale_as_live(
        freshness_state="LIVE",
        presented_as_live=True,
        evidence_label="LIVE",
    )
    assert check["ok"] is True


def test_gate_blocks_conflict():
    gate = build_decision_truth_gate(
        freshness_state="LIVE",
        quality_state="insufficient",
        evidence_label="LIVE",
        conflicting=True,
    )
    assert gate["all_gates_pass"] is False
    assert gate["gates"]["no_material_conflict"] is False


def test_evaluate_abstain_on_conflict():
    gate = build_decision_truth_gate(
        freshness_state="LIVE",
        quality_state="insufficient",
        evidence_label="LIVE",
        conflicting=True,
    )
    result = evaluate_decision_state(gate=gate)
    assert result["decision_state"] == DecisionState.ABSTAIN.value
    assert result["abstain_reason"] == AbstainReason.CONFLICTING_SIGNALS.value


def test_evaluate_act_when_gates_pass():
    gate = build_decision_truth_gate(
        freshness_state="LIVE",
        quality_state="decision_grade",
        evidence_label="LIVE",
        presented_as_live=True,
        conflicting=False,
    )
    result = evaluate_decision_state(gate=gate)
    assert result["decision_state"] == DecisionState.ACT.value
    assert result["act_allowed"] is True


def test_evaluate_wait_on_stale_only():
    gate = build_decision_truth_gate(
        freshness_state="STALE",
        quality_state="decision_grade",
        evidence_label="DELAYED",
        presented_as_live=False,
    )
    result = evaluate_decision_state(gate=gate)
    assert result["decision_state"] in {DecisionState.WAIT.value, DecisionState.ABSTAIN.value}
    assert result["act_allowed"] is False


def test_decision_contract_fields():
    contract = build_decision_contract(
        capability_id=2,
        launch_item_id=2,
        decision_state="ABSTAIN",
        symbol="BTC",
        freshness_state="STALE",
        evidence_label="DELAYED",
        quality_state="decision_grade",
        abstain_reason="stale_data",
    )
    assert contract["decision_id"].startswith("dt_")
    assert contract["immutable_after_issuance"] is True
    assert contract["decision_state"] == "ABSTAIN"


def test_attach_decision_truth_envelope_stale_gate():
    body = {
        "launch_item_id": 2,
        "capability_id": 641,
        "success": False,
        "decision_live_blocked": True,
        "freshness_state": "STALE",
        "presented_as_live": False,
        "error": "decision_blocked_stale_or_unknown_data",
    }
    out = attach_decision_truth_envelope(body, launch_item_id=2)
    assert out["launch57_decision_truth"]["internal_support_only"] is True
    evaluated = out["launch57_decision_truth"]["evaluated_decision"]
    assert evaluated["decision_state"] == DecisionState.ABSTAIN.value
    assert evaluated["act_allowed"] is False


def test_attach_decision_truth_envelope_live_path():
    body = {
        "launch_item_id": 7,
        "capability_id": 35,
        "success": True,
        "freshness_state": "LIVE",
        "presented_as_live": True,
        "provenance": {"quality_state": "decision_grade"},
        "symbol": "BTC",
    }
    out = attach_decision_truth_envelope(body, launch_item_id=7)
    evaluated = out["launch57_decision_truth"]["evaluated_decision"]
    assert evaluated["decision_state"] == DecisionState.ACT.value


def test_decision_truth_signal_persisted(tmp_path, monkeypatch):
    store = tmp_path / "launch57_decision_truth_signals.jsonl"
    monkeypatch.setattr("launch57.decision_truth_common._SIGNAL_STORE", store)
    row = record_decision_truth_signal(
        capability_id=2,
        decision_state="ABSTAIN",
        reason="stale_data",
    )
    assert row["signal_id"].startswith("dt_sig_")
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_stale_gate_body_includes_decision_truth():
    from launch57.decision_common import stale_gate_body

    body = stale_gate_body(
        capability_id=2,
        launch_item_id=2,
        surface="oracle",
        symbol="BTC",
        spine={"freshness_state": "STALE", "data_spine": {}},
        entrypoint="test_entry",
    )
    assert "launch57_decision_truth" in body
    assert body["launch57_decision_truth"]["evaluated_decision"]["act_allowed"] is False


def test_acceptance_criteria_core_checks():
    status = acceptance_criteria_status()
    assert status["ac03_evidence_class_canonical"] is True
    assert status["ac07_abstain_reachable"] is True
    assert status["ac09_act_requires_valid_evidence"] is True
    assert status["ac22_no_false_pass_live"] is True
    assert status["stale_as_live_blocked"] is True
