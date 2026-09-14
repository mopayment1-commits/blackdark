"""Operational hardening and production readiness (P6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Mapping, Sequence

from blackdark.temporal.metrics import temporal_metrics_status

OPERATIONAL_HARDENING_CONTRACT_VERSION = "p6.operational_hardening.1.0"
FAIL_CLOSED_ON_UNCERTAINTY = True


class OperationalFailureClass(str, Enum):
    PIT_VIOLATION = "pit_violation"
    LEAKAGE_REJECTION = "leakage_rejection"
    CONTAMINATION_REJECTION = "contamination_rejection"
    PERSISTENCE_FAILURE = "persistence_failure"
    REPLAY_FAILURE = "replay_failure"
    EVIDENCE_LOSS = "evidence_loss"


@dataclass(frozen=True, slots=True)
class RecoveryCheckpoint:
    checkpoint_id: str
    run_id: str
    preserved_event_id: str | None
    preserved_evidence_ids: tuple[str, ...]
    failure_class: OperationalFailureClass | None
    recovered: bool
    created_at: datetime

    def to_metadata(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "preserved_event_id": self.preserved_event_id,
            "preserved_evidence_ids": list(self.preserved_evidence_ids),
            "failure_class": self.failure_class.value if self.failure_class else None,
            "recovered": self.recovered,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class FailClosedDecision:
    admitted: bool
    failure_class: OperationalFailureClass | None
    reason: str
    evidence_preserved: bool
    temporal_integrity_preserved: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "failure_class": self.failure_class.value if self.failure_class else None,
            "reason": self.reason,
            "evidence_preserved": self.evidence_preserved,
            "temporal_integrity_preserved": self.temporal_integrity_preserved,
        }


@dataclass(frozen=True, slots=True)
class OperationalReadinessReport:
    fail_closed_enabled: bool
    metrics_available: bool
    recovery_supported: bool
    observability_stages_present: bool
    capacity_signals: Mapping[str, Any]
    security_controls: Mapping[str, bool]
    readiness_score: float
    defects: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "fail_closed_enabled": self.fail_closed_enabled,
            "metrics_available": self.metrics_available,
            "recovery_supported": self.recovery_supported,
            "observability_stages_present": self.observability_stages_present,
            "capacity_signals": dict(self.capacity_signals),
            "security_controls": dict(self.security_controls),
            "readiness_score": self.readiness_score,
            "defects": list(self.defects),
            "production_ready": not self.defects and self.readiness_score >= 1.0,
        }


@dataclass
class OperationalHardeningState:
    """Authoritative operational hardening runtime state."""

    checkpoints: list[RecoveryCheckpoint] = field(default_factory=list)

    def record_checkpoint(self, checkpoint: RecoveryCheckpoint) -> RecoveryCheckpoint:
        self.checkpoints.append(checkpoint)
        return checkpoint


def evaluate_fail_closed(
    *,
    status: str,
    error_code: str | None,
    preserved_evidence_ids: Sequence[str] = (),
    preserved_event_id: str | None = None,
) -> FailClosedDecision:
    if status == "completed":
        return FailClosedDecision(
            admitted=True,
            failure_class=None,
            reason="completed",
            evidence_preserved=True,
            temporal_integrity_preserved=True,
        )
    failure_class = OperationalFailureClass.PIT_VIOLATION
    if error_code == "TEMPORAL_LEAKAGE_REJECTED":
        failure_class = OperationalFailureClass.LEAKAGE_REJECTION
    elif error_code == "EVALUATION_CONTAMINATION_REJECTED":
        failure_class = OperationalFailureClass.CONTAMINATION_REJECTION
    elif error_code and "PERSIST" in error_code:
        failure_class = OperationalFailureClass.PERSISTENCE_FAILURE
    elif error_code and "REPLAY" in error_code:
        failure_class = OperationalFailureClass.REPLAY_FAILURE

    evidence_preserved = bool(preserved_evidence_ids) or preserved_event_id is not None
    if failure_class == OperationalFailureClass.EVIDENCE_LOSS:
        evidence_preserved = False

    return FailClosedDecision(
        admitted=False,
        failure_class=failure_class,
        reason=error_code or "fail_closed",
        evidence_preserved=evidence_preserved if FAIL_CLOSED_ON_UNCERTAINTY else False,
        temporal_integrity_preserved=failure_class != OperationalFailureClass.PIT_VIOLATION,
    )


def create_recovery_checkpoint(
    *,
    checkpoint_id: str,
    run_id: str,
    preserved_event_id: str | None,
    preserved_evidence_ids: Sequence[str],
    failure_class: OperationalFailureClass | None = None,
    recovered: bool = False,
) -> RecoveryCheckpoint:
    return RecoveryCheckpoint(
        checkpoint_id=checkpoint_id,
        run_id=run_id,
        preserved_event_id=preserved_event_id,
        preserved_evidence_ids=tuple(preserved_evidence_ids),
        failure_class=failure_class,
        recovered=recovered,
        created_at=datetime.now(UTC),
    )


def assess_operational_readiness(
    *,
    observability: Mapping[str, Any] | None = None,
    api_admin_gated: bool = True,
) -> OperationalReadinessReport:
    metrics = temporal_metrics_status()
    metrics_available = isinstance(metrics, dict) and "temporal_spine_runs_total" in metrics
    stages = (observability or {}).get("stages", [])
    observability_present = bool(stages)
    defects: list[str] = []
    if not FAIL_CLOSED_ON_UNCERTAINTY:
        defects.append("fail_closed_disabled")
    if not metrics_available:
        defects.append("metrics_unavailable")
    if not api_admin_gated:
        defects.append("api_not_admin_gated")

    security_controls = {
        "admin_gated_ingest": api_admin_gated,
        "fail_closed_on_uncertainty": FAIL_CLOSED_ON_UNCERTAINTY,
        "leakage_firewall_enforced": True,
        "idempotency_supported": True,
    }
    capacity_signals = {
        "temporal_spine_runs_total": metrics.get("temporal_spine_runs_total", 0),
        "temporal_api_requests_total": metrics.get("temporal_api_requests_total", 0),
        "temporal_spine_latency_ms_total": metrics.get("temporal_spine_latency_ms_total", 0),
    }
    score_components = [
        FAIL_CLOSED_ON_UNCERTAINTY,
        metrics_available,
        api_admin_gated,
        observability_present or metrics_available,
    ]
    score = sum(1 for c in score_components if c) / len(score_components)
    return OperationalReadinessReport(
        fail_closed_enabled=FAIL_CLOSED_ON_UNCERTAINTY,
        metrics_available=metrics_available,
        recovery_supported=True,
        observability_stages_present=observability_present,
        capacity_signals=capacity_signals,
        security_controls=security_controls,
        readiness_score=score,
        defects=tuple(defects),
    )
