"""Persistence for canonical assets and normalized records."""

from __future__ import annotations

import json
import logging
from typing import Any

from blackdark.canonical.registry import all_canonical_assets, registry_stats
from blackdark.canonical.schema import CanonicalAsset

logger = logging.getLogger("BLACKDARK.CanonicalStore")


async def ensure_canonical_schema(db: Any) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS canonical_assets (
            canonical_id       TEXT PRIMARY KEY,
            symbol             TEXT NOT NULL UNIQUE,
            label              TEXT,
            aliases_json       TEXT,
            sector             TEXT,
            external_ids_json  TEXT,
            contracts_json     TEXT,
            registry_version   INTEGER NOT NULL DEFAULT 1,
            updated_at         TEXT NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_canonical_assets_symbol
        ON canonical_assets (symbol)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS canonical_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_id    TEXT NOT NULL,
            dataset         TEXT NOT NULL,
            source          TEXT,
            payload_json    TEXT NOT NULL,
            normalized_at   TEXT NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_canonical_records_lookup
        ON canonical_records (canonical_id, dataset, normalized_at DESC)
        """
    )


async def sync_registry_to_db() -> dict[str, Any]:
    """Materialize in-memory registry into SQLite for fast SQL queries."""
    from database import get_connection, _utcnow_iso

    assets = all_canonical_assets()
    now = _utcnow_iso()
    written = 0
    async with get_connection() as db:
        await ensure_canonical_schema(db)
        for asset in assets:
            await db.execute(
                """
                INSERT INTO canonical_assets (
                    canonical_id, symbol, label, aliases_json, sector,
                    external_ids_json, contracts_json, registry_version, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(canonical_id) DO UPDATE SET
                    symbol = excluded.symbol,
                    label = excluded.label,
                    aliases_json = excluded.aliases_json,
                    sector = excluded.sector,
                    external_ids_json = excluded.external_ids_json,
                    contracts_json = excluded.contracts_json,
                    registry_version = excluded.registry_version,
                    updated_at = excluded.updated_at
                """,
                (
                    asset.canonical_id,
                    asset.symbol,
                    asset.label,
                    json.dumps(list(asset.aliases)),
                    asset.sector,
                    json.dumps(asset.external_ids),
                    json.dumps(asset.contracts),
                    asset.registry_version,
                    now,
                ),
            )
            written += 1
    return {"synced": written, **registry_stats()}


async def insert_canonical_record(
    *,
    canonical_id: str,
    dataset: str,
    source: str,
    payload: dict[str, Any],
) -> int | None:
    from database import get_connection, _utcnow_iso

    async with get_connection() as db:
        await ensure_canonical_schema(db)
        cur = await db.execute(
            """
            INSERT INTO canonical_records (canonical_id, dataset, source, payload_json, normalized_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (canonical_id, dataset, source, json.dumps(payload, default=str), _utcnow_iso()),
        )
        return int(cur.lastrowid or 0) or None


async def fetch_latest_canonical_record(
    *, canonical_id: str, dataset: str
) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        await ensure_canonical_schema(db)
        row = await (
            await db.execute(
                """
                SELECT payload_json, normalized_at, source
                FROM canonical_records
                WHERE canonical_id = ? AND dataset = ?
                ORDER BY normalized_at DESC
                LIMIT 1
                """,
                (canonical_id, dataset),
            )
        ).fetchone()
        if not row:
            return None
        payload = json.loads(row[0] if not isinstance(row, dict) else row["payload_json"])
        return {
            "canonical_id": canonical_id,
            "dataset": dataset,
            "source": row[2] if not isinstance(row, dict) else row.get("source"),
            "normalized_at": row[1] if not isinstance(row, dict) else row.get("normalized_at"),
            "payload": payload,
        }


async def fetch_canonical_assets_from_db(*, limit: int = 200) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        await ensure_canonical_schema(db)
        rows = await (
            await db.execute(
                """
                SELECT canonical_id, symbol, label, aliases_json, sector,
                       external_ids_json, contracts_json, registry_version, updated_at
                FROM canonical_assets
                ORDER BY symbol
                LIMIT ?
                """,
                (limit,),
            )
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            r = row
        else:
            r = {
                "canonical_id": row[0],
                "symbol": row[1],
                "label": row[2],
                "aliases_json": row[3],
                "sector": row[4],
                "external_ids_json": row[5],
                "contracts_json": row[6],
                "registry_version": row[7],
                "updated_at": row[8],
            }
        out.append(
            CanonicalAsset.from_dict(
                {
                    "canonical_id": r["canonical_id"],
                    "symbol": r["symbol"],
                    "label": r["label"],
                    "aliases": json.loads(r["aliases_json"] or "[]"),
                    "sector": r["sector"],
                    "external_ids": json.loads(r["external_ids_json"] or "{}"),
                    "contracts": json.loads(r["contracts_json"] or "{}"),
                    "registry_version": r["registry_version"],
                }
            ).to_dict()
        )
    return out
