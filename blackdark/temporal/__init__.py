"""BLACKDARK Temporal truth foundation (P0.1) and PIT reconstruction boundary (P0.2)."""

from blackdark.temporal.accessibility import (
    PitAccessibilityDecision,
    evaluate_pit_accessibility,
    extract_available_at_from_row,
    filter_point_in_time,
)
from blackdark.temporal.firewall import (
    LeakageClass,
    TemporalLeakageFirewallDecision,
    TemporalLeakageRejection,
    TemporalProcessingContext,
    evaluate_temporal_leakage_firewall,
)
from blackdark.temporal.reconstruction import (
    PitReconstructionExclusion,
    PitReconstructionResult,
    TemporalRecord,
    reconstruct_point_in_time,
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
    "LeakageClass",
    "PitAccessibilityDecision",
    "PitReconstructionExclusion",
    "PitReconstructionResult",
    "TemporalLeakageFirewallDecision",
    "TemporalLeakageRejection",
    "TemporalObservation",
    "TemporalProcessingContext",
    "TemporalRecord",
    "TemporalSemanticField",
    "TemporalTimestamp",
    "TimestampProvenanceKind",
    "evaluate_pit_accessibility",
    "evaluate_temporal_leakage_firewall",
    "extract_available_at_from_row",
    "filter_point_in_time",
    "parse_temporal_instant",
    "reconstruct_point_in_time",
]
