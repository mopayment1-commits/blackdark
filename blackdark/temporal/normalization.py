"""Normalize live/ingested input into canonical temporal events."""

from __future__ import annotations

from typing import Any, Mapping

from blackdark.temporal.event_contract import CanonicalTemporalEvent, ProvenanceMetadata
from blackdark.temporal.event_store import new_event_id
from blackdark.temporal.pit_contract import validate_ingestion_payload, validate_pit_contract
from blackdark.temporal.serialization import observation_from_dict, provenance_from_dict
from blackdark.temporal.truth import TemporalSemanticField, TemporalTimestamp


def normalize_ingestion_to_canonical_event(
    payload: Mapping[str, Any],
    *,
    strict: bool = True,
) -> CanonicalTemporalEvent:
    validate_ingestion_payload(payload, strict=strict)
    observation = observation_from_dict(payload["observation"])
    provenance = provenance_from_dict(payload["provenance"])
    validate_pit_contract(observation=observation, provenance=provenance, strict=strict)
    return CanonicalTemporalEvent(
        event_id=str(payload.get("event_id") or new_event_id()),
        entity_key=str(payload["entity_key"]),
        event_type=str(payload["event_type"]),
        payload=dict(payload.get("payload") or {}),
        observation=observation,
        provenance=provenance,
        record_version=payload.get("record_version", "1"),
        correction_or_revision_reference=payload.get("correction_or_revision_reference"),
        conflict_metadata=payload.get("conflict_metadata"),
    )


def build_observation_dict(
    *,
    event_time: str,
    observed_time: str,
    available_at: str,
    ingested_at: str,
    effective_at: str,
    revised_at: str,
) -> dict[str, Any]:
    def _direct(field: TemporalSemanticField, value: str) -> dict[str, Any]:
        return TemporalTimestamp.direct(field, value).to_metadata()

    return {
        "event_time": _direct(TemporalSemanticField.EVENT_TIME, event_time),
        "observed_time": _direct(TemporalSemanticField.OBSERVED_TIME, observed_time),
        "available_at": _direct(TemporalSemanticField.AVAILABLE_AT, available_at),
        "ingested_at": _direct(TemporalSemanticField.INGESTED_AT, ingested_at),
        "effective_at": _direct(TemporalSemanticField.EFFECTIVE_AT, effective_at),
        "revised_at": _direct(TemporalSemanticField.REVISED_AT, revised_at),
    }


def build_provenance_dict(
    *,
    source: str,
    source_version: str,
    dataset_version: str,
    rights_or_provenance: Mapping[str, Any],
    provenance_reference: str | None = None,
) -> dict[str, Any]:
    return ProvenanceMetadata(
        source=source,
        source_version=source_version,
        dataset_version=dataset_version,
        rights_or_provenance=dict(rights_or_provenance),
        provenance_reference=provenance_reference,
    ).to_metadata()
