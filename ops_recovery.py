"""Ops recovery minimum — backup/restore probe + dependency degrade semantics."""

from __future__ import annotations

import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def prove_sqlite_backup_restore() -> dict[str, Any]:
    """Copy SQLite DB to temp, reopen, verify institutional table readable."""
    db_path = Path(config.DB_PATH)
    if not db_path.exists():
        from institutional_store import ensure_ready

        ensure_ready()
    if not db_path.exists():
        return {"ok": False, "reason": "db_missing", "engine": "sqlite"}

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "blackdark_backup.db"
        shutil.copy2(db_path, dest)
        import sqlite3

        conn = sqlite3.connect(str(dest))
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'inst_%'"
            )
            tables = sorted(r[0] for r in cur.fetchall())
            ok = "inst_oms_orders" in tables and "inst_audit_events" in tables
            return {
                "ok": ok,
                "engine": "sqlite",
                "backup_bytes": dest.stat().st_size,
                "institutional_tables": tables,
                "proved_at": _utcnow(),
                "control": "backup_restore",
            }
        finally:
            conn.close()


async def prove_db_authority_tables() -> dict[str, Any]:
    """Verify institutional tables exist on the active engine (SQLite or Postgres)."""
    from institutional_store import ensure_ready
    from postgres_backend import use_postgres

    ensure_ready()
    engine = "postgres" if use_postgres() else "sqlite"
    required = {
        "inst_oms_orders",
        "inst_decision_nodes",
        "inst_memory",
        "inst_alerts",
        "inst_portfolio_positions",
        "inst_audit_events",
    }
    from database import get_connection

    async with get_connection() as db:
        if use_postgres():
            cur = await db.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name LIKE 'inst_%'
                """
            )
            rows = await cur.fetchall()
            tables = sorted(str(r[0] if not isinstance(r, dict) else r.get("table_name")) for r in rows)
        else:
            cur = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'inst_%'"
            )
            rows = await cur.fetchall()
            tables = sorted(str(r[0] if not isinstance(r, dict) else list(r.values())[0]) for r in rows)
    missing = sorted(required - set(tables))
    return {
        "ok": not missing,
        "engine": engine,
        "authority": engine,
        "institutional_tables": tables,
        "missing": missing,
        "database_url_configured": bool(getattr(config, "DATABASE_URL", "") or ""),
        "control": "schema_authority",
        "proved_at": _utcnow(),
        "note": (
            "Postgres HA / pg_dump DR is EXTERNAL operational proof. "
            "This control verifies schema authority on the configured engine."
        ),
    }


def prove_db_authority_tables_sync() -> dict[str, Any]:
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, prove_db_authority_tables()).result(timeout=30)
        return loop.run_until_complete(prove_db_authority_tables())
    except RuntimeError:
        return asyncio.run(prove_db_authority_tables())


def dependency_degrade_matrix() -> dict[str, Any]:
    """Document/prove fail-closed degrade contracts for core deps."""
    return {
        "postgres_or_sqlite": {
            "required_for": ["oms", "decision", "alerts", "portfolio"],
            "on_outage": "fail_closed_writes",
        },
        "redis": {
            "required_for": ["price_cache_optional"],
            "on_outage": "degrade_to_direct_stream",
        },
        "provider_ws": {
            "required_for": ["live_books"],
            "on_outage": "canonical_truth_bus_fail_closed",
        },
        "webhook_connectors": {
            "required_for": ["b2b_delivery"],
            "on_outage": "accepted_pending_connector",
        },
    }


def prove_postgres_ddl_ready() -> dict[str, Any]:
    """Offline Postgres readiness: translate core + institutional DDL idioms."""
    import re

    from database import SCHEMA
    from postgres_backend import _sqlite_schema_to_pg

    # Institutional tables live in migrations; include representative DDL for translate proof.
    inst_ddl = """
    CREATE TABLE IF NOT EXISTS inst_oms_orders (
        order_id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        quantity REAL NOT NULL,
        filled_quantity REAL NOT NULL DEFAULT 0,
        id INTEGER PRIMARY KEY AUTOINCREMENT
    );
    CREATE TABLE IF NOT EXISTS inst_audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id TEXT NOT NULL,
        payload_json TEXT
    );
    """
    combined = f"{SCHEMA}\n{inst_ddl}"
    pg = _sqlite_schema_to_pg(combined)
    forbidden = []
    if re.search(r"AUTOINCREMENT", pg, flags=re.IGNORECASE):
        forbidden.append("AUTOINCREMENT")
    if re.search(r"\bPRAGMA\b", pg, flags=re.IGNORECASE):
        forbidden.append("PRAGMA")
    if re.search(r"\bREAL\b", pg):
        forbidden.append("REAL")
    inst_ok = "inst_oms_orders" in pg and "inst_audit_events" in pg
    serial_ok = "SERIAL PRIMARY KEY" in pg
    return {
        "ok": inst_ok and serial_ok and not forbidden,
        "control": "postgres_ddl_ready",
        "institutional_ddl_present": inst_ok,
        "serial_translation": serial_ok,
        "forbidden_sqlite_idioms_remaining": forbidden,
        "translated_chars": len(pg),
        "ha_dr": "EXTERNAL",
        "note": "Offline DDL translate proof only — not a live Postgres HA/pg_dump exercise.",
        "proved_at": _utcnow(),
    }


def prove_postgres_local_dump_restore() -> dict[str, Any]:
    """Ephemeral local Postgres dump→restore prove (NOT production HA).

    Uses BLACKDARK_PG_DR_URL or postgresql://blackdark:blackdark@127.0.0.1:5432/postgres.
    Labels ha_dr=LOCAL_EPHEMERAL_NOT_HA — never claims cluster HA/RPO.
    """
    import os
    import subprocess
    import tempfile
    import uuid
    from urllib.parse import urlparse

    url = (
        os.getenv("BLACKDARK_PG_DR_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql://blackdark:blackdark@127.0.0.1:5432/postgres"
    ).strip()
    if not url.startswith(("postgresql://", "postgres://")):
        return {
            "ok": False,
            "control": "postgres_local_dump_restore",
            "reason": "no_postgres_url",
            "ha_dr": "EXTERNAL",
            "proved_at": _utcnow(),
        }

    parsed = urlparse(url)
    user = parsed.username or "blackdark"
    password = parsed.password or "blackdark"
    host = parsed.hostname or "127.0.0.1"
    port = str(parsed.port or 5432)
    admin_db = (parsed.path or "/postgres").lstrip("/") or "postgres"
    probe_db = f"blackdark_dr_{uuid.uuid4().hex[:10]}"
    env = {**os.environ, "PGPASSWORD": password}

    def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )

    created = False
    dump_path = ""
    try:
        c1 = _run(
            [
                "psql",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                admin_db,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                f'CREATE DATABASE "{probe_db}"',
            ]
        )
        if c1.returncode != 0:
            return {
                "ok": False,
                "control": "postgres_local_dump_restore",
                "reason": f"create_db_failed:{c1.stderr.strip()[:200]}",
                "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
                "proved_at": _utcnow(),
            }
        created = True
        c2 = _run(
            [
                "psql",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                probe_db,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                """
                CREATE TABLE inst_oms_orders (
                    order_id TEXT PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    state TEXT NOT NULL
                );
                CREATE TABLE inst_audit_events (
                    id SERIAL PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    event_type TEXT NOT NULL
                );
                INSERT INTO inst_oms_orders VALUES ('oms_dr_1','org_dr','INTENT');
                INSERT INTO inst_audit_events (org_id, event_type) VALUES ('org_dr','dr_seed');
                """,
            ]
        )
        if c2.returncode != 0:
            return {
                "ok": False,
                "control": "postgres_local_dump_restore",
                "reason": f"seed_failed:{c2.stderr.strip()[:200]}",
                "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
                "proved_at": _utcnow(),
            }
        with tempfile.TemporaryDirectory() as tmp:
            dump_path = str(Path(tmp) / f"{probe_db}.dump")
            d1 = _run(
                [
                    "pg_dump",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-Fc",
                    "-f",
                    dump_path,
                    probe_db,
                ]
            )
            if d1.returncode != 0:
                return {
                    "ok": False,
                    "control": "postgres_local_dump_restore",
                    "reason": f"dump_failed:{d1.stderr.strip()[:200]}",
                    "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
                    "proved_at": _utcnow(),
                }
            _run(
                [
                    "psql",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-d",
                    admin_db,
                    "-c",
                    f'DROP DATABASE "{probe_db}"',
                ]
            )
            created = False
            c3 = _run(
                [
                    "psql",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-d",
                    admin_db,
                    "-c",
                    f'CREATE DATABASE "{probe_db}"',
                ]
            )
            if c3.returncode != 0:
                return {
                    "ok": False,
                    "control": "postgres_local_dump_restore",
                    "reason": f"recreate_failed:{c3.stderr.strip()[:200]}",
                    "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
                    "proved_at": _utcnow(),
                }
            created = True
            r1 = _run(
                [
                    "pg_restore",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-d",
                    probe_db,
                    dump_path,
                ]
            )
            # pg_restore may return non-zero with warnings; verify tables explicitly
            v1 = _run(
                [
                    "psql",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-d",
                    probe_db,
                    "-tAc",
                    "SELECT count(*) FROM inst_oms_orders WHERE order_id='oms_dr_1'",
                ]
            )
            v2 = _run(
                [
                    "psql",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-d",
                    probe_db,
                    "-tAc",
                    "SELECT count(*) FROM inst_audit_events",
                ]
            )
            ok = (
                v1.returncode == 0
                and v2.returncode == 0
                and (v1.stdout or "").strip() == "1"
                and int((v2.stdout or "0").strip() or "0") >= 1
            )
            return {
                "ok": ok,
                "control": "postgres_local_dump_restore",
                "engine": "postgres",
                "probe_db": probe_db,
                "dump_bytes": Path(dump_path).stat().st_size if Path(dump_path).exists() else 0,
                "restore_rc": r1.returncode,
                "oms_rows": (v1.stdout or "").strip(),
                "audit_rows": (v2.stdout or "").strip(),
                "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
                "note": "Local ephemeral dump/restore only — not multi-AZ HA / RPO-RTO certification.",
                "proved_at": _utcnow(),
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "control": "postgres_local_dump_restore",
            "reason": f"{type(exc).__name__}:{exc}"[:200],
            "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
            "proved_at": _utcnow(),
        }
    finally:
        if created:
            _run(
                [
                    "psql",
                    "-h",
                    host,
                    "-p",
                    port,
                    "-U",
                    user,
                    "-d",
                    admin_db,
                    "-c",
                    f'DROP DATABASE IF EXISTS "{probe_db}"',
                ]
            )


def ops_status() -> dict[str, Any]:
    from postgres_backend import use_postgres

    authority = prove_db_authority_tables_sync()
    ddl = prove_postgres_ddl_ready()
    pg_dr = prove_postgres_local_dump_restore()
    if use_postgres():
        backup = {
            "ok": bool(authority.get("ok")) and bool(pg_dr.get("ok")),
            "engine": "postgres",
            "control": "backup_restore",
            "note": "Schema authority + local ephemeral dump/restore. Production HA remains EXTERNAL.",
            "institutional_tables": authority.get("institutional_tables"),
            "local_dump_restore": pg_dr,
            "proved_at": _utcnow(),
        }
    else:
        backup = prove_sqlite_backup_restore()
    return {
        "surface": "ops_recovery",
        "backup_restore": backup,
        "schema_authority": authority,
        "postgres_ddl_ready": ddl,
        "postgres_local_dump_restore": pg_dr,
        "degrade": dependency_degrade_matrix(),
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "proved_at": _utcnow(),
    }
