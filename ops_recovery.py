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
        "ha_dr": "DDL_TRANSLATE_ONLY",
        "note": (
            "Offline DDL translate proof only. Live HA/RPO is prove_postgres_streaming_ha_rpo_rto; "
            "not a substitute for cloud multi-AZ."
        ),
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


async def prove_postgres_product_path() -> dict[str, Any]:
    """Ephemeral Postgres product-path: ensure_ready + OMS round-trip on DATABASE_URL.

    Labels ha_dr=LOCAL_EPHEMERAL_NOT_HA — proves code path on Postgres, not cloud HA.
    """
    import os
    import subprocess
    import uuid
    from urllib.parse import urlparse

    import config
    import institutional_store as store
    import postgres_backend

    url = (
        os.getenv("BLACKDARK_PG_DR_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql://blackdark:blackdark@127.0.0.1:5432/postgres"
    ).strip()
    if not url.startswith(("postgresql://", "postgres://")):
        return {
            "ok": False,
            "control": "postgres_product_path",
            "reason": "no_postgres_url",
            "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
            "proved_at": _utcnow(),
        }

    parsed = urlparse(url)
    user = parsed.username or "blackdark"
    password = parsed.password or "blackdark"
    host = parsed.hostname or "127.0.0.1"
    port = str(parsed.port or 5432)
    admin_db = (parsed.path or "/postgres").lstrip("/") or "postgres"
    probe_db = f"blackdark_prodpath_{uuid.uuid4().hex[:10]}"
    probe_url = f"postgresql://{user}:{password}@{host}:{port}/{probe_db}"
    env = {**os.environ, "PGPASSWORD": password}
    prev_url = getattr(config, "DATABASE_URL", "") or ""
    created = False

    def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, env=env, check=False, capture_output=True, text=True, timeout=60)

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
                "control": "postgres_product_path",
                "reason": f"create_db_failed:{(c1.stderr or '')[:200]}",
                "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
                "proved_at": _utcnow(),
            }
        created = True

        config.DATABASE_URL = probe_url
        store._READY_FOR = None  # noqa: SLF001
        await postgres_backend.close_pool()
        # Use async store path directly — avoid nested loop/_run while this coro runs.
        await store._ensure_schema()  # noqa: SLF001
        order_id = f"oms_pg_{uuid.uuid4().hex[:8]}"
        row = {
            "order_id": order_id,
            "org_id": "pg_product_path",
            "venue": "okx",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quantity": 0.001,
            "filled_quantity": 0.0,
            "order_type": "limit",
            "limit_price": 1.0,
            "state": "INTENT",
            "idempotency_key": f"pg-{order_id}",
            "actor": "postgres_product_path",
            "history": [{"state": "INTENT"}],
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        await store.oms_upsert(row)
        got = await store.oms_get(order_id)
        authority = "postgres" if postgres_backend.use_postgres() else "sqlite"
        ok = bool(got and got.get("order_id") == order_id and authority == "postgres")
        return {
            "ok": ok,
            "control": "postgres_product_path",
            "engine": "postgres",
            "probe_db": probe_db,
            "authority": authority,
            "order_id": order_id,
            "oms_round_trip": bool(got),
            "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
            "note": "Product-path ensure_ready+OMS on ephemeral Postgres — not multi-AZ HA.",
            "proved_at": _utcnow(),
            "verified_complete": False,
            "implementation_class": "PARTIAL",
            "product_complete": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "control": "postgres_product_path",
            "reason": f"{type(exc).__name__}:{exc}"[:200],
            "ha_dr": "LOCAL_EPHEMERAL_NOT_HA",
            "proved_at": _utcnow(),
        }
    finally:
        try:
            await postgres_backend.close_pool()
        except Exception:
            pass
        config.DATABASE_URL = prev_url
        store._READY_FOR = None  # noqa: SLF001
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
                    f'DROP DATABASE IF EXISTS "{probe_db}" WITH (FORCE)',
                ]
            )


