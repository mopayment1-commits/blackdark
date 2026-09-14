"""Postgres repository for TEAS temporal spine tables."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.temporal.contamination_registry import ContaminationEntry, ContaminationPurpose, ContaminationState
from blackdark.temporal.serialization import (
    canonical_event_from_row,
    canonical_event_to_row,
    evidence_record_from_row,
    evidence_record_to_row,
    forward_shadow_receipt_from_row,
    forward_shadow_receipt_to_row,
)
from blackdark.temporal.truth import parse_temporal_instant


async def insert_canonical_event(
    session: AsyncSession,
    row: Mapping[str, Any],
) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_canonical_events (
                event_id, entity_key, event_type, payload, observation, provenance,
                record_version, correction_or_revision_reference, conflict_metadata, idempotency_key
            ) VALUES (
                :event_id, :entity_key, :event_type, CAST(:payload AS jsonb), CAST(:observation AS jsonb),
                CAST(:provenance AS jsonb), :record_version, :correction_or_revision_reference,
                CAST(:conflict_metadata AS jsonb), :idempotency_key
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING event_id
            """
        ),
        dict(row),
    )
    inserted = result.fetchone()
    if inserted:
        return inserted[0]
    if row.get("idempotency_key"):
        existing = await session.execute(
            text("SELECT event_id FROM te_canonical_events WHERE idempotency_key = :key"),
            {"key": row["idempotency_key"]},
        )
        found = existing.fetchone()
        if found:
            return found[0]
    return row["event_id"]


async def get_canonical_event_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> dict[str, Any] | None:
    result = await session.execute(
        text("SELECT * FROM te_canonical_events WHERE idempotency_key = :key"),
        {"key": idempotency_key},
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def get_canonical_event(session: AsyncSession, event_id: str) -> dict[str, Any] | None:
    result = await session.execute(
        text("SELECT * FROM te_canonical_events WHERE event_id = :event_id"),
        {"event_id": event_id},
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def query_canonical_events(
    session: AsyncSession,
    *,
    entity_key: str | None = None,
    event_type: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit}
    if entity_key:
        clauses.append("entity_key = :entity_key")
        params["entity_key"] = entity_key
    if event_type:
        clauses.append("event_type = :event_type")
        params["event_type"] = event_type
    result = await session.execute(
        text(
            f"""
            SELECT * FROM te_canonical_events
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at ASC
            LIMIT :limit
            """
        ),
        params,
    )
    return [dict(r) for r in result.mappings().all()]


async def insert_evidence_record(session: AsyncSession, row: Mapping[str, Any]) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_evidence_records (
                evidence_id, evidence_class, producer, record_payload, payload_hash,
                source_table, source_record_id
            ) VALUES (
                :evidence_id, :evidence_class, :producer, CAST(:record_payload AS jsonb),
                :payload_hash, :source_table, :source_record_id
            )
            ON CONFLICT (evidence_id) DO NOTHING
            RETURNING evidence_id
            """
        ),
        dict(row),
    )
    inserted = result.fetchone()
    return inserted[0] if inserted else row["evidence_id"]


async def get_evidence_record(session: AsyncSession, evidence_id: str) -> dict[str, Any] | None:
    result = await session.execute(
        text("SELECT * FROM te_evidence_records WHERE evidence_id = :evidence_id"),
        {"evidence_id": evidence_id},
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def insert_forward_shadow_receipt(session: AsyncSession, row: Mapping[str, Any]) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_forward_shadow_receipts (
                receipt_id, prediction_id, subject_identity, receipt_payload, payload_hash,
                evidence_class, issued_at, idempotency_key
            ) VALUES (
                :receipt_id, :prediction_id, :subject_identity, CAST(:receipt_payload AS jsonb),
                :payload_hash, :evidence_class, :issued_at, :idempotency_key
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING receipt_id
            """
        ),
        dict(row),
    )
    inserted = result.fetchone()
    if inserted:
        return inserted[0]
    if row.get("idempotency_key"):
        existing = await session.execute(
            text("SELECT receipt_id FROM te_forward_shadow_receipts WHERE idempotency_key = :key"),
            {"key": row["idempotency_key"]},
        )
        found = existing.fetchone()
        if found:
            return found[0]
    return row["receipt_id"]


