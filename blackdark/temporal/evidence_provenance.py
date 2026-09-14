"""Evidence Provenance Ledger — canonical evidence boundary (P2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence
import hashlib
import json

from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    validate_evidence_class_assignment,
)
from blackdark.temporal.outcome_contract import OutcomeContract
from blackdark.temporal.outcome_quality import OutcomeQualityAssessment
from blackdark.temporal.reproducibility_manifest import ReproducibilityManifest
from blackdark.temporal.source_rights import SourceRightsMetadata

EVIDENCE_PROVENANCE_CONTRACT_VERSION = "p2.0.0"
AUTOMATIC_EVIDENCE_PROMOTION = False


@dataclass(frozen=True, slots=True)
class EvidenceInvalidation:
    evidence_id: str
    reason_code: str
    reason: str
    invalidated_at: datetime
    lineage_preserved: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "invalidated_at": self.invalidated_at.isoformat(),
            "lineage_preserved": self.lineage_preserved,
        }


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """TEMP-AR-0145..0150 canonical evidence record."""

    evidence_id: str
    evidence_class: str
    producer: str
    source_provenance: Mapping[str, Any]
    temporal_context: Mapping[str, Any]
    versions: Mapping[str, Any]
    lineage: tuple[str, ...]
    validation_state: str
    quality_state: Mapping[str, Any]
    limitations: tuple[str, ...]
    methodology: str
    timestamps: Mapping[str, Any]
    evaluator_identity: str | None
    invalidation: EvidenceInvalidation | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_class": self.evidence_class,
            "producer": self.producer,
            "source_provenance": dict(self.source_provenance),
            "temporal_context": dict(self.temporal_context),
            "versions": dict(self.versions),
            "lineage": list(self.lineage),
            "validation_state": self.validation_state,
            "quality_state": dict(self.quality_state),
            "limitations": list(self.limitations),
            "methodology": self.methodology,
            "timestamps": dict(self.timestamps),
            "evaluator_identity": self.evaluator_identity,
            "invalidation": self.invalidation.to_metadata() if self.invalidation else None,
            "payload": dict(self.payload),
        }


@dataclass
class EvidenceProvenanceLedger:
    """Append-only evidence provenance ledger — no competing system of record."""

    _records: list[EvidenceRecord]

    def __init__(self, records: Sequence[EvidenceRecord] | None = None) -> None:
        self._records = list(records or [])

    def list_records(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records)

    def get_record(self, evidence_id: str) -> EvidenceRecord | None:
        for record in self._records:
            if record.evidence_id == evidence_id:
                return record
        return None

    def record_evidence(
        self,
        *,
        evidence_class: str,
        producer: str,
        source_provenance: Mapping[str, Any],
        temporal_context: Mapping[str, Any],
        versions: Mapping[str, Any],
        lineage: Sequence[str],
        quality_state: Mapping[str, Any],
        limitations: Sequence[str],
        methodology: str,
        timestamps: Mapping[str, Any],
        evaluator_identity: str | None,
        payload: Mapping[str, Any],
        validation_state: str = "recorded",
    ) -> EvidenceRecord:
        validate_evidence_class_assignment(evidence_class)
        evidence_key = hashlib.sha256(
            json.dumps(
                {
                    "evidence_class": evidence_class,
                    "producer": producer,
                    "lineage": list(lineage),
                    "timestamps": dict(timestamps),
                },
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()[:16]
        record = EvidenceRecord(
            evidence_id=f"evidence_{evidence_key}",
            evidence_class=evidence_class,
            producer=producer,
            source_provenance=dict(source_provenance),
            temporal_context=dict(temporal_context),
            versions=dict(versions),
            lineage=tuple(lineage),
            validation_state=validation_state,
            quality_state=dict(quality_state),
            limitations=tuple(limitations),
            methodology=methodology,
            timestamps=dict(timestamps),
            evaluator_identity=evaluator_identity,
            payload=dict(payload),
        )
        self._records.append(record)
        return record

    def invalidate_evidence(
        self,
        evidence_id: str,
        *,
        reason_code: str,
        reason: str,
        invalidated_at: datetime,
    ) -> EvidenceRecord:
        existing = self.get_record(evidence_id)
        if existing is None:
            raise ValueError(f"evidence not found: {evidence_id}")
        invalidation = EvidenceInvalidation(
            evidence_id=evidence_id,
            reason_code=reason_code,
            reason=reason,
            invalidated_at=invalidated_at,
        )
        updated = EvidenceRecord(
            evidence_id=existing.evidence_id,
            evidence_class=existing.evidence_class,
            producer=existing.producer,
            source_provenance=existing.source_provenance,
            temporal_context=existing.temporal_context,
            versions=existing.versions,
            lineage=existing.lineage,
            validation_state="invalidated",
            quality_state=existing.quality_state,
            limitations=existing.limitations + (reason_code,),
            methodology=existing.methodology,
            timestamps=existing.timestamps,
            evaluator_identity=existing.evaluator_identity,
            invalidation=invalidation,
            payload=existing.payload,
        )
        self._records.append(updated)
        return updated

    def attempt_promotion(self, evidence_id: str, to_class: str) -> None:
        """TEMP-AR-0144: promotion attempts fail closed."""
        existing = self.get_record(evidence_id)
        if existing is None:
            raise ValueError(f"evidence not found: {evidence_id}")
        assert_no_automatic_promotion(existing.evidence_class, to_class)
        raise ValueError(
            f"automatic evidence promotion forbidden: {existing.evidence_class} -> {to_class}"
        )


def build_evidence_from_outcome_pipeline(
    *,
    outcome: OutcomeContract,
    quality: OutcomeQualityAssessment,
    reproducibility: ReproducibilityManifest,
    source_rights: SourceRightsMetadata | None,
    evidence_class: str = TemporalEvidenceClass.HISTORICAL_REPLAY.value,
) -> EvidenceRecord:
    """Trace: source → temporal → replay/decision → outcome/validation → evidence."""
    validate_evidence_class_assignment(evidence_class)
    ledger = EvidenceProvenanceLedger()
    return ledger.record_evidence(
        evidence_class=evidence_class,
        producer="temporal_p2_pipeline",
        source_provenance=source_rights.to_metadata() if source_rights else {},
        temporal_context=dict(outcome.evaluation_context),
        versions={
            "evaluator_version": outcome.evaluator_version,
            "model_version": reproducibility.model_version,
            "feature_version": reproducibility.feature_version,
        },
        lineage=(outcome.outcome_id, reproducibility.run_id),
        quality_state=quality.to_metadata(),
        limitations=quality.known_limitations,
        methodology="independent_outcome_evaluator",
        timestamps={
            "outcome_timestamp": (
                outcome.outcome_timestamp.isoformat() if outcome.outcome_timestamp else None
            ),
            "replay_timestamps": reproducibility.timestamps,
        },
        evaluator_identity=outcome.evaluator_version,
        payload={
            "outcome": outcome.to_metadata(),
            "reproducibility": reproducibility.to_metadata(),
        },
    )