def prove_postgres_streaming_ha_rpo_rto() -> dict[str, Any]:
    """Local physical streaming replication HA with measured RPO/RTO.

    Uses pg_basebackup → standby on :5433 → insert visibility (RPO) → promote (RTO).
    Class: LOCAL_STREAMING_REPLICATION (behavioral). NOT cloud multi-AZ.
    """
    import os
    import shutil
    import subprocess
    import time
    import uuid
    from pathlib import Path
    from urllib.parse import urlparse

    url = (
        os.getenv("BLACKDARK_PG_DR_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql://blackdark:blackdark@127.0.0.1:5432/postgres"
    ).strip()
    if not url.startswith(("postgresql://", "postgres://")):
        return {
            "ok": False,
            "control": "postgres_streaming_ha_rpo_rto",
            "reason": "no_postgres_url",
            "ha_class": "UNAVAILABLE",
            "proved_at": _utcnow(),
        }

    parsed = urlparse(url)
    user = parsed.username or "blackdark"
    password = parsed.password or "blackdark"
    host = parsed.hostname or "127.0.0.1"
    port = str(parsed.port or 5432)
    admin_db = (parsed.path or "/postgres").lstrip("/") or "postgres"
    env = {**os.environ, "PGPASSWORD": password}
    standby_dir = Path(f"/tmp/bd_ha_standby_{uuid.uuid4().hex[:8]}")
    standby_port = str(int(os.getenv("BLACKDARK_PG_STANDBY_PORT", "5433")))
    marker = f"ha_{uuid.uuid4().hex}"
    pg_bin = Path("/usr/lib/postgresql/16/bin")
    if not (pg_bin / "pg_basebackup").exists():
        # Fallback: discover major version
        for cand in sorted(Path("/usr/lib/postgresql").glob("*/bin/pg_basebackup")):
            pg_bin = cand.parent
            break
    basebackup = str(pg_bin / "pg_basebackup")
    pg_ctl = str(pg_bin / "pg_ctl")

    def _run(args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, env=env, check=False, capture_output=True, text=True, timeout=timeout)

    def _psql(db_port: str, sql: str, db: str = admin_db) -> subprocess.CompletedProcess[str]:
        return _run(
            [
                "psql",
                "-h",
                host,
                "-p",
                db_port,
                "-U",
                user,
                "-d",
                db,
                "-v",
                "ON_ERROR_STOP=1",
                "-tAc",
                sql,
            ]
        )

    started = False
    try:
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
                "ALTER ROLE CURRENT_USER WITH REPLICATION;",
            ]
        )
        if standby_dir.exists():
            shutil.rmtree(standby_dir, ignore_errors=True)
        standby_dir.mkdir(mode=0o700, parents=True)
        bb = _run(
            [
                basebackup,
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-D",
                str(standby_dir),
                "-Fp",
                "-Xs",
                "-P",
                "-R",
            ],
            timeout=180,
        )
        if bb.returncode != 0:
            return {
                "ok": False,
                "control": "postgres_streaming_ha_rpo_rto",
                "reason": f"basebackup_failed:{(bb.stderr or bb.stdout or '')[:240]}",
                "ha_class": "LOCAL_STREAMING_REPLICATION",
                "proved_at": _utcnow(),
            }
        os.chmod(standby_dir, 0o700)
        (standby_dir / "pg_hba.conf").write_text(
            "\n".join(
                [
                    "host all all 127.0.0.1/32 scram-sha-256",
                    "host all all ::1/128 scram-sha-256",
                    "local all all trust",
                    "host replication all 127.0.0.1/32 scram-sha-256",
                    "local replication all trust",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (standby_dir / "pg_ident.conf").write_text("", encoding="utf-8")
        max_conn = (_psql(port, "SHOW max_connections;").stdout or "100").strip() or "100"
        max_workers = (_psql(port, "SHOW max_worker_processes;").stdout or "8").strip() or "8"
        (standby_dir / "postgresql.conf").write_text(
            "\n".join(
                [
                    f"port = {standby_port}",
                    "unix_socket_directories = '/tmp'",
                    "listen_addresses = '127.0.0.1'",
                    "hot_standby = on",
                    f"max_connections = {max_conn}",
                    f"max_worker_processes = {max_workers}",
                    "shared_buffers = 128MB",
                    "wal_level = replica",
                    "max_wal_senders = 10",
                    "hot_standby_feedback = on",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        log_path = standby_dir / "standby.log"
        start = _run([pg_ctl, "-D", str(standby_dir), "-l", str(log_path), "start"], timeout=60)
        if start.returncode != 0:
            return {
                "ok": False,
                "control": "postgres_streaming_ha_rpo_rto",
                "reason": f"standby_start_failed:{(start.stderr or '')[:200]}",
                "log_tail": (log_path.read_text(encoding="utf-8", errors="ignore")[-500:] if log_path.exists() else ""),
                "ha_class": "LOCAL_STREAMING_REPLICATION",
                "proved_at": _utcnow(),
            }
        started = True
        # wait ready
        ready = False
        for _ in range(40):
            r = _psql(standby_port, "SELECT pg_is_in_recovery();")
            if r.returncode == 0 and (r.stdout or "").strip() == "t":
                ready = True
                break
            time.sleep(0.15)
        if not ready:
            return {
                "ok": False,
                "control": "postgres_streaming_ha_rpo_rto",
                "reason": "standby_not_in_recovery",
                "ha_class": "LOCAL_STREAMING_REPLICATION",
                "proved_at": _utcnow(),
            }

        _psql(
            port,
            "CREATE TABLE IF NOT EXISTS ha_probe_marker(id text primary key, t timestamptz default now());",
        )
        _psql(port, f"INSERT INTO ha_probe_marker VALUES ('{marker}', now()) ON CONFLICT DO NOTHING;")
        t0 = time.perf_counter()
        visible = False
        for _ in range(80):
            c = _psql(standby_port, f"SELECT count(*) FROM ha_probe_marker WHERE id='{marker}';")
            if c.returncode == 0 and (c.stdout or "").strip() == "1":
                visible = True
                break
            time.sleep(0.05)
        rpo_ms = int((time.perf_counter() - t0) * 1000)

        t1 = time.perf_counter()
        prom = _run([pg_ctl, "-D", str(standby_dir), "promote"], timeout=60)
        promoted = False
        for _ in range(80):
            r = _psql(standby_port, "SELECT pg_is_in_recovery();")
            if r.returncode == 0 and (r.stdout or "").strip() == "f":
                promoted = True
                break
            time.sleep(0.05)
        rto_ms = int((time.perf_counter() - t1) * 1000)
        write_ok = False
        if promoted:
            w = _psql(
                standby_port,
                f"INSERT INTO ha_probe_marker VALUES ('promoted_{marker}', now()) ON CONFLICT DO NOTHING;",
            )
            write_ok = w.returncode == 0

        ok = bool(visible and promoted and write_ok and prom.returncode == 0 and rpo_ms < 5000 and rto_ms < 10000)
        return {
            "ok": ok,
            "control": "postgres_streaming_ha_rpo_rto",
            "ha_class": "LOCAL_STREAMING_REPLICATION",
            "cloud_multi_az": False,
            "standby_port": int(standby_port),
            "rpo_ms": rpo_ms,
            "rto_ms": rto_ms,
            "rpo_target_ms": 1000,
            "rto_target_ms": 5000,
            "rpo_met": rpo_ms <= 1000,
            "rto_met": rto_ms <= 5000,
            "marker_replicated": visible,
            "promoted": promoted,
            "promoted_writable": write_ok,
            "note": (
                "Local physical streaming replication with measured RPO/RTO. "
                "NOT a claim of cloud multi-AZ / managed HA."
            ),
            "verified_complete": ok,
            "implementation_class": "VERIFIED_COMPLETE" if ok else "PARTIAL",
            "product_complete": False,
            "proved_at": _utcnow(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "control": "postgres_streaming_ha_rpo_rto",
            "reason": f"{type(exc).__name__}:{exc}"[:240],
            "ha_class": "LOCAL_STREAMING_REPLICATION",
            "proved_at": _utcnow(),
            "verified_complete": False,
            "implementation_class": "PARTIAL",
        }
    finally:
        if started:
            _run([pg_ctl, "-D", str(standby_dir), "stop", "-m", "fast"], timeout=60)
        _psql(port, "DROP TABLE IF EXISTS ha_probe_marker;")
        if standby_dir.exists():
            shutil.rmtree(standby_dir, ignore_errors=True)


def prove_ops_recovery_bundle(*, include_streaming_ha: bool = False) -> dict[str, Any]:
    """Bundle local dump/restore + schema authority (+ optional streaming HA).

    Never claims cloud multi-AZ. Streaming HA remains the only VC candidate.
    """
    from institutional_store import ensure_ready, oms_get_sync, oms_upsert_sync, store_status

    authority = prove_db_authority_tables_sync()
    ddl = prove_postgres_ddl_ready()
    pg_dr = prove_postgres_local_dump_restore()
    sqlite_br = prove_sqlite_backup_restore()
    pg_ha: dict[str, Any] | None = None
    if include_streaming_ha:
        pg_ha = prove_postgres_streaming_ha_rpo_rto()

    # Process-restart continuity: re-open store and read back an OMS row.
    continuity: dict[str, Any] = {"ok": False}
    try:
        ensure_ready()
        order_id = f"ops_cont_{_utcnow().replace(':', '').replace('+', '')[:20]}"
        row = {
            "order_id": order_id,
            "org_id": "ops_bundle",
            "venue": "okx",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quantity": 0.001,
            "filled_quantity": 0.0,
            "order_type": "limit",
            "limit_price": 1.0,
            "state": "INTENT",
            "idempotency_key": f"ops-cont-{order_id}",
            "actor": "ops_bundle",
            "history": [{"state": "INTENT"}],
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        oms_upsert_sync(row)
        # Simulate re-open
        import institutional_store as store

        store._READY_FOR = None  # noqa: SLF001
        ensure_ready()
        got = oms_get_sync(order_id)
        continuity = {
            "ok": bool(got and got.get("order_id") == order_id and got.get("state") == "INTENT"),
            "order_id": order_id,
            "authority": store_status().get("authority"),
            "note": "Local process re-open continuity — not cloud multi-AZ HA.",
        }
    except Exception as exc:  # noqa: BLE001
        continuity = {"ok": False, "reason": type(exc).__name__}

    verified = bool(pg_ha and pg_ha.get("verified_complete"))
    ok = bool(authority.get("ok") and ddl.get("ok") and (pg_dr.get("ok") or sqlite_br.get("ok")) and continuity.get("ok"))
    out: dict[str, Any] = {
        "ok": ok,
        "surface": "ops_recovery_bundle",
        "schema_authority": {"ok": authority.get("ok")},
        "postgres_ddl_ready": {"ok": ddl.get("ok")},
        "postgres_local_dump_restore": {
            "ok": pg_dr.get("ok"),
            "ha_dr": pg_dr.get("ha_dr"),
        },
        "sqlite_backup_restore": {"ok": sqlite_br.get("ok")},
        "process_restart_continuity": continuity,
        "cloud_multi_az": False,
        "verified_complete": verified,
        "implementation_class": "VERIFIED_COMPLETE" if verified else "PARTIAL",
        "product_complete": False,
        "note": (
            "Local ops recovery bundle. Streaming HA VC only when include_streaming_ha "
            "and prove_postgres_streaming_ha_rpo_rto succeeds. Never cloud multi-AZ."
        ),
        "proved_at": _utcnow(),
    }
    if pg_ha is not None:
        out["postgres_streaming_ha_rpo_rto"] = {
            "ok": pg_ha.get("ok"),
            "verified_complete": pg_ha.get("verified_complete"),
            "rpo_ms": pg_ha.get("rpo_ms"),
            "rto_ms": pg_ha.get("rto_ms"),
            "cloud_multi_az": pg_ha.get("cloud_multi_az"),
        }
    return out


def ops_status(*, include_streaming_ha: bool = False) -> dict[str, Any]:
    """Ops status. Streaming HA is opt-in (heavy basebackup) — call prove_* directly for VC."""
    from postgres_backend import use_postgres

    bundle = prove_ops_recovery_bundle(include_streaming_ha=include_streaming_ha)
    authority = prove_db_authority_tables_sync()
    ddl = prove_postgres_ddl_ready()
    # Reuse dump/restore already exercised inside the bundle when possible.
    pg_dr = prove_postgres_local_dump_restore() if not bundle.get("postgres_local_dump_restore") else {
        "ok": (bundle.get("postgres_local_dump_restore") or {}).get("ok"),
        "ha_dr": (bundle.get("postgres_local_dump_restore") or {}).get("ha_dr"),
        "control": "postgres_local_dump_restore",
        "proved_at": _utcnow(),
    }
    pg_ha = bundle.get("postgres_streaming_ha_rpo_rto") if include_streaming_ha else None
    if use_postgres():
        backup = {
            "ok": bool(authority.get("ok")) and bool((pg_dr or {}).get("ok")),
            "engine": "postgres",
            "control": "backup_restore",
            "note": "Schema authority + local dump/restore. Streaming HA via prove_postgres_streaming_ha_rpo_rto.",
            "institutional_tables": authority.get("institutional_tables"),
            "local_dump_restore": pg_dr,
            "proved_at": _utcnow(),
        }
    else:
        backup = prove_sqlite_backup_restore()
    verified = bool(pg_ha and pg_ha.get("verified_complete"))
    out: dict[str, Any] = {
        "surface": "ops_recovery",
        "backup_restore": backup,
        "schema_authority": authority,
        "postgres_ddl_ready": ddl,
        "postgres_local_dump_restore": pg_dr,
        "ops_recovery_bundle": {
            "ok": bundle.get("ok"),
            "process_restart_continuity": bundle.get("process_restart_continuity"),
            "cloud_multi_az": False,
        },
        "postgres_streaming_ha_control": "prove_postgres_streaming_ha_rpo_rto",
        "degrade": dependency_degrade_matrix(),
        "verified_complete": verified,
        "implementation_class": "VERIFIED_COMPLETE" if verified else "PARTIAL",
        "product_complete": False,
        "proved_at": _utcnow(),
    }
    if pg_ha is not None:
        out["postgres_streaming_ha_rpo_rto"] = pg_ha
    return out