async def insert_forward_shadow_correction(session: AsyncSession, row: Mapping[str, Any]) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_forward_shadow_corrections (
                correction_id, receipt_id, correction_payload, provenance
            ) VALUES (
                :correction_id, :receipt_id, CAST(:correction_payload AS jsonb), CAST(:provenance AS jsonb)
            )
            RETURNING correction_id
            """
        ),
        dict(row),
    )
    return result.fetchone()[0]


async def upsert_contamination_entry(session: AsyncSession, entry: ContaminationEntry) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_contamination_registry (
                entry_id, dataset_id, window_start, window_end, usage_purpose,
                model_version, config_version, dataset_version, exposure_count,
                contamination_state, metadata
            ) VALUES (
                :entry_id, :dataset_id, :window_start, :window_end, :usage_purpose,
                :model_version, :config_version, :dataset_version, :exposure_count,
                :contamination_state, CAST(:metadata AS jsonb)
            )
            ON CONFLICT (dataset_id, window_start, window_end, usage_purpose, model_version, config_version, dataset_version)
            DO UPDATE SET
                exposure_count = te_contamination_registry.exposure_count + 1,
                contamination_state = EXCLUDED.contamination_state,
                metadata = te_contamination_registry.metadata || EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING entry_id
            """
        ),
        {
            "entry_id": entry.entry_id,
            "dataset_id": entry.dataset_id,
            "window_start": entry.window_start,
            "window_end": entry.window_end,
            "usage_purpose": entry.usage_purpose.value,
            "model_version": entry.model_version,
            "config_version": entry.config_version,
            "dataset_version": entry.dataset_version,
            "exposure_count": entry.exposure_count,
            "contamination_state": entry.contamination_state.value,
            "metadata": json.dumps(dict(entry.metadata)),
        },
    )
    return result.fetchone()[0]


async def load_contamination_entries(session: AsyncSession, dataset_id: str | None = None) -> list[ContaminationEntry]:
    if dataset_id:
        result = await session.execute(
            text("SELECT * FROM te_contamination_registry WHERE dataset_id = :dataset_id ORDER BY created_at"),
            {"dataset_id": dataset_id},
        )
    else:
        result = await session.execute(text("SELECT * FROM te_contamination_registry ORDER BY created_at"))
    entries: list[ContaminationEntry] = []
    for row in result.mappings().all():
        metadata = row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"])
        entries.append(
            ContaminationEntry(
                entry_id=row["entry_id"],
                dataset_id=row["dataset_id"],
                window_start=parse_temporal_instant(row["window_start"]),
                window_end=parse_temporal_instant(row["window_end"]),
                usage_purpose=ContaminationPurpose(row["usage_purpose"]),
                model_version=row["model_version"],
                config_version=row["config_version"],
                dataset_version=row["dataset_version"],
                exposure_count=row["exposure_count"],
                contamination_state=ContaminationState(row["contamination_state"]),
                metadata=metadata,
            )
        )
    return entries


async def insert_walk_forward_run(session: AsyncSession, row: Mapping[str, Any]) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_walk_forward_runs (
                run_id, dataset_id, model_version, config_version, dataset_version,
                train_start, train_end, eval_start, eval_end,
                purge_gap_seconds, embargo_gap_seconds, frozen, provenance, result_payload, contamination_checked
            ) VALUES (
                :run_id, :dataset_id, :model_version, :config_version, :dataset_version,
                :train_start, :train_end, :eval_start, :eval_end,
                :purge_gap_seconds, :embargo_gap_seconds, :frozen, CAST(:provenance AS jsonb),
                CAST(:result_payload AS jsonb), :contamination_checked
            )
            RETURNING run_id
            """
        ),
        dict(row),
    )
    return result.fetchone()[0]


async def insert_reality_anchor_observation(session: AsyncSession, row: Mapping[str, Any]) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_reality_anchor_observations (
                observation_id, anchor_id, receipt_id, forward_time_passage_verified,
                simulated_time_used, live_data_required, external_evidence_pending,
                external_gate_requirement_id, observation_payload
            ) VALUES (
                :observation_id, :anchor_id, :receipt_id, :forward_time_passage_verified,
                :simulated_time_used, :live_data_required, :external_evidence_pending,
                :external_gate_requirement_id, CAST(:observation_payload AS jsonb)
            )
            RETURNING observation_id
            """
        ),
        dict(row),
    )
    return result.fetchone()[0]


async def insert_spine_run(session: AsyncSession, row: Mapping[str, Any]) -> str:
    result = await session.execute(
        text(
            """
            INSERT INTO te_spine_runs (
                run_id, pipeline_stage, status, input_idempotency_key,
                event_id, evidence_id, receipt_id, error_code, observability
            ) VALUES (
                :run_id, :pipeline_stage, :status, :input_idempotency_key,
                :event_id, :evidence_id, :receipt_id, :error_code, CAST(:observability AS jsonb)
            )
            RETURNING run_id
            """
        ),
        dict(row),
    )
    return result.fetchone()[0]


def new_spine_run_id() -> str:
    return f"spine_{uuid4().hex[:16]}"
