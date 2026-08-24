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
        rows = await conn.execute(text("SELECT version FROM data_engine_migrations"))
        done = {r[0] for r in rows.fetchall()}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = path.stem
            if version in done:
                continue
            sql = path.read_text(encoding="utf-8")
            await conn.execute(text(sql))
            await conn.execute(
                text("INSERT INTO data_engine_migrations (version) VALUES (:v)"),
                {"v": version},
            )
            applied.append(version)
            logger.info("Applied data engine migration %s", version)
    return {"applied": applied, "total": len(list(MIGRATIONS_DIR.glob("*.sql")))}
