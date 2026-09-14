"""Serialize/deserialize temporal domain objects for Postgres persistence."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping

from blackdark.temporal.event_contract import CanonicalTemporalEvent, ProvenanceMetadata
from blackdark.temporal.evidence_provenance import EvidenceRecord
from blackdark.temporal.forward_shadow import ForwardShadowReceipt
from blackdark.temporal.truth import (
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    TimestampProvenanceKind,
    parse_temporal_instant,
)


def _ts_to_dict(ts: TemporalTimestamp) -> dict[str, Any]:
    return ts.to_metadata()


def _ts_from_dict(data: Mapping[str, Any]) -> TemporalTimestamp:
    field = TemporalSemanticField(data["field"])
    provenance = TimestampProvenanceKind(data["provenance"])
    value = data.get("value")
    parsed = parse_temporal_instant(value) if value else None
    basis = data.get("derivation_basis")
    if provenance == TimestampProvenanceKind.UNKNOWN:
        return TemporalTimestamp.unknown(field)
    if provenance == TimestampProvenanceKind.DIRECT:
        assert parsed is not None
        return TemporalTimestamp.direct(field, parsed)
    assert parsed is not None and basis
    return TemporalTimestamp.derived(field, parsed, derivation_basis=basis)


def observation_to_dict(observation: TemporalObservation) -> dict[str, Any]:
    return observation.to_metadata()


def observation_from_dict(data: Mapping[str, Any]) -> TemporalObservation:
    return TemporalObservation.create(
        event_time=_ts_from_dict(data["event_time"]),
        observed_time=_ts_from_dict(data["observed_time"]),
        available_at=_ts_from_dict(data["available_at"]),
        ingested_at=_ts_from_dict(data["ingested_at"]),
        effective_at=_ts_from_dict(data["effective_at"]),
        revised_at=_ts_from_dict(data["revised_at"]),
    )


def provenance_to_dict(provenance: ProvenanceMetadata) -> dict[str, Any]:
    return provenance.to_metadata()


def provenance_from_dict(data: Mapping[str, Any]) -> ProvenanceMetadata:
    rights = data.get("rights_or_provenance")
    return ProvenanceMetadata(
        source=data.get("source"),
        source_version=data.get("source_version"),
        dataset_version=data.get("dataset_version"),
        rights_or_provenance=dict(rights) if rights else None,
        provenance_reference=data.get("provenance_reference"),
        retention_policy_reference=data.get("retention_policy_reference"),
    )


def canonical_event_to_row(event: CanonicalTemporalEvent, *, idempotency_key: str | None = None) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "entity_key": event.entity_key,
        "event_type": event.event_type,
        "payload": json.dumps(dict(event.payload)),
        "observation": json.dumps(observation_to_dict(event.observation)),
        "provenance": json.dumps(provenance_to_dict(event.provenance)),
        "record_version": str(event.record_version),
        "correction_or_revision_reference": event.correction_or_revision_reference,
        "conflict_metadata": json.dumps(dict(event.conflict_metadata)) if event.conflict_metadata else None,
        "idempotency_key": idempotency_key,
    }


def canonical_event_from_row(row: Mapping[str, Any]) -> CanonicalTemporalEvent:
    payload = row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"])
    observation = row["observation"] if isinstance(row["observation"], dict) else json.loads(row["observation"])
    provenance = row["provenance"] if isinstance(row["provenance"], dict) else json.loads(row["provenance"])
    conflict = row.get("conflict_metadata")
    if conflict is not None and not isinstance(conflict, dict):
        conflict = json.loads(conflict)
    return CanonicalTemporalEvent(
        event_id=row["event_id"],
        entity_key=row["entity_key"],
        event_type=row["event_type"],
        payload=payload,
        observation=observation_from_dict(observation),
        provenance=provenance_from_dict(provenance),
        record_version=row["record_version"],
        correction_or_revision_reference=row.get("correction_or_revision_reference"),
        conflict_metadata=conflict,
    )


def evidence_record_to_row(
    record: EvidenceRecord,
    *,
    source_table: str | None = None,
    source_record_id: str | None = None,
) -> dict[str, Any]:
    payload = record.to_metadata()
    return {
        "evidence_id": record.evidence_id,
        "evidence_class": record.evidence_class,
        "producer": record.producer,
        "record_payload": json.dumps(payload),
        "payload_hash": _hash_payload(payload),
        "source_table": source_table,
        "source_record_id": source_record_id,
    }


def evidence_record_from_row(row: Mapping[str, Any]) -> EvidenceRecord:
    payload = row["record_payload"] if isinstance(row["record_payload"], dict) else json.loads(row["record_payload"])
    from blackdark.temporal.evidence_provenance import EvidenceInvalidation

    invalidation = payload.get("invalidation")
    inv_obj = None
    if invalidation:
        inv_obj = EvidenceInvalidation(
            evidence_id=invalidation["evidence_id"],
            reason_code=invalidation["reason_code"],
            reason=invalidation["reason"],
            invalidated_at=parse_temporal_instant(invalidation["invalidated_at"]),
            lineage_preserved=invalidation.get("lineage_preserved", True),
        )
    return EvidenceRecord(
        evidence_id=payload["evidence_id"],
        evidence_class=payload["evidence_class"],
        producer=payload["producer"],
        source_provenance=payload["source_provenance"],
        temporal_context=payload["temporal_context"],
        versions=payload["versions"],
        lineage=tuple(payload["lineage"]),
        validation_state=payload["validation_state"],
        quality_state=payload["quality_state"],
        limitations=tuple(payload["limitations"]),
        methodology=payload["methodology"],
        timestamps=payload["timestamps"],
        evaluator_identity=payload.get("evaluator_identity"),
        invalidation=inv_obj,
        payload=payload.get("payload", {}),
    )


def forward_shadow_receipt_to_row(receipt: ForwardShadowReceipt, *, idempotency_key: str | None = None) -> dict[str, Any]:
    payload = receipt.to_metadata()
    return {
        "receipt_id": receipt.shadow_receipt_id,
        "prediction_id": receipt.prediction_id,
        "subject_identity": receipt.subject_identity,
        "receipt_payload": json.dumps(payload),
        "payload_hash": _hash_payload(payload),
        "evidence_class": receipt.evidence_class,
        "issued_at": receipt.issued_at,
        "idempotency_key": idempotency_key,
    }


def forward_shadow_receipt_from_row(row: Mapping[str, Any]) -> ForwardShadowReceipt:
    payload = row["receipt_payload"] if isinstance(row["receipt_payload"], dict) else json.loads(row["receipt_payload"])
    return ForwardShadowReceipt(
        shadow_receipt_id=payload["shadow_receipt_id"],
        created_at_or_receipt_time=parse_temporal_instant(payload["created_at_or_receipt_time"]),
        subject_identity=payload["subject_identity"],
        input_identity=payload["input_identity"],
        decision_or_prediction_identity=payload["decision_or_prediction_identity"],
        model_or_engine_version=payload["model_or_engine_version"],
        parameters=payload.get("parameters", {}),
        temporal_context=payload.get("temporal_context", {}),
        source_or_dataset_context=payload.get("source_or_dataset_context", {}),
        pre_outcome_payload=payload.get("pre_outcome_payload", {}),
        evidence_class=payload["evidence_class"],
        provenance_reference=payload["provenance_reference"],
        status=payload["status"],
        prediction_id=payload["prediction_id"],
        issued_at=parse_temporal_instant(payload["issued_at"]),
        model_version=payload["model_version"],
        rule_config_version=payload["rule_config_version"],
        dataset_version=payload["dataset_version"],
        code_version=payload["code_version"],
        input_snapshot_hash=payload["input_snapshot_hash"],
        prediction=payload["prediction"],
        confidence=payload.get("confidence"),
        abstention_state=payload["abstention_state"],
        outcome_known_at=parse_temporal_instant(payload["outcome_known_at"]) if payload.get("outcome_known_at") else None,
        linked_outcome_id=payload.get("linked_outcome_id"),
    )


def _hash_payload(payload: Mapping[str, Any]) -> str:
    import hashlib

    normalized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()
