"""
BLACKDARK — PostgreSQL backend (asyncpg) for microservices / production scale.

Activated when DATABASE_URL starts with postgresql:// or postgres://
"""

from __future__ import annotations

import asyncio

import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.Postgres")

_pool: Any = None


def use_postgres() -> bool:
    url = (getattr(config, "DATABASE_URL", None) or "").strip()
    return url.startswith(("postgresql://", "postgres://"))


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
    """aiosqlite-compatible cursor result with fetch helpers."""

    def __init__(
        self,
        rows: list[Any] | None = None,
        *,
        rowcount: int = 0,
        lastrowid: int | None = None,
    ) -> None:
        self._rows = list(rows or [])
        self.rowcount = rowcount if rows is None else len(self._rows)
        self.lastrowid = lastrowid

    async def fetchall(self) -> list[Any]:
        await asyncio.sleep(0)
        return list(self._rows)

    async def fetchone(self) -> Any | None:
        await asyncio.sleep(0)
        return self._rows[0] if self._rows else None

    async def fetchmany(self, size: int = 1) -> list[Any]:
        await asyncio.sleep(0)
        return self._rows[: max(0, size)]


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

    @staticmethod
    def _is_read_query(query: str) -> bool:
        head = query.lstrip().upper()
        return (
            head.startswith(("SELECT", "WITH", "PRAGMA")) or " RETURNING " in f" {head} "
        )

    @staticmethod
    def _row_to_mapping(row: Any) -> dict[str, Any]:
        if row is None:
            return {}
        try:
            return dict(row)
        except Exception:
            return {"value": row}

    @staticmethod
    def _rowcount_from_status(status: Any) -> int:
        if not status:
            return 0
        try:
            return int(str(status).split()[-1])
        except (TypeError, ValueError):
            return 0

    async def _execute_insert_without_returning(
        self,
        q: str,
        params: tuple | list,
    ) -> _PgResult:
        try:
            q_ret = q.rstrip(";") + " RETURNING id"
            row = await self._conn.fetchrow(q_ret, *params)
            self._last_id = int(row["id"]) if row and "id" in row else None
            mapped = [self._row_to_mapping(row)] if row else []
            return _PgResult(mapped, rowcount=1, lastrowid=self._last_id)
        except Exception:
            status = await self._conn.execute(q, *params)
            count = self._rowcount_from_status(status)
            return _PgResult(rowcount=count, lastrowid=self._last_id)

    async def execute(self, query: str, params: tuple | list = ()) -> _PgResult:
        q = self._convert_query(query)
        upper = q.strip().upper()

        # Keep INSERT OR IGNORE / SQLite idioms from crashing hard on PG reads/writes.
        if "INSERT OR IGNORE" in upper:
            q = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", q, count=1, flags=re.IGNORECASE)
            if "ON CONFLICT" not in q.upper():
                q = q.rstrip(";") + " ON CONFLICT DO NOTHING"
            upper = q.strip().upper()

        if upper.startswith("INSERT") and "RETURNING" not in upper:
            # Prefer returning id when present; fall back safely for tables without id.
            return await self._execute_insert_without_returning(q, params)

        if self._is_read_query(q):
            rows = await self._conn.fetch(q, *params)
            mapped = [self._row_to_mapping(r) for r in rows]
            return _PgResult(mapped, lastrowid=self._last_id)

        status = await self._conn.execute(q, *params)
        count = self._rowcount_from_status(status)
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
        # asyncpg autocommits each statement; keep sqlite-compatible no-op.
        await asyncio.sleep(0)
        self._last_txn_op = "commit"

    async def rollback(self) -> None:
        # No transaction boundary to undo under asyncpg autocommit.
        await asyncio.sleep(0)
        self._last_txn_op = "rollback"

    async def close(self) -> None:
        # Connection lifetime is owned by the pool, not this wrapper.
        await asyncio.sleep(0)
        self._last_txn_op = "close"


async def init_pool() -> None:
    global _pool
    if _pool is not None or not use_postgres():
        return
    import os

    import asyncpg

    url = config.DATABASE_URL.strip()
    viral = os.getenv("VIRAL_MODE", "true").lower() in {"1", "true", "yes"}
    default_max = 40 if viral else 20
    max_size = int(os.getenv("PG_POOL_MAX", str(getattr(config, "PG_POOL_MAX", default_max))))
    min_size = int(os.getenv("PG_POOL_MIN", "4" if viral else "2"))
    min_size = max(1, min(min_size, max_size))
    _pool = await asyncpg.create_pool(
        url,
        min_size=min_size,
        max_size=max_size,
        command_timeout=float(os.getenv("PG_COMMAND_TIMEOUT_SEC", "20")),
        max_inactive_connection_lifetime=float(os.getenv("PG_MAX_INACTIVE_CONN_LIFETIME", "300")),
    )
    logger.info("PostgreSQL pool ready (min=%s max=%s viral=%s).", min_size, max_size, viral)


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
        ts = datetime.now(UTC).isoformat()
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
