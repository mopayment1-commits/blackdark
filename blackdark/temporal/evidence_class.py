"""Canonical Temporal evidence classes and promotion rules (P2)."""

from __future__ import annotations

from enum import Enum


class TemporalEvidenceClass(str, Enum):
    """TEMP-AR-0138 through TEMP-AR-0143."""

    HISTORICAL_BACKTEST = "HISTORICAL_BACKTEST"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    SIMULATED = "SIMULATED"
    FORWARD_SHADOW = "FORWARD_SHADOW"
    VERIFIED_PRODUCTION = "VERIFIED_PRODUCTION"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"


CANONICAL_EVIDENCE_CLASSES: frozenset[str] = frozenset(c.value for c in TemporalEvidenceClass)

# TEMP-AR-0151, 0152, 0153 hard rules
FORBIDDEN_EVIDENCE_CLASS_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (TemporalEvidenceClass.HISTORICAL_REPLAY.value, TemporalEvidenceClass.FORWARD_SHADOW.value),
        (TemporalEvidenceClass.HISTORICAL_BACKTEST.value, TemporalEvidenceClass.FORWARD_SHADOW.value),
        (TemporalEvidenceClass.SIMULATED.value, TemporalEvidenceClass.FORWARD_SHADOW.value),
        (TemporalEvidenceClass.FORWARD_SHADOW.value, TemporalEvidenceClass.VERIFIED_PRODUCTION.value),
        (TemporalEvidenceClass.HISTORICAL_REPLAY.value, TemporalEvidenceClass.VERIFIED_PRODUCTION.value),
        (TemporalEvidenceClass.VERIFIED_PRODUCTION.value, TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value),
        (TemporalEvidenceClass.HISTORICAL_REPLAY.value, TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value),
    }
)


def is_valid_evidence_class(value: str) -> bool:
    return value in CANONICAL_EVIDENCE_CLASSES


def validate_evidence_class_assignment(value: str) -> None:
    if not is_valid_evidence_class(value):
        raise ValueError(f"unknown evidence class: {value}")


def can_promote_evidence_class(from_class: str, to_class: str) -> bool:
    """TEMP-AR-0144: no automatic promotion between evidence classes."""
    if from_class == to_class:
        return True
    return (from_class, to_class) not in FORBIDDEN_EVIDENCE_CLASS_TRANSITIONS


def assert_no_automatic_promotion(from_class: str, to_class: str) -> None:
    """Raise when an unauthorized promotion is attempted."""
    if from_class != to_class and not can_promote_evidence_class(from_class, to_class):
        raise ValueError(
            f"automatic evidence class promotion forbidden: {from_class} -> {to_class}"
        )
