"""
BLACKDARK — Database health & maintenance (Priority 5).

SQLite maintenance for production scale + optional PostgreSQL/Timescale readiness.
"""

from __future__ import annotations

import logging
import os
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.DBUpgrade")


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def external_database_status() -> dict[str, Any]:
    """Report configured external DB targets (not required for local SQLite)."""
    pg_url = os.getenv("DATABASE_URL", "").strip()
    ts_dsn = os.getenv("HOT_STORAGE_TIMESCALE_DSN", "").strip()
    clickhouse = os.getenv("HOT_STORAGE_CLICKHOUSE_URL", "").strip()
    backend = os.getenv("HOT_STORAGE_BACKEND", "local").strip().lower()
    primary = "postgresql" if pg_url.lower().startswith(("postgres://", "postgresql://")) else "sqlite"
    return {
        "primary": primary,
        "sqlite_path": str(config.DB_PATH),
        "postgres_configured": bool(pg_url),
        "timescale_configured": bool(ts_dsn),
        "clickhouse_configured": bool(clickhouse),
        "hot_storage_backend": backend,
        "upgrade_ready": bool(pg_url or ts_dsn),
        "note": (
            "PostgreSQL is the production engine when DATABASE_URL is set."
            if primary == "postgresql"
            else "SQLite is default. Set DATABASE_URL or HOT_STORAGE_TIMESCALE_DSN when scaling."
        ),
    }


def _is_postgres_url() -> bool:
    url = os.getenv("DATABASE_URL", "").strip().lower()
    return url.startswith(("postgres://", "postgresql://"))


async def database_health_report() -> dict[str, Any]:
    """Never raise: production /api/database/health must not 500."""
    users: dict[str, Any] = {}
    telemetry: dict[str, Any] = {}
    try:
        from database import fetch_platform_user_stats, fetch_system_telemetry

        users = await fetch_platform_user_stats()
        telemetry = await fetch_system_telemetry()
    except Exception as exc:
        logger.exception("database_health telemetry failed")
        telemetry = {"error": type(exc).__name__}

    external = external_database_status()
    if _is_postgres_url():
        pool: dict[str, Any] = {}
        resolver_meta: dict[str, Any] | None = None
        try:
            from postgres_backend import pool_stats

            pool = pool_stats()
            resolver_meta = pool.get("resolver")
        except Exception:
            pool = {"active": False}
        if not pool.get("active"):
            try:
                from database_url_resolver import resolve_database_url

                _, resolver_meta = resolve_database_url()
            except Exception:
                pass
        return {
            "timestamp": _utcnow_iso(),
            "engine": "postgresql",
            "ok": bool(pool.get("active") or users or telemetry),
            "telemetry": telemetry,
            "users": users,
            "postgres_pool": pool,
            "resolver": resolver_meta,
            "external": external,
            "recommendations": (
                ["PostgreSQL pool connected."]
                if pool.get("active")
                else ["DATABASE_URL is set; confirm the Railway Postgres plugin is attached."]
            ),
        }

    db_path = config.DB_PATH
    wal_path = Path(str(db_path) + "-wal")
    shm_path = Path(str(db_path) + "-shm")
    size_mb = round((telemetry.get("database_size_bytes") or 0) / (1024 * 1024), 2)
    recommendations: list[str] = []
    if size_mb > 500:
        recommendations.append("Database >500MB — run maintenance or enable parquet compaction.")
    if wal_path.exists() and wal_path.stat().st_size > 50 * 1024 * 1024:
        recommendations.append("WAL file large — run checkpoint via maintenance.")
    if (telemetry.get("pricing_count") or 0) > 500_000:
        recommendations.append("pricing_logs growing — retention prune recommended.")
    return {
        "timestamp": _utcnow_iso(),
        "engine": "sqlite",
        "ok": True,
        "telemetry": telemetry,
        "users": users,
        "database_size_mb": size_mb,
        "wal_size_mb": round(wal_path.stat().st_size / (1024 * 1024), 2) if wal_path.exists() else 0,
        "shm_exists": shm_path.exists(),
        "external": external,
        "recommendations": recommendations or ["Database healthy for current load."],
    }


async def prune_old_market_rows(retention_days: int | None = None) -> dict[str, int]:
    from database import get_connection

    days = retention_days or int(os.getenv("DB_RETENTION_DAYS", "30"))
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    deleted: dict[str, int] = {}

    from sql_safety import delete_before_sql

    async with get_connection() as db:
        for table in ("pricing_logs", "order_books"):
            cursor = await db.execute(
                delete_before_sql(table),
                (cutoff,),
            )
            deleted[table] = cursor.rowcount

        ingest_cursor = await db.execute(
            "DELETE FROM ingestion_snapshots WHERE fetched_at < ?",
            (cutoff,),
        )
        deleted["ingestion_snapshots"] = ingest_cursor.rowcount

    return deleted


async def run_sqlite_maintenance(*, vacuum: bool = True, analyze: bool = True) -> dict[str, Any]:
    """VACUUM + ANALYZE + WAL checkpoint + optional retention prune."""
    from database import get_connection, insert_maintenance_run, prune_ingestion_snapshots

    started = _utcnow_iso()
    results: dict[str, Any] = {"started_at": started, "actions": []}

    prune_rows = os.getenv("DB_MAINTENANCE_PRUNE", "true").lower() in {"1", "true", "yes"}
    if prune_rows:
        deleted = await prune_old_market_rows()
        results["actions"].append({"prune_old_rows": deleted})
        ingested = await prune_ingestion_snapshots(max_rows=50_000)
        results["actions"].append({"prune_ingestion_snapshots": ingested})

    async with get_connection() as db:
        if analyze:
            await db.execute("ANALYZE")
            results["actions"].append("analyze")
        await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        results["actions"].append("wal_checkpoint")

    if vacuum:
        async with get_connection() as db:
            await db.execute("VACUUM")
        results["actions"].append("vacuum")

    backup_enabled = os.getenv("DB_BACKUP_ON_MAINTENANCE", "false").lower() in {"1", "true", "yes"}
    if backup_enabled and config.DB_PATH.exists():
        backup_dir = config.DATA_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        dest = backup_dir / f"blackdark_{stamp}.db"
        shutil.copy2(config.DB_PATH, dest)
        results["actions"].append({"backup": str(dest)})

    results["finished_at"] = _utcnow_iso()
    health = await database_health_report()
    results["database_size_mb"] = health.get("database_size_mb")
    await insert_maintenance_run(results)
    logger.info("SQLite maintenance complete | size_mb=%s", results.get("database_size_mb"))
    return results
