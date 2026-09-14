"""P4 evidence, simulation, calibration, history tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from decision_truth import govern_decision_payload
from decision_truth.anti_cherry_picking import validate_performance_claim
from decision_truth.calibration import append_calibration_observation, evaluate_calibration
from decision_truth.change_detector import detect_decision_changes
from decision_truth.evidence_grade import evaluate_evidence_grade
from decision_truth.evidence_taxonomy import resolve_evidence_class
from decision_truth.history_integrity import record_history_event, recent_history
from decision_truth.lifecycle import evaluate_evidence_lifecycle
from decision_truth.outcome_ledger import pre_register_decision, record_outcome_observed
from decision_truth.simulation import evaluate_simulation_context


def _payload(**overrides):
    base = {
        "kind": "cross_exchange",
        "symbol": "BTC",
        "quote_amount": 1000,
        "net_profit_usdt": 10,
        "total_slippage_bps": 3,
        "trading_fees_usdt": 0.2,
        "withdrawal_fee_usdt": 0.05,
        "quote_age_ms": 120,
        "depth_usd": 250000,
        "fill_probability": 0.92,
        "estimated_recipients": 5,
        "live_duration_seconds": 8,
        "data_quality_score": 80,
        "evidence_class": "SHADOW_LIVE_FORWARD",
        "liquidity_ok": True,
        "risk_ok": True,
    }
    base.update(overrides)
    return base


def test_preregistration_before_outcome(tmp_path, monkeypatch):
    prereg_path = tmp_path / "prereg.jsonl"
    outcome_path = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr("decision_truth.outcome_ledger._PREREG_PATH", prereg_path)
    monkeypatch.setattr("decision_truth.outcome_ledger._OUTCOME_PATH", outcome_path)
    monkeypatch.setattr("decision_truth.outcome_ledger._BUFFER", {})

    reg = pre_register_decision({"symbol": "BTC", "decision_state": "AVAILABLE", "horizon": "intraday"})
    out = record_outcome_observed(reg["decision_id"], realized_outcome={"success": True}, evaluation_result="hit")
    assert out["record_type"] == "OUTCOME_OBSERVED"
    with pytest.raises(ValueError, match="outcome_without_preregistration"):
        record_outcome_observed("missing_id", realized_outcome={"success": False})


def test_post_outcome_cannot_masquerade_as_preregistered():
    claim = validate_performance_claim({"decision_id": "nope", "post_outcome_preregistration": True})
    assert claim["allowed"] is False


def test_append_only_history(tmp_path, monkeypatch):
    hist_path = tmp_path / "history.jsonl"
    monkeypatch.setattr("decision_truth.history_integrity._HISTORY_PATH", hist_path)
    record_history_event(previous_state="AVAILABLE", new_state="DEGRADED", cause="test")
    rows = recent_history()
    assert len(rows) == 1
    assert rows[0]["append_only"] is True


def test_correction_history_preserved(tmp_path, monkeypatch):
    hist_path = tmp_path / "history.jsonl"
    monkeypatch.setattr("decision_truth.history_integrity._HISTORY_PATH", hist_path)
    record_history_event(previous_state="A", new_state="B", cause="initial", correction=False)
    record_history_event(previous_state="B", new_state="B", cause="correction", correction=True)
    rows = recent_history()
    assert any(r.get("correction") for r in rows)


def test_decision_change_material_input():
    prev = {"decision_truth_state": "AVAILABLE", "evidence_class": "SIMULATED"}
    cur = {"decision_truth_state": "REJECTED", "evidence_class": "SIMULATED"}
    changes = detect_decision_changes(cur, prev)
    assert any(c["field"] == "decision_state" for c in changes)


def test_no_change_when_immaterial():
    prev = {"opportunity_score": 70}
    cur = {"opportunity_score": 71}
    changes = detect_decision_changes(cur, prev)
    assert changes == []


def test_calibration_insufficient(tmp_path, monkeypatch):
    monkeypatch.setattr("decision_truth.calibration._LEDGER_PATH", tmp_path / "cal.jsonl")
    out = evaluate_calibration(_payload())
    assert out["state"] == "CALIBRATION_INSUFFICIENT_DATA"


def test_calibration_buckets(tmp_path, monkeypatch):
    path = tmp_path / "cal.jsonl"
    monkeypatch.setattr("decision_truth.calibration._LEDGER_PATH", path)
    for i in range(6):
        append_calibration_observation(
            {
                "confidence_bucket": "70-80",
                "declared_probability": 0.75,
                "realized_success": i % 2 == 0,
                "evidence_class": "SHADOW_LIVE_FORWARD",
            }
        )
    out = evaluate_calibration(_payload(), evidence_class="SHADOW_LIVE_FORWARD")
    assert out["state"] in {"AVAILABLE", "CALIBRATION_WEAK"}
    assert out.get("brier_score") is not None


def test_simulation_disclosures():
    sim = evaluate_simulation_context(_payload(), economics={"expected_net_edge_usdt": 2.0, "total_costs_usd": 0.5, "capacity": {"capacity_usd": 1000, "state": "AVAILABLE"}, "uncertainty": {"low_usd": 1.0, "high_usd": 3.0, "state": "AVAILABLE"}})
    assert sim["disclosures"]["no_future_guarantee"] is True
    assert sim["disclosures"]["wording_policy"] == "must_not_imply_live_outcome"


def test_portfolio_simulation_unavailable():
    sim = evaluate_simulation_context(_payload(), economics={"expected_net_edge_usdt": 1.0}, portfolio_context={"state": "PORTFOLIO_CONTEXT_UNAVAILABLE"})
    assert sim["portfolio_simulation"]["state"] == "PORTFOLIO_SIMULATION_UNAVAILABLE"


def test_evidence_grade_no_hardcoded_default():
    grade = evaluate_evidence_grade({"data_quality_score": 10}, economics={}, calibration={"state": "CALIBRATION_INSUFFICIENT_DATA"}, simulation={"state": "UNAVAILABLE"})
    assert grade["overall_grade"] == "UNAVAILABLE"


def test_explainable_grade():
    grade = evaluate_evidence_grade(
        _payload(),
        economics={"total_costs_usd": 1.0, "cost_autopsy": [{}], "capacity": {"capacity_usd": 1000, "state": "AVAILABLE"}},
        calibration={"state": "AVAILABLE"},
        simulation={"state": "AVAILABLE", "institutional_methodology": {"sample_adequacy": {"state": "UNAVAILABLE"}, "out_of_sample": {"state": "UNAVAILABLE"}, "walk_forward": {"state": "UNAVAILABLE"}, "regime_segmentation": {"state": "UNAVAILABLE"}}},
        evidence_class="SHADOW_LIVE_FORWARD",
    )
    assert grade["state"] == "AVAILABLE"
    assert "components" in grade
    assert grade["overall_grade"] in {"A", "B", "C", "D", "E", "F"}


def test_evidence_taxonomy_no_auto_promotion():
    out = resolve_evidence_class({"source": "replay", "evidence_class_promotion_target": "PRODUCTION_VERIFIED"})
    assert out["automatic_promotion_blocked"] is True


def test_methodology_version_propagation():
    pack = evaluate_evidence_lifecycle(_payload(), pre_register=False)
    assert pack["methodology_versions"]["evidence_lifecycle"]


def test_anti_cherry_picking_violation():
    claim = validate_performance_claim({"losses_omitted": True, "decision_id": "x"})
    assert claim["allowed"] is False


def test_decision_contract_integration():
    out = govern_decision_payload(_payload(), run_data_governance=False)
    contract = (out.get("decision_truth") or {}).get("contract") or {}
    lifecycle = (out.get("decision_truth") or {}).get("evidence_lifecycle") or out.get("evidence_lifecycle") or {}
    assert contract.get("grade") not in {None, ""}
    assert lifecycle.get("simulation") or out.get("simulation_context")
    assert out.get("decision_id")
