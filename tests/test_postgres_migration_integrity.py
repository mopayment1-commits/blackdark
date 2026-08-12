"""P0 database integrity — clean Postgres migrate, CRUD, rollback semantics."""

from __future__ import annotations

import os

import pytest

from postgres_backend import _sqlite_schema_to_pg


def test_autoincrement_translation_covers_migration_ddl():
    sql = """
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        price REAL NOT NULL
    );
    INSERT OR IGNORE INTO t(id) VALUES (1);
    """
    pg = _sqlite_schema_to_pg(sql)
    assert "AUTOINCREMENT" not in pg.upper()
    assert "SERIAL PRIMARY KEY" in pg.upper()
    assert "DOUBLE PRECISION" in pg.upper()
    # INSERT OR IGNORE is preserved for execute() → ON CONFLICT rewrite.
    assert "INSERT OR IGNORE" in pg.upper()


@pytest.mark.asyncio
async def test_adapter_execute_translates_autoincrement(monkeypatch):
    import postgres_backend as pb

    class _FakeConn:
        def __init__(self):
            self.queries: list[str] = []

        async def execute(self, q, *params):
            self.queries.append(q)
            return "CREATE 0"

        async def fetch(self, q, *params):
            return []

        def transaction(self):
            return _FakeTx()

    class _FakeTx:
        async def start(self):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

    conn = _FakeConn()
    adapter = pb.PgConnectionAdapter(conn, _FakeTx())
    await adapter.execute(
        "CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY AUTOINCREMENT, x REAL)"
    )
    assert conn.queries
    assert "AUTOINCREMENT" not in conn.queries[0].upper()
    assert "SERIAL" in conn.queries[0].upper()


@pytest.mark.asyncio
async def test_adapter_commit_and_rollback_are_real():
    import postgres_backend as pb

    class _FakeTx:
        def __init__(self):
            self.ops: list[str] = []

        async def start(self):
            self.ops.append("start")

        async def commit(self):
            self.ops.append("commit")

        async def rollback(self):
            self.ops.append("rollback")

    class _FakeConn:
        def __init__(self):
            self.tx = _FakeTx()

        def transaction(self):
            self.tx = _FakeTx()
            return self.tx

    conn = _FakeConn()
    tx = conn.tx
    adapter = pb.PgConnectionAdapter(conn, tx)
    await adapter.commit()
    assert "commit" in tx.ops
    assert adapter._tx is not tx  # restarted
    old = adapter._tx
    await adapter.rollback()
    assert "rollback" in old.ops


POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)


def _postgres_reachable() -> bool:
    import socket

    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1.5):
            return True
    except OSError:
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_clean_postgres_migrate_crud_rollback_restart(monkeypatch, tmp_path):
    import asyncpg

    import config
    import database
    import postgres_backend as pb

    monkeypatch.setattr(config, "DATABASE_URL", POSTGRES_URL)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "unused.db")

    raw = await asyncpg.connect(POSTGRES_URL)
    await raw.execute("DROP SCHEMA public CASCADE")
    await raw.execute("CREATE SCHEMA public")
    await raw.close()

    await pb.close_pool()
    await database.init_db()

    marker = "migrate-integrity-marker"
    async with database.get_connection() as db:
        await db.execute(
            """
            INSERT INTO pricing_logs (timestamp, exchange, symbol, price, market_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("2026-01-01T00:00:00+00:00", marker, "BTC/USDT", 1.0, "spot"),
        )
        rows = await (
            await db.execute("SELECT exchange FROM pricing_logs WHERE exchange = ?", (marker,))
        ).fetchall()
        assert rows

    rollback_marker = "rollback-integrity-marker"
    async with database.get_connection() as db:
        await db.execute(
            """
            INSERT INTO pricing_logs (timestamp, exchange, symbol, price, market_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("2026-01-01T00:00:00+00:00", rollback_marker, "BTC/USDT", 1.0, "spot"),
        )
        await db.rollback()

    async with database.get_connection() as db:
        rows = await (
            await db.execute(
                "SELECT exchange FROM pricing_logs WHERE exchange = ?",
                (rollback_marker,),
            )
        ).fetchall()
        assert not rows

    await pb.close_pool()
    await database.init_db()
    async with database.get_connection() as db:
        rows = await (
            await db.execute("SELECT exchange FROM pricing_logs WHERE exchange = ?", (marker,))
        ).fetchall()
        assert rows

    await pb.close_pool()
