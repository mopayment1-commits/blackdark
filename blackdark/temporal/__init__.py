"""BLACKDARK Temporal truth foundation (P0–P1) and Outcome/Evidence foundation (P2)."""

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
from blackdark.temporal.evidence_class import (
    CANONICAL_EVIDENCE_CLASSES,
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    can_promote_evidence_class,
)
from blackdark.temporal.evidence_provenance import (
    EvidenceInvalidation,
    EvidenceProvenanceLedger,
    EvidenceRecord,
    build_evidence_from_outcome_pipeline,
)
from blackdark.temporal.outcome_contract import (
    OUTCOME_EVALUATOR_IDENTITY,
    OutcomeContract,
    OutcomeLabelStatus,
)
from blackdark.temporal.outcome_factory import (
    OutcomeFactoryResult,
    generate_outcomes_from_decision_step,
    predictor_must_not_self_validate,
)
from blackdark.temporal.outcome_quality import (
    OutcomeQualityAssessment,
    OutcomeQualityTier,
    assess_outcome_quality,
)
from blackdark.temporal.p2_pipeline import P2PipelineResult, run_p2_outcome_evidence_pipeline
from blackdark.temporal.p2_requirement_registry import (
    P2_ATOMIC_REQUIREMENT_IDS,
    P2_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
)
from blackdark.temporal.reproducibility_manifest import (
    ReproducibilityManifest,
    build_reproducibility_manifest,
)
from blackdark.temporal.retention_policy import StorageTier, build_retention_descriptor, classify_storage_tier
from blackdark.temporal.source_quality import SourceQualityEvidence, assess_source_quality
from blackdark.temporal.source_rights import SourceRightsMetadata, extract_source_rights
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
    "CANONICAL_EVIDENCE_CLASSES",
    "CanonicalTemporalEvent",
    "DECISION_PATH_STAGES",
    "DecisionPathReplayResult",
    "DecisionPathStepResult",
    "EvidenceInvalidation",
    "EvidenceProvenanceLedger",
    "EvidenceRecord",
    "HISTORICAL_REPLAY",
    "MultiScenarioReplayResult",
    "OUTCOME_EVALUATOR_IDENTITY",
    "OutcomeContract",
    "OutcomeFactoryResult",
    "OutcomeLabelStatus",
    "OutcomeQualityAssessment",
    "OutcomeQualityTier",
    "P2PipelineResult",
    "P2_ATOMIC_REQUIREMENT_IDS",
    "P2_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS",
    "P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS",
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
    "ReproducibilityManifest",
    "SourceQualityEvidence",
    "SourceRightsMetadata",
    "StorageTier",
    "TemporalCanonicalEventStore",
    "TemporalEvidenceClass",
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
    "assert_no_automatic_promotion",
    "assess_outcome_quality",
    "assess_source_quality",
    "build_evidence_from_outcome_pipeline",
    "build_reproducibility_manifest",
    "build_retention_descriptor",
    "can_promote_evidence_class",
    "classify_storage_tier",
    "compare_replay_runs",
    "compute_determinism_fingerprint",
    "extract_source_rights",
    "generate_outcomes_from_decision_step",
    "predictor_must_not_self_validate",
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
    "run_p2_outcome_evidence_pipeline",
]
