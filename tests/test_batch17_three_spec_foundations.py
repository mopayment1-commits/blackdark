"""Batch17 three-spec foundation tests."""

from __future__ import annotations

from bd_platform.batch17_three_spec_foundations import batch17_foundation_status


def test_batch17_foundations_complete() -> None:
    status = batch17_foundation_status()
    assert status["evaluation_contamination"]["live_promotion"] is False
    assert status["evidence_class_gates"]["verified_production_blocked"] is True
    assert status["progressive_disclosure"]["critical_risk_never_hidden"] is True
    assert status["capability_graph"]["causal_without_evidence_blocked"] is True
    assert status["event_store"]["live_promotion"] is False
    assert status["source_rights"]["enforced"] is True
    assert status["outcome_quality"]["live_outcome_factory"] is False
    assert status["mass_replay"]["live_promotion"] is False
    assert status["cost_budget"]["autonomous_scaling"] is False
    assert status["router_contract"]["self_modifying"] is False
    assert status["walk_forward"]["live_evaluation"] is False
