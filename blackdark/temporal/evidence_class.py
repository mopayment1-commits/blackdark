"""TEAS temporal evidence class facade — rules delegated to blackdark.evidence_taxonomy."""

from __future__ import annotations

from blackdark.evidence_taxonomy import (
    CANONICAL_TEMPORAL_EVIDENCE_CLASSES,
    FORBIDDEN_TEMPORAL_EVIDENCE_CLASS_TRANSITIONS,
    TemporalEvidenceClass,
    assert_governed_cross_domain_promotion,
    assert_no_automatic_temporal_promotion,
    can_promote_temporal_evidence_class,
    map_cap646_to_temporal,
    map_temporal_to_cap646,
    validate_temporal_evidence_class,
)

CANONICAL_EVIDENCE_CLASSES = CANONICAL_TEMPORAL_EVIDENCE_CLASSES
FORBIDDEN_EVIDENCE_CLASS_TRANSITIONS = FORBIDDEN_TEMPORAL_EVIDENCE_CLASS_TRANSITIONS


def is_valid_evidence_class(value: str) -> bool:
    return value in CANONICAL_EVIDENCE_CLASSES


def validate_evidence_class_assignment(value: str) -> None:
    validate_temporal_evidence_class(value)


def can_promote_evidence_class(from_class: str, to_class: str) -> bool:
    return can_promote_temporal_evidence_class(from_class, to_class)


def assert_no_automatic_promotion(from_class: str, to_class: str) -> None:
    assert_no_automatic_temporal_promotion(from_class, to_class)


def to_cap646_evidence_class(value: str) -> str:
    return map_temporal_to_cap646(value)


def from_cap646_evidence_class(value: str, *, replay_hint: bool = False) -> str:
    return map_cap646_to_temporal(value, replay_hint=replay_hint)


__all__ = [
    "CANONICAL_EVIDENCE_CLASSES",
    "FORBIDDEN_EVIDENCE_CLASS_TRANSITIONS",
    "TemporalEvidenceClass",
    "assert_governed_cross_domain_promotion",
    "assert_no_automatic_promotion",
    "can_promote_evidence_class",
    "from_cap646_evidence_class",
    "is_valid_evidence_class",
    "to_cap646_evidence_class",
    "validate_evidence_class_assignment",
]
