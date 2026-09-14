"""BLACKDARK Temporal truth foundation (P0.1), PIT reconstruction (P0.2), firewall (P0.3), event store (P1.1), replay (P1.2/P1.3)."""

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
from blackdark.temporal.event_contract import (
    CanonicalTemporalEvent,
    ProvenanceMetadata,
    TemporalEventQuery,
    deterministic_event_sort_key,
)
from blackdark.temporal.event_store import TemporalCanonicalEventStore, TemporalEventStoreError, new_event_id
from blackdark.temporal.decision_path import (
    DECISION_PATH_STAGES,
    DecisionPathReplayResult,
    DecisionPathStepResult,
    execute_historical_decision_path,
)
from blackdark.temporal.replay_coverage import (
    HISTORICAL_REPLAY,
    MultiScenarioReplayResult,
    ReplayComparisonResult,
    ReplayScenarioResult,
    ReplayScenarioSpec,
    compare_replay_runs,
    run_full_decision_path_replay,
    run_multi_scenario_replay,
)
from blackdark.temporal.replay import (
    REPLAY_EVIDENCE_CLASS,
    REPLAY_ENGINE_CONTRACT_VERSION,
    ReplayFailureReason,
    ReplayRequest,
    ReplayRejection,
    ReplayResult,
    ReplayStepOutput,
    compute_determinism_fingerprint,
    run_deterministic_mass_replay,
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
    "CanonicalTemporalEvent",
    "DECISION_PATH_STAGES",
    "DecisionPathReplayResult",
    "DecisionPathStepResult",
    "HISTORICAL_REPLAY",
    "MultiScenarioReplayResult",
    "LeakageClass",
    "PitAccessibilityDecision",
    "PitReconstructionExclusion",
    "PitReconstructionResult",
    "ProvenanceMetadata",
    "REPLAY_ENGINE_CONTRACT_VERSION",
    "REPLAY_EVIDENCE_CLASS",
    "ReplayFailureReason",
    "ReplayRejection",
    "ReplayComparisonResult",
    "ReplayRequest",
    "ReplayResult",
    "ReplayScenarioResult",
    "ReplayScenarioSpec",
    "ReplayStepOutput",
    "TemporalCanonicalEventStore",
    "TemporalEventQuery",
    "TemporalEventStoreError",
    "TemporalLeakageFirewallDecision",
    "TemporalLeakageRejection",
    "TemporalObservation",
    "TemporalProcessingContext",
    "TemporalRecord",
    "TemporalSemanticField",
    "TemporalTimestamp",
    "TimestampProvenanceKind",
    "compare_replay_runs",
    "compute_determinism_fingerprint",
    "deterministic_event_sort_key",
    "execute_historical_decision_path",
    "evaluate_pit_accessibility",
    "evaluate_temporal_leakage_firewall",
    "extract_available_at_from_row",
    "filter_point_in_time",
    "new_event_id",
    "parse_temporal_instant",
    "reconstruct_point_in_time",
    "run_deterministic_mass_replay",
    "run_full_decision_path_replay",
    "run_multi_scenario_replay",
]
