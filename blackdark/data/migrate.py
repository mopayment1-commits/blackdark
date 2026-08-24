"""Apply numbered SQL migrations for Wave 01 data engine."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text

from blackdark.data.db import get_engine

logger = logging.getLogger("BLACKDARK.DataEngine.Migrate")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


async def apply_migrations() -> dict[str, Any]:
    engine = get_engine()
    applied: list[str] = []
    skipped: list[str] = []

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

    async with engine.connect() as conn:
        rows = await conn.execute(text("SELECT version FROM data_engine_migrations"))
        done = {r[0] for r in rows.fetchall()}
        await conn.commit()

    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = path.stem
        if version in done:
            skipped.append(version)
            continue
        sql = path.read_text(encoding="utf-8")
        try:
            async with engine.begin() as conn:
                for stmt in (part.strip() for part in sql.split(";")):
                    if stmt:
                        await conn.execute(text(stmt))
                await conn.execute(
                    text("INSERT INTO data_engine_migrations (version) VALUES (:v)"),
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
        "total": len(list(MIGRATIONS_DIR.glob("*.sql"))),
    }
