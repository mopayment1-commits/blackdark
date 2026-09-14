"""P6 Operational Hardening tests."""

from __future__ import annotations

from blackdark.temporal.operational_hardening import (
    FAIL_CLOSED_ON_UNCERTAINTY,
    OperationalFailureClass,
    OperationalHardeningState,
    assess_operational_readiness,
    create_recovery_checkpoint,
    evaluate_fail_closed,
)


def test_fail_closed_on_leakage_rejection() -> None:
    assert FAIL_CLOSED_ON_UNCERTAINTY is True
    decision = evaluate_fail_closed(
        status="failed",
        error_code="TEMPORAL_LEAKAGE_REJECTED",
        preserved_evidence_ids=("ev-1",),
    )
    assert decision.admitted is False
    assert decision.failure_class == OperationalFailureClass.LEAKAGE_REJECTION
    assert decision.evidence_preserved is True


def test_fail_closed_preserves_evidence_on_pit_violation() -> None:
    decision = evaluate_fail_closed(
        status="failed",
        error_code="PIT_RECONSTRUCTION_EMPTY",
        preserved_event_id="evt-1",
    )
    assert decision.admitted is False
    assert decision.evidence_preserved is True


def test_recovery_checkpoint() -> None:
    state = OperationalHardeningState()
    cp = create_recovery_checkpoint(
        checkpoint_id="cp-1",
        run_id="run-1",
        preserved_event_id="evt-1",
        preserved_evidence_ids=("ev-1", "ev-2"),
        failure_class=OperationalFailureClass.PERSISTENCE_FAILURE,
    )
    state.record_checkpoint(cp)
    assert len(state.checkpoints) == 1
    assert state.checkpoints[0].preserved_evidence_ids == ("ev-1", "ev-2")


def test_operational_readiness_report() -> None:
    report = assess_operational_readiness(
        observability={"stages": [{"stage": "normalization", "status": "completed"}]},
        api_admin_gated=True,
    )
    assert report.fail_closed_enabled is True
    assert report.metrics_available is True
    assert report.security_controls["admin_gated_ingest"] is True
    assert report.readiness_score >= 0.75
