"""BLACKDARK Temporal truth foundation (P0.1)."""

from blackdark.temporal.accessibility import (
    PitAccessibilityDecision,
    evaluate_pit_accessibility,
    extract_available_at_from_row,
    filter_point_in_time,
)
from blackdark.temporal.truth import (
    AVAILABLE_AT_FIELD_ALIASES,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    TimestampProvenanceKind,
    parse_temporal_instant,
)

__all__ = [
    "AVAILABLE_AT_FIELD_ALIASES",
    "PitAccessibilityDecision",
    "TemporalObservation",
    "TemporalSemanticField",
    "TemporalTimestamp",
    "TimestampProvenanceKind",
    "evaluate_pit_accessibility",
    "extract_available_at_from_row",
    "filter_point_in_time",
    "parse_temporal_instant",
]
