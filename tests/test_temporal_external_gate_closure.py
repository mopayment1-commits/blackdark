"""Closure verification tests for EXTERNAL_OR_LIVE_GATE scope."""

from __future__ import annotations

from blackdark.temporal.external_gate_closure_verification import evaluate_external_gate_closure_assertions
from blackdark.temporal.external_gate_requirement_registry import (
    EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS,
    EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS,
)


def test_external_gate_registry_matches_rtm_scope() -> None:
    assert EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 10
    assert len(EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS) == 10
    assert set(EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS) == set(EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS)


def test_external_gate_closure_assertions_pass() -> None:
    result = evaluate_external_gate_closure_assertions(runtime_signals={"p6_baseline_closed": True})
    assertions = result["closure_assertions"]
    assert assertions["EXTERNAL_GATE_MODULE_SURFACES"] == 0
    assert assertions["DOCUMENT_APPROVAL_PROHIBITIONS"] is True
    assert assertions["EVIDENCE_GATE_REQUIREMENTS"] is True
    assert assertions["SIMULATED_TIME_CANNOT_CLOSE_LIVE_GATE"] is True
    assert assertions["PASS_ENGINEERING_LOCAL_EVIDENCE_ONLY"] is True
    assert assertions["EXTERNAL_GATE_LOCAL_ENGINEERING_COMPLETE"] is True
    assert assertions["EXTERNAL_GATE_SCOPE_CLOSED"] is True


def test_per_atomic_status_pending_external_assurance() -> None:
    result = evaluate_external_gate_closure_assertions()
    for aid in EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS:
        probe = result["per_atomic_status"][aid]
        assert probe["local_engineering_complete"] is True
        if aid != "TEMP-AR-0432":
            assert probe.get("external_runtime_gate_pending") is True
