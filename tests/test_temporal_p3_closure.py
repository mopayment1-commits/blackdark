"""P3 closure assertion verification from runtime probes and focused tests."""

from __future__ import annotations

from blackdark.temporal.p3_closure_verification import (
    evaluate_p3_closure_assertions,
    probe_canonical_authority_conflicts,
    probe_p3_deterministic_evaluation,
    probe_p3_historical_truth_mutation,
    probe_p3_prior_evidence_mutation,
    probe_p3_local_engineering_complete,
    probe_regime_context_contamination,
    probe_temp_ar_0164_status,
)
from blackdark.temporal.p3_requirement_registry import (
    P3_ATOMIC_REQUIREMENT_IDS,
    P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
)


def test_regime_context_contamination_runtime_probe() -> None:
    assert probe_regime_context_contamination() == 0


def test_canonical_authority_conflicts_runtime_probe() -> None:
    assert probe_canonical_authority_conflicts() == 0


def test_p3_historical_truth_mutation_runtime_probe() -> None:
    assert probe_p3_historical_truth_mutation() == 0


def test_p3_prior_evidence_mutation_runtime_probe() -> None:
    assert probe_p3_prior_evidence_mutation() == 0


def test_p3_deterministic_evaluation_runtime_probe() -> None:
    assert probe_p3_deterministic_evaluation() is True


def test_p3_local_engineering_complete_runtime_probe() -> None:
    complete, count = probe_p3_local_engineering_complete()
    assert complete is True
    assert count == 63


def test_temp_ar_0164_external_gate_pending() -> None:
    status = probe_temp_ar_0164_status()
    assert status["atomic_id"] == "TEMP-AR-0164"
    assert status["local_engineering_complete"] is True
    assert status["external_evidence_pending"] is True
    assert status["forward_time_passage_verified"] is False
    assert status["simulated_time_not_claimed_as_forward"] is True


def test_p3_requirement_inventory_reconciliation() -> None:
    assert P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 63
    assert P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 63
    assert len(P3_ATOMIC_REQUIREMENT_IDS) == 63
    assert P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ("TEMP-AR-0164",)


def test_p3_closure_assertions_aggregate() -> None:
    result = evaluate_p3_closure_assertions()
    assertions = result["closure_assertions"]

    assert assertions["REGIME_CONTEXT_CONTAMINATION"] == 0
    assert assertions["CANONICAL_AUTHORITY_CONFLICTS"] == 0
    assert assertions["P3_HISTORICAL_TRUTH_MUTATION"] == 0
    assert assertions["P3_PRIOR_EVIDENCE_MUTATION"] == 0
    assert assertions["P3_DETERMINISTIC_EVALUATION_REQUIREMENTS_PRESERVED"] is True
    assert assertions["P3_LOCAL_ENGINEERING_COMPLETE"] is True
    assert assertions["P3_CLOSED"] is True

    assert result["P3_TOTAL_ACTIVE_ATOMIC_REQUIREMENTS"] == 63
    assert result["P3_LOCAL_ENGINEERING_COMPLETE_COUNT"] == 63
    assert result["P3_UNIMPLEMENTED_ACTIVE_ATOMIC_REQUIREMENTS"] == 0
    assert result["P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS"] == ["TEMP-AR-0164"]
    assert "FAILURE_SURPRISE_ABSTENTION_COMPLETE" in result["accepted_p3_fixes"]
    assert "POST_OUTCOME_CANONICAL_TRUTH_ENFORCEMENT_COMPLETE" in result["accepted_p3_fixes"]
