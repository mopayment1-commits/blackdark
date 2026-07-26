"""
BLACKDARK — PostgreSQL backend (asyncpg) for microservices / production scale.

Activated when DATABASE_URL starts with postgresql:// or postgres://
"""

from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import config

logger = logging.getLogger("BLACKDARK.Postgres")

_pool: Any = None


def use_postgres() -> bool:
    url = (getattr(config, "DATABASE_URL", None) or "").strip()
    return url.startswith("postgresql://") or url.startswith("postgres://")


def _sqlite_schema_to_pg(sqlite_schema: str) -> str:
    pg = sqlite_schema
    pg = re.sub(
        r"INTEGER PRIMARY KEY AUTOINCREMENT",
        "SERIAL PRIMARY KEY",
        pg,
        flags=re.IGNORECASE,
    )
    pg = re.sub(r"\bREAL\b", "DOUBLE PRECISION", pg)
    pg = re.sub(r"INSERT OR IGNORE", "INSERT", pg, flags=re.IGNORECASE)
    return pg


class _PgResult:
    def __init__(self, rowcount: int = 0, lastrowid: int | None = None) -> None:
        self.rowcount = rowcount
        self.lastrowid = lastrowid


class PgConnectionAdapter:
    """Minimal aiosqlite-compatible wrapper over asyncpg."""

    row_factory = None

    def __init__(self, conn: Any) -> None:
        self._conn = conn
        self._last_id: int | None = None

    @staticmethod
    def _convert_query(query: str) -> str:
        if "?" not in query:
            return query
        idx = 0
        parts: list[str] = []
        for ch in query:
            if ch == "?":
                idx += 1
                parts.append(f"${idx}")
            else:
                parts.append(ch)
        return "".join(parts)

    async def execute(self, query: str, params: tuple | list = ()) -> _PgResult:
        q = self._convert_query(query)
        if q.strip().upper().startswith("INSERT") and "RETURNING" not in q.upper():
            q = q.rstrip(";") + " RETURNING id"
            row = await self._conn.fetchrow(q, *params)
            self._last_id = int(row["id"]) if row and "id" in row else None
            return _PgResult(rowcount=1, lastrowid=self._last_id)
        status = await self._conn.execute(q, *params)
        count = 0
        if status:
            try:
                count = int(str(status).split()[-1])
            except (TypeError, ValueError):
                count = 0
        return _PgResult(rowcount=count, lastrowid=self._last_id)

    async def executemany(self, query: str, params_seq: list) -> None:
        q = self._convert_query(query)
        await self._conn.executemany(q, params_seq)

    async def executescript(self, script: str) -> None:
        from database import SCHEMA

        ddl = _sqlite_schema_to_pg(script or SCHEMA)
        for stmt in ddl.split(";"):
            cleaned = stmt.strip()
            if cleaned:
                await self._conn.execute(cleaned)

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def close(self) -> None:
        pass


async def init_pool() -> None:
    global _pool
    if _pool is not None or not use_postgres():
        return
    import asyncpg

    url = config.DATABASE_URL.strip()
    _pool = await asyncpg.create_pool(
        url,
        min_size=2,
        max_size=int(getattr(config, "PG_POOL_MAX", 20)),
        command_timeout=30,
    )
    logger.info("PostgreSQL pool ready.")


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_postgres() -> None:
    from database import SCHEMA

    await init_pool()
    assert _pool is not None
    ddl = _sqlite_schema_to_pg(SCHEMA)
    async with _pool.acquire() as conn:
        for stmt in ddl.split(";"):
            cleaned = stmt.strip()
            if cleaned:
                try:
                    await conn.execute(cleaned)
                except Exception as exc:
                    if "already exists" not in str(exc).lower():
                        logger.debug("PG DDL skip: %s", exc)
        ts = datetime.now(timezone.utc).isoformat()
        await conn.execute(
            """
            INSERT INTO platform_analytics
                (id, page_views, dashboard_views, landing_views, voice_commands,
                 waitlist_count, subscriber_count, updated_at)
            VALUES (1, 0, 0, 0, 0, 0, 0, $1)
            ON CONFLICT (id) DO NOTHING
            """,
            ts,
        )
        await conn.execute(
            """
            INSERT INTO execution_state (id, panic_active, auto_execution_enabled, updated_at)
            VALUES (1, 0, 0, $1)
            ON CONFLICT (id) DO NOTHING
            """,
            ts,
        )
    logger.info("PostgreSQL schema initialised.")


@asynccontextmanager
async def pg_connection() -> AsyncIterator[PgConnectionAdapter]:
    if _pool is None:
        await init_pool()
    assert _pool is not None
    async with _pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()
        adapter = PgConnectionAdapter(conn)
        try:
            yield adapter
            await tx.commit()
        except Exception:
            await tx.rollback()
            raise


def pool_stats() -> dict[str, Any]:
    if _pool is None:
        return {"active": False}
    return {
        "active": True,
        "min_size": _pool.get_min_size(),
        "max_size": _pool.get_max_size(),
        "size": _pool.get_size(),
    }
