"""Postgres dialect safety for subscription / rollout time windows (no SQLite datetime())."""

from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime, timedelta
from pathlib import Path


def test_fetch_active_subscription_sql_has_no_sqlite_datetime():
    import database

    src = inspect.getsource(database.fetch_active_subscription_for_email)
    # Strip comments so the remediation note does not false-positive.
    code = "\n".join(
        line for line in src.splitlines() if not line.lstrip().startswith("#")
    )
    assert "datetime(" not in code
    assert "past_due_at > ?" in code


def test_universe_rollout_sql_has_no_sqlite_datetime():
    import universe_rollout

    src = inspect.getsource(universe_rollout.live_rollout_status)
    assert "datetime(" not in src
    assert "timestamp >= ?" in src


def test_past_due_grace_floor_works_on_sqlite(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "sub.db"))
    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sub.db"))

    async def _run():
        await database.init_db()
        email = "past-due@example.com"
        now = datetime.now(UTC)
        past_due_at = (now - timedelta(days=2)).isoformat()
        async with database.get_connection() as db:
            await db.execute(
                """
                INSERT INTO subscriptions
                  (email, tier, status, past_due_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (email, "pro", "past_due", past_due_at, now.isoformat()),
            )
            await db.commit()
        row = await database.fetch_active_subscription_for_email(email)
        assert row is not None
        assert row["status"] == "past_due"
        assert row["tier"] == "pro"

        # Outside grace → expired / None
        old = (now - timedelta(days=30)).isoformat()
        async with database.get_connection() as db:
            await db.execute(
                "UPDATE subscriptions SET past_due_at = ? WHERE email = ?",
                (old, email),
            )
            await db.commit()
        assert await database.fetch_active_subscription_for_email(email) is None

    asyncio.run(_run())


def test_close_pool_tolerates_closed_event_loop(monkeypatch):
    import asyncio

    import postgres_backend as pb

    class _FakePool:
        def __init__(self):
            self.terminated = False

        async def close(self):
            raise RuntimeError("Event loop is closed")

        def terminate(self):
            self.terminated = True

    fake = _FakePool()
    monkeypatch.setattr(pb, "_pool", fake)

    async def _run():
        await pb.close_pool()

    asyncio.run(_run())
    assert fake.terminated is True
    assert pb._pool is None
