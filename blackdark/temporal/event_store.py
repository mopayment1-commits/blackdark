"""Canonical Temporal Historical/Event Store boundary (P1.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
from uuid import uuid4

from blackdark.temporal.event_contract import (
    CanonicalTemporalEvent,
    ProvenanceMetadata,
    TemporalEventQuery,
    deterministic_event_sort_key,
)
from blackdark.temporal.truth import parse_temporal_instant


class TemporalEventStoreError(ValueError):
    """Canonical event store contract violation."""


@dataclass
class TemporalCanonicalEventStore:
    """
    Append-only canonical Temporal historical/event store.

    Preserves all historical versions without destructive overwrite. Storage does not
    imply Temporal admissibility; P0 firewall/reconstruction must still be applied.
    """

    _events: list[CanonicalTemporalEvent]

    def __init__(self, events: Sequence[CanonicalTemporalEvent] | None = None) -> None:
        self._events = list(events or [])

    @property
    def event_count(self) -> int:
        return len(self._events)

    def list_events(self) -> tuple[CanonicalTemporalEvent, ...]:
        return tuple(self._events)

    def get_event(self, event_id: str) -> CanonicalTemporalEvent | None:
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None

    def append_event(self, event: CanonicalTemporalEvent) -> CanonicalTemporalEvent:
        if self.get_event(event.event_id) is not None:
            raise TemporalEventStoreError(f"event_id already exists: {event.event_id}")
        self._events.append(event)
        return event

    def append_revision(
        self,
        event: CanonicalTemporalEvent,
        *,
        prior_event_id: str,
    ) -> CanonicalTemporalEvent:
        prior = self.get_event(prior_event_id)
        if prior is None:
            raise TemporalEventStoreError(f"prior event not found: {prior_event_id}")
        if event.correction_or_revision_reference not in (None, prior_event_id):
            raise TemporalEventStoreError("revision lineage reference must match prior_event_id when supplied")
        revision = CanonicalTemporalEvent(
            event_id=event.event_id,
            entity_key=event.entity_key,
            event_type=event.event_type,
            payload=event.payload,
            observation=event.observation,
            provenance=event.provenance,
            record_version=event.record_version,
            correction_or_revision_reference=prior_event_id,
            conflict_metadata=event.conflict_metadata,
        )
        return self.append_event(revision)

    def append_conflicting_event(
        self,
        event: CanonicalTemporalEvent,
        *,
        conflict_metadata: dict[str, Any],
    ) -> CanonicalTemporalEvent:
        if not conflict_metadata:
            raise TemporalEventStoreError("conflict_metadata required for conflicting source records")
        conflict_event = CanonicalTemporalEvent(
            event_id=event.event_id,
            entity_key=event.entity_key,
            event_type=event.event_type,
            payload=event.payload,
            observation=event.observation,
            provenance=event.provenance,
            record_version=event.record_version,
            correction_or_revision_reference=event.correction_or_revision_reference,
            conflict_metadata=conflict_metadata,
        )
        return self.append_event(conflict_event)

    def retrieve(self, query: TemporalEventQuery) -> tuple[CanonicalTemporalEvent, ...]:
        matches: list[CanonicalTemporalEvent] = []
        for event in self._events:
            if query.entity_key is not None and event.entity_key != query.entity_key:
                continue
            if query.event_type is not None and event.event_type != query.event_type:
                continue
            if query.source is not None and event.provenance.source != query.source:
                continue
            if query.record_version is not None and str(event.record_version) != str(query.record_version):
                continue
            if (
                query.correction_or_revision_reference is not None
                and event.correction_or_revision_reference != query.correction_or_revision_reference
            ):
                continue
            if query.available_at_upper is not None:
                available_at = event.observation.available_at
                if not available_at.is_known() or available_at.value is None:
                    continue
                if available_at.value > parse_temporal_instant(query.available_at_upper):
                    continue
            if query.event_time_upper is not None:
                event_time = event.observation.event_time
                if not event_time.is_known() or event_time.value is None:
                    continue
                if event_time.value > parse_temporal_instant(query.event_time_upper):
                    continue
            matches.append(event)
        matches.sort(key=deterministic_event_sort_key)
        return tuple(matches)

    def retrieve_lineage(self, event_id: str) -> tuple[CanonicalTemporalEvent, ...]:
        chain: list[CanonicalTemporalEvent] = []
        current = self.get_event(event_id)
        if current is None:
            return ()
        chain.append(current)
        while current.correction_or_revision_reference:
            parent = self.get_event(current.correction_or_revision_reference)
            if parent is None:
                break
            chain.append(parent)
            current = parent
        chain.reverse()
        return tuple(chain)


def new_event_id(prefix: str = "evt") -> str:
    return f"{prefix}_{uuid4().hex[:16]}"
