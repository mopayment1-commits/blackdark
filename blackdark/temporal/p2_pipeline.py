"""P2 orchestration: decision path → outcome → quality → evidence provenance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from blackdark.temporal.decision_path import DecisionPathReplayResult
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import (
    EvidenceProvenanceLedger,
    EvidenceRecord,
    build_evidence_from_outcome_pipeline,
)
from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.outcome_factory import (
    OutcomeFactoryResult,
    generate_outcomes_from_decision_step,
    predictor_must_not_self_validate,
)
from blackdark.temporal.outcome_quality import OutcomeQualityAssessment, assess_outcome_quality
from blackdark.temporal.replay import ReplayResult
from blackdark.temporal.reproducibility_manifest import (
    ReproducibilityManifest,
    build_reproducibility_manifest,
)
from blackdark.temporal.retention_policy import build_retention_descriptor, classify_storage_tier
from blackdark.temporal.source_quality import assess_source_quality
from blackdark.temporal.source_rights import extract_source_rights


@dataclass(frozen=True, slots=True)
class P2PipelineResult:
    outcome_factory: OutcomeFactoryResult
    quality_assessments: tuple[OutcomeQualityAssessment, ...]
    reproducibility: ReproducibilityManifest
    evidence_records: tuple[EvidenceRecord, ...]
    evidence_class: str
    predictor_self_validation: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "outcome_factory": self.outcome_factory.to_metadata(),
            "quality_assessments": [q.to_metadata() for q in self.quality_assessments],
            "reproducibility": self.reproducibility.to_metadata(),
            "evidence_records": [e.to_metadata() for e in self.evidence_records],
            "evidence_class": self.evidence_class,
            "predictor_self_validation": self.predictor_self_validation,
        }


def run_p2_outcome_evidence_pipeline(
    *,
    event_source: TemporalCanonicalEventStore,
    mass_replay: ReplayResult,
    decision_path: DecisionPathReplayResult,
    ledger: EvidenceProvenanceLedger | None = None,
) -> P2PipelineResult:
    """Execute full P2 pipeline reusing P0/P1 foundations."""
    reproducibility = build_reproducibility_manifest(
        mass_replay,
        model_version=decision_path.model_identity,
        evaluator_version="independent_outcome_evaluator_v1",
    )
    source_events = event_source.list_events()
    source_quality = assess_source_quality(source_events)
    all_outcomes: list = []
    all_quality: list[OutcomeQualityAssessment] = []
    evidence_records: list[EvidenceRecord] = []
    active_ledger = ledger or EvidenceProvenanceLedger()

    for step_result, replay_step in zip(decision_path.steps, mass_replay.replay_outputs):
        factory_result = generate_outcomes_from_decision_step(
            step=replay_step,
            event_source=event_source,
            stages=step_result.stages,
            parameters=decision_path.parameters,
            model_identity=decision_path.model_identity,
        )
        all_outcomes.extend(factory_result.outcomes)

        for outcome in factory_result.outcomes:
            quality = assess_outcome_quality(
                outcome,
                source_quality_score=source_quality.completeness,
            )
            all_quality.append(quality)
            rights = None
            for event in source_events:
                if event.entity_key == outcome.subject_identity:
                    rights = extract_source_rights(event.provenance)
                    break
            tier = classify_storage_tier(access_frequency="frequent_replay")
            retention = build_retention_descriptor(tier, rights_metadata=rights.to_metadata() if rights else {})
            record = build_evidence_from_outcome_pipeline(
                outcome=outcome,
                quality=quality,
                reproducibility=reproducibility,
                source_rights=rights,
                evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
            )
            active_ledger.record_evidence(
                evidence_class=record.evidence_class,
                producer=record.producer,
                source_provenance={**record.source_provenance, "retention": retention.to_metadata()},
                temporal_context=record.temporal_context,
                versions=record.versions,
                lineage=record.lineage,
                quality_state=record.quality_state,
                limitations=record.limitations,
                methodology=record.methodology,
                timestamps=record.timestamps,
                evaluator_identity=record.evaluator_identity,
                payload=record.payload,
            )
            evidence_records.append(active_ledger.list_records()[-1])

    predictor_ok = predictor_must_not_self_validate(
        decision_path.model_identity,
        "independent_outcome_evaluator_v1",
    )

    return P2PipelineResult(
        outcome_factory=OutcomeFactoryResult(outcomes=tuple(all_outcomes), evaluator_identity="independent_outcome_evaluator_v1"),
        quality_assessments=tuple(all_quality),
        reproducibility=reproducibility,
        evidence_records=tuple(evidence_records),
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        predictor_self_validation=not predictor_ok,
    )
