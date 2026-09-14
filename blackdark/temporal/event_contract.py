"""Canonical Temporal historical/event record contract (P1.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from blackdark.temporal.reconstruction import TemporalRecord
from blackdark.temporal.truth import TemporalObservation, TemporalSemanticField, TemporalTimestamp


@dataclass(frozen=True, slots=True)
class ProvenanceMetadata:
    """Upstream DG-supplied provenance/rights metadata (copied, not reinterpreted)."""

    source: str | None = None
    source_version: str | None = None
    dataset_version: str | None = None
    rights_or_provenance: Mapping[str, Any] | None = None
    provenance_reference: str | None = None
    retention_policy_reference: str | None = None

    def field_known(self, name: str) -> bool:
        value = getattr(self, name)
        if name == "rights_or_provenance":
            return value is not None
        return value is not None and value != ""

    def to_metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_version": self.source_version,
            "dataset_version": self.dataset_version,
            "rights_or_provenance": dict(self.rights_or_provenance) if self.rights_or_provenance else None,
            "provenance_reference": self.provenance_reference,
            "retention_policy_reference": self.retention_policy_reference,
            "source_known": self.field_known("source"),
            "source_version_known": self.field_known("source_version"),
            "dataset_version_known": self.field_known("dataset_version"),
            "rights_or_provenance_known": self.field_known("rights_or_provenance"),
        }


@dataclass(frozen=True, slots=True)
class CanonicalTemporalEvent:
    """Immutable canonical Temporal event record for historical/event storage."""

    event_id: str
    entity_key: str
    event_type: str
    payload: Mapping[str, Any]
    observation: TemporalObservation
    provenance: ProvenanceMetadata
    record_version: str | int
    correction_or_revision_reference: str | None = None
    conflict_metadata: Mapping[str, Any] | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "entity_key": self.entity_key,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "observation": self.observation.to_metadata(),
            "provenance": self.provenance.to_metadata(),
            "record_version": self.record_version,
            "correction_or_revision_reference": self.correction_or_revision_reference,
            "conflict_metadata": dict(self.conflict_metadata) if self.conflict_metadata else None,
        }

    def to_temporal_record(self) -> TemporalRecord:
        return TemporalRecord(
            record_id=self.event_id,
            entity_key=self.entity_key,
            observation=self.observation,
            payload=dict(self.payload),
            version=self.record_version,
        )


@dataclass(frozen=True, slots=True)
class TemporalEventQuery:
    """Deterministic retrieval query for canonical Temporal events."""

    entity_key: str | None = None
    event_type: str | None = None
    source: str | None = None
    record_version: str | int | None = None
    correction_or_revision_reference: str | None = None
    available_at_upper: datetime | None = None
    event_time_upper: datetime | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "entity_key": self.entity_key,
            "event_type": self.event_type,
            "source": self.source,
            "record_version": self.record_version,
            "correction_or_revision_reference": self.correction_or_revision_reference,
            "available_at_upper": self.available_at_upper.isoformat() if self.available_at_upper else None,
            "event_time_upper": self.event_time_upper.isoformat() if self.event_time_upper else None,
        }


def _sort_instant(timestamp: TemporalTimestamp) -> datetime:
    if timestamp.is_known() and timestamp.value is not None:
        return timestamp.value
    return datetime.min.replace(tzinfo=UTC)


def deterministic_event_sort_key(event: CanonicalTemporalEvent) -> tuple[Any, ...]:
    """Stable ordering for identical store state and query parameters."""
    return (
        _sort_instant(event.observation.available_at),
        _sort_instant(event.observation.event_time),
        str(event.provenance.source or ""),
        str(event.event_type),
        str(event.entity_key),
        str(event.record_version),
        event.event_id,
    )
