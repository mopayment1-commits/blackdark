"""Temporal Leakage Firewall — blocks future information in historical/replay contexts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from cap646.evidence_class import EvidenceClass, assert_promotion_allowed, infer_evidence_class


class TemporalLeakageError(ValueError):
    """Raised when event_time exceeds evaluation cutoff (lookahead)."""


def _parse_ts(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def assert_no_temporal_leakage(
    *,
    event_time: str | float | int | None,
    evaluation_cutoff: str | float | int | None,
    context: str = "replay",
) -> None:
    """Reject records whose event_time is after the evaluation cutoff."""
    ev = _parse_ts(event_time)
    cutoff = _parse_ts(evaluation_cutoff)
    if ev is None or cutoff is None:
        return
    if ev > cutoff:
        raise TemporalLeakageError(
            f"temporal_leakage:{context}:event_time>{evaluation_cutoff}"
        )


def filter_point_in_time(
    rows: list[dict[str, Any]],
    *,
    cutoff: str | float | int,
    time_field: str = "event_time",
) -> list[dict[str, Any]]:
    """Return rows observable at cutoff (event_time <= cutoff)."""
    cutoff_ts = _parse_ts(cutoff)
    if cutoff_ts is None:
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        ts = _parse_ts(row.get(time_field) or row.get("observed_time"))
        if ts is None or ts <= cutoff_ts:
            out.append(row)
    return out


def guard_evidence_class_promotion(
    *,
    current: EvidenceClass,
    target: EvidenceClass,
    has_independent_verification: bool = False,
) -> dict[str, Any]:
    """Enforce evidence-class firewall; independent verification required for production."""
    if target == "PRODUCTION_VERIFIED" and not has_independent_verification:
        return {
            "allowed": False,
            "reason": "independent_verification_required",
            "current": current,
            "target": target,
        }
    try:
        assert_promotion_allowed(current, target)
        return {"allowed": True, "current": current, "target": target}
    except ValueError as exc:
        return {"allowed": False, "reason": str(exc), "current": current, "target": target}


def leakage_firewall_report(*, source: str | None = None) -> dict[str, Any]:
    cls = infer_evidence_class(source=source)
    return {
        "module": "temporal_leakage_firewall",
        "status": "ACTIVE_LOCAL",
        "evidence_class": cls,
        "invariants": [
            "HISTORICAL_BACKTEST != HISTORICAL_REPLAY != SIMULATED != FORWARD_SHADOW != VERIFIED_PRODUCTION",
            "EXPERIENCE_COMPRESSION != TIME_FABRATION",
        ],
        "checked_at": datetime.now(UTC).isoformat(),
    }
