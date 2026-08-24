"""Apply numbered SQL migrations for Wave 01 data engine."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text

from blackdark.data.db import get_engine

logger = logging.getLogger("BLACKDARK.DataEngine.Migrate")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
_REQUIRED_TABLES = (
    "data_sources",
    "ingestion_runs",
    "ohlcv_data",
    "de_funding_rates",
    "open_interest",
    "market_events",
    "data_provenance",
    "ingestion_errors",
    "market_snapshots",
)

_migrate_lock = asyncio.Lock()


async def _table_exists(conn, table: str) -> bool:
    result = await conn.execute(
        text(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = :table
            """
        ),
        {"table": table},
    )
    return result.fetchone() is not None


async def _repair_migration_state(conn) -> bool:
    """Reset migration ledger when tables are missing (partial/failed prior deploy)."""
    missing = []
    for table in _REQUIRED_TABLES:
        if not await _table_exists(conn, table):
            missing.append(table)
    if not missing:
        return False
    ledger = await _table_exists(conn, "data_engine_migrations")
    if ledger:
        await conn.execute(text("DELETE FROM data_engine_migrations"))
        logger.warning(
            "Reset data_engine_migrations — missing tables: %s",
            ", ".join(missing),
        )
    return True


async def apply_migrations() -> dict[str, Any]:
    async with _migrate_lock:
        engine = get_engine()
        applied: list[str] = []
        skipped: list[str] = []
        repaired = False

        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS data_engine_migrations (
                        version VARCHAR(64) PRIMARY KEY,
                        applied_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
            )

        async with engine.begin() as conn:
            repaired = await _repair_migration_state(conn)

        async with engine.connect() as conn:
            rows = await conn.execute(text("SELECT version FROM data_engine_migrations"))
            done = {r[0] for r in rows.fetchall()}
            await conn.commit()

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = path.stem
            if version in done and not repaired:
                skipped.append(version)
                continue
            sql = path.read_text(encoding="utf-8")
            try:
                async with engine.begin() as conn:
                    for stmt in (part.strip() for part in sql.split(";")):
                        if stmt:
                            await conn.execute(text(stmt))
                    await conn.execute(
                        text(
                            """
                            INSERT INTO data_engine_migrations (version)
                            VALUES (:v)
                            ON CONFLICT (version) DO NOTHING
                            """
                        ),
                        {"v": version},
                    )
                applied.append(version)
                logger.info("Applied data engine migration %s", version)
            except Exception:
                logger.exception("Failed to apply data engine migration %s", version)
                raise

        return {
            "applied": applied,
            "skipped": skipped,
            "repaired": repaired,
            "total": len(list(MIGRATIONS_DIR.glob("*.sql"))),
        }
