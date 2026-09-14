"""Postgres persistence adapters for production temporal spine."""

from __future__ import annotations

import json
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.data import temporal_repository as repo
from blackdark.temporal.contamination_registry import ContaminationEntry, ContaminationRegistry
from blackdark.temporal.event_contract import CanonicalTemporalEvent, TemporalEventQuery
from blackdark.temporal.event_store import TemporalCanonicalEventStore, TemporalEventStoreError, deterministic_event_sort_key
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger, EvidenceRecord
from blackdark.temporal.forward_shadow import ForwardShadowLedger, ForwardShadowReceipt
from blackdark.temporal.serialization import (
    canonical_event_from_row,
    canonical_event_to_row,
    evidence_record_from_row,
    evidence_record_to_row,
    forward_shadow_receipt_from_row,
    forward_shadow_receipt_to_row,
)
from blackdark.temporal.truth import parse_temporal_instant


class PostgresEventStore(TemporalCanonicalEventStore):
    """Production event store backed by te_canonical_events."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        bootstrap_events: Sequence[CanonicalTemporalEvent] | None = None,
    ) -> None:
        super().__init__(bootstrap_events)
        self._session = session
        self._hydrated = False

    async def hydrate(self) -> None:
        if self._hydrated:
            return
        rows = await repo.query_canonical_events(self._session)
        self._events = [canonical_event_from_row(row) for row in rows]
        self._hydrated = True

    async def persist_append(
        self,
        event: CanonicalTemporalEvent,
        *,
        idempotency_key: str | None = None,
    ) -> CanonicalTemporalEvent:
        await self.hydrate()
        if self.get_event(event.event_id) is not None:
            raise TemporalEventStoreError(f"event_id already exists: {event.event_id}")
        row = canonical_event_to_row(event, idempotency_key=idempotency_key)
        await repo.insert_canonical_event(self._session, row)
        self._events.append(event)
        return event


class PostgresEvidenceLedger(EvidenceProvenanceLedger):
    def __init__(
        self,
        session: AsyncSession,
        *,
        bootstrap: Sequence[EvidenceRecord] | None = None,
        source_table: str | None = None,
        source_record_id: str | None = None,
    ) -> None:
        super().__init__(bootstrap)
        self._session = session
        self._pending_persist: list[EvidenceRecord] = []
        self._source_table = source_table
        self._source_record_id = source_record_id

    def record_evidence(self, **kwargs: Any) -> EvidenceRecord:
        record = super().record_evidence(**kwargs)
        self._pending_persist.append(record)
        return record

    async def flush_records(
        self,
        *,
        source_table: str | None = None,
        source_record_id: str | None = None,
    ) -> list[EvidenceRecord]:
        persisted: list[EvidenceRecord] = []
        table = source_table or self._source_table
        record_id = source_record_id or self._source_record_id
        for record in self._pending_persist:
            row = evidence_record_to_row(
                record,
                source_table=table,
                source_record_id=record_id,
            )
            await repo.insert_evidence_record(self._session, row)
            persisted.append(record)
        self._pending_persist.clear()
        return persisted


class PostgresForwardShadowLedger(ForwardShadowLedger):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self._session = session

    async def persist_receipt(
        self,
        receipt: ForwardShadowReceipt,
        *,
        idempotency_key: str | None = None,
    ) -> ForwardShadowReceipt:
        row = forward_shadow_receipt_to_row(receipt, idempotency_key=idempotency_key)
        await repo.insert_forward_shadow_receipt(self._session, row)
        self._receipts.append(receipt)
        return receipt


class PostgresContaminationRegistry(ContaminationRegistry):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self._session = session
        self._loaded = False

    async def hydrate(self) -> None:
        if self._loaded:
            return
        entries = await repo.load_contamination_entries(self._session)
        self.load_entries(entries)
        self._loaded = True

    async def persist_entry(self, entry: ContaminationEntry) -> str:
        await self.hydrate()
        return await repo.upsert_contamination_entry(self._session, entry)

    async def record_exposure_persisted(self, entry: ContaminationEntry) -> ContaminationEntry:
        await self.hydrate()
        key_entry = super().record_exposure(
            dataset_id=entry.dataset_id,
            window_start=entry.window_start,
            window_end=entry.window_end,
            purpose=entry.usage_purpose,
            model_version=entry.model_version,
            config_version=entry.config_version,
            dataset_version=entry.dataset_version,
            metadata=entry.metadata,
        )
        await repo.upsert_contamination_entry(self._session, key_entry)
        return key_entry
