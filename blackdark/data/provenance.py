"""Provenance hashing and persistence helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PARSER_VERSION = "1.0.0"


def hash_payload(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


async def record_provenance(
    session: AsyncSession,
    *,
    ingestion_run_id: UUID | str,
    target_table: str,
    target_record_id: int,
    source_endpoint: str,
    raw_body: str | bytes,
    response_status: int,
    request_headers: dict[str, Any] | None = None,
) -> UUID:
    body = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
    result = await session.execute(
        text(
            """
            INSERT INTO data_provenance (
                ingestion_run_id, target_table, target_record_id,
                source_endpoint, request_headers, response_status,
                response_size_bytes, raw_response_hash, parser_version
            ) VALUES (
                :run_id, :table, :record_id,
                :endpoint, CAST(:headers AS jsonb), :status,
                :size, :hash, :parser
            )
            RETURNING id
            """
        ),
        {
            "run_id": str(ingestion_run_id),
            "table": target_table,
            "record_id": target_record_id,
            "endpoint": source_endpoint,
            "headers": json.dumps(request_headers or {}),
            "status": response_status,
            "size": len(body),
            "hash": hash_payload(body),
            "parser": PARSER_VERSION,
        },
    )
    row = result.fetchone()
    return row[0]


async def get_provenance_by_record(session: AsyncSession, record_id: UUID | str) -> dict[str, Any] | None:
    result = await session.execute(
        text(
            """
            SELECT
                p.id AS provenance_id,
                ds.slug AS source,
                p.source_endpoint,
                p.ingestion_run_id,
                ir.run_type,
                p.parsed_at AS fetched_at,
                p.raw_response_hash,
                p.parser_version,
                p.request_headers
            FROM data_provenance p
            LEFT JOIN ingestion_runs ir ON ir.id = p.ingestion_run_id
            LEFT JOIN data_sources ds ON ds.id = ir.source_id
            WHERE p.id = CAST(:id AS uuid)
            """
        ),
        {"id": str(record_id)},
    )
    row = result.mappings().fetchone()
    if not row:
        return None
    data = dict(row)
    if data.get("fetched_at"):
        data["fetched_at"] = data["fetched_at"].isoformat()
    return data
