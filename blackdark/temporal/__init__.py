"""BLACKDARK Temporal truth foundation (P0–P1), Outcome/Evidence (P2), Shadow/Regime (P3)."""

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
from blackdark.temporal.drift_monitoring import DriftMonitorResult, DriftSignal, evaluate_drift
from blackdark.temporal.failure_surprise_corpus import (
    CaptureCategory,
    FailureSurpriseCase,
    FailureSurpriseCorpus,
    FSB_ATOMIC_IDS,
    FAILURE_SURPRISE_ABSTENTION_TOTAL,
)
from blackdark.temporal.forward_shadow import ForwardShadowLedger, ForwardShadowReceipt
from blackdark.temporal.p2_pipeline import P2PipelineResult, run_p2_outcome_evidence_pipeline
from blackdark.temporal.learning_value import (
    LEARNING_VALUE_DETERMINISTIC,
    RETENTION_EQUALS_LEARNING_PRIORITY,
    LearningStream,
    LearningValueEngine,
    LearningValueResult,
)
from blackdark.temporal.p3_pipeline import P3PipelineResult, run_forward_shadow_pipeline
from blackdark.temporal.p4_learning_value_registry import P4_LEARNING_VALUE_ATOMIC_REQUIREMENT_IDS
from blackdark.temporal.p3_requirement_registry import (
    P3_ATOMIC_REQUIREMENT_IDS,
    P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
)
from blackdark.temporal.regime_intelligence import (
    KnownRegimeLabel,
    RegimeContext,
    RegimeDecomposedEvaluation,
    classify_regime,
    evaluate_by_regime,
)
from blackdark.temporal.reality_anchor import RealityAnchorStatus, evaluate_reality_anchor
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
    "DriftMonitorResult",
    "DriftSignal",
    "CaptureCategory",
    "FailureSurpriseCase",
    "FailureSurpriseCorpus",
    "FSB_ATOMIC_IDS",
    "FAILURE_SURPRISE_ABSTENTION_TOTAL",
    "ForwardShadowLedger",
    "ForwardShadowReceipt",
    "KnownRegimeLabel",
    "LEARNING_VALUE_DETERMINISTIC",
    "LearningStream",
    "LearningValueEngine",
    "LearningValueResult",
    "P2PipelineResult",
    "P4_LEARNING_VALUE_ATOMIC_REQUIREMENT_IDS",
    "RETENTION_EQUALS_LEARNING_PRIORITY",
    "P3PipelineResult",
    "P3_ATOMIC_REQUIREMENT_IDS",
    "P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS",
    "P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS",
    "P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS",
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
    "RealityAnchorStatus",
    "RegimeContext",
    "RegimeDecomposedEvaluation",
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
    "classify_regime",
    "evaluate_by_regime",
    "evaluate_drift",
    "evaluate_reality_anchor",
    "run_forward_shadow_pipeline",
    "run_p2_outcome_evidence_pipeline",
]
