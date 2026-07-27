"""
BLACKDARK — Multi-Tier Storage Orchestrator.

Tier 0 (Live):     Redis / in-memory live_book_hub — sub-second reads
Tier 1 (Hot 48h):  NDJSON spool + optional TimescaleDB / ClickHouse
Tier 2 (Warm):     Local Parquet (historical_parquet/, history/)
Tier 3 (Cold):     S3 Standard-IA → Glacier (lifecycle policy)
Tier 4 (Ops DB):   SQLite / PostgreSQL — users, signals, config ONLY

Runs compaction, retention enforcement, and acquisition-ready health reporting.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.StorageTier")

_scheduler_task: asyncio.Task | None = None
_compactor_started = False
_running = False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def _mb(size_bytes: int) -> float:
    return round(size_bytes / (1024 * 1024), 2)


async def ensure_hot_pipeline_started() -> bool:
    try:
        from hot_storage import get_hot_pipeline, start_hot_pipeline

        if get_hot_pipeline() is None:
            await start_hot_pipeline()
        return True
    except Exception:
        logger.exception("Hot pipeline startup failed.")
        return False


async def ensure_compaction_scheduler() -> bool:
    global _compactor_started
    if _compactor_started or not config.PARQUET_COMPACTION_ENABLED:
        return _compactor_started
    try:
        from parquet_compactor import start_midnight_compaction_scheduler

        await start_midnight_compaction_scheduler()
        _compactor_started = True
        logger.info(
            "Parquet compaction scheduler active | hot_cutoff_hours=%s",
            config.COMPACTION_MIN_AGE_HOURS,
        )
        return True
    except Exception:
        logger.exception("Parquet compaction scheduler failed to start.")
        return False


def prune_stale_hot_spool_files(*, retention_hours: int | None = None) -> dict[str, Any]:
    """Remove NDJSON spool files older than the hot-tier retention window."""
    hours = retention_hours or config.HOT_TIER_RETENTION_HOURS
    cutoff = _utcnow() - timedelta(hours=hours)
    root = config.HOT_STORAGE_DIR
    removed: list[str] = []
    bytes_freed = 0

    if not root.exists():
        return {"removed_files": 0, "bytes_freed": 0, "cutoff_iso": cutoff.isoformat()}

    for type_dir in root.iterdir():
        if not type_dir.is_dir():
            continue
        for spool_file in type_dir.glob("*.ndjson"):
            try:
                day_str = spool_file.stem
                file_day = datetime.strptime(day_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                file_end = file_day + timedelta(days=1)
                if file_end >= cutoff:
                    continue
                size = spool_file.stat().st_size
                spool_file.unlink(missing_ok=True)
                removed.append(str(spool_file))
                bytes_freed += size
            except (ValueError, OSError):
                continue

    return {
        "removed_files": len(removed),
        "bytes_freed": bytes_freed,
        "mb_freed": _mb(bytes_freed),
        "cutoff_iso": cutoff.isoformat(),
    }


def prune_stale_warm_parquet(*, retention_days: int | None = None) -> dict[str, Any]:
    """Drop local warm Parquet partitions older than retention (after cloud sync)."""
    days = retention_days or config.WARM_PARQUET_LOCAL_RETENTION_DAYS
    cutoff = _utcnow() - timedelta(days=days)
    removed = 0
    bytes_freed = 0

    for root in (config.HISTORICAL_PARQUET_DIR, config.HISTORY_PARQUET_DIR):
        if not root.exists():
            continue
        for parquet_file in root.rglob("*.parquet"):
            try:
                mtime = datetime.fromtimestamp(parquet_file.stat().st_mtime, tz=timezone.utc)
                if mtime >= cutoff:
                    continue
                size = parquet_file.stat().st_size
                parquet_file.unlink(missing_ok=True)
                removed += 1
                bytes_freed += size
            except OSError:
                continue

    return {
        "removed_files": removed,
        "bytes_freed": bytes_freed,
        "mb_freed": _mb(bytes_freed),
        "retention_days": days,
    }


async def enforce_market_data_retention() -> dict[str, int]:
    """Purge legacy market rows from the operational DB (should stay near empty)."""
    from db_upgrade import prune_old_market_rows

    return await prune_old_market_rows(retention_days=config.DB_MARKET_DATA_RETENTION_DAYS)


async def run_hot_tier_compaction_once() -> dict[str, Any]:
    """Compact eligible hot spool + SQLite market data into Parquet."""
    report: dict[str, Any] = {"started_at": _utcnow_iso()}
    try:
        from parquet_compactor import compact_historical_data

        result = await compact_historical_data(min_age_hours=config.COMPACTION_MIN_AGE_HOURS)
        report["partitions_written"] = result.partitions_written
        report["rows_written"] = result.rows_written
        report["rows_purged"] = result.rows_purged
        report["partitions_failed"] = result.partitions_failed
    except Exception as exc:
        report["error"] = str(exc)[:240]
        logger.exception("Hot-tier compaction failed.")
    report["finished_at"] = _utcnow_iso()
    return report


def prune_stale_hot_spool_archive(*, retention_days: int | None = None) -> dict[str, Any]:
    """Remove archived NDJSON after compaction (prevents duplicate storage bloat)."""
    days = retention_days or config.HOT_SPOOL_ARCHIVE_RETENTION_DAYS
    cutoff = _utcnow() - timedelta(days=days)
    root = config.PARQUET_COMPACTION_ARCHIVE_DIR
    removed = 0
    bytes_freed = 0

    if not root.exists():
        return {"removed_files": 0, "bytes_freed": 0, "retention_days": days}

    for archive_file in root.rglob("*.ndjson"):
        try:
            mtime = datetime.fromtimestamp(archive_file.stat().st_mtime, tz=timezone.utc)
            if mtime >= cutoff:
                continue
            size = archive_file.stat().st_size
            archive_file.unlink(missing_ok=True)
            removed += 1
            bytes_freed += size
        except OSError:
            continue

    return {
        "removed_files": removed,
        "bytes_freed": bytes_freed,
        "mb_freed": _mb(bytes_freed),
        "retention_days": days,
    }


async def run_storage_maintenance_cycle() -> dict[str, Any]:
    """Full tier maintenance: compact → prune hot → prune warm → DB purge."""
    cycle: dict[str, Any] = {"timestamp": _utcnow_iso(), "actions": []}

    if config.PARQUET_COMPACTION_ENABLED:
        compaction = await run_hot_tier_compaction_once()
        cycle["actions"].append({"compaction": compaction})

    spool_prune = prune_stale_hot_spool_files()
    cycle["actions"].append({"hot_spool_prune": spool_prune})

    archive_prune = prune_stale_hot_spool_archive()
    cycle["actions"].append({"hot_spool_archive_prune": archive_prune})

    warm_prune = prune_stale_warm_parquet()
    cycle["actions"].append({"warm_parquet_prune": warm_prune})

    try:
        market_purge = await enforce_market_data_retention()
        cycle["actions"].append({"market_db_purge": market_purge})
    except Exception:
        logger.exception("Market data retention purge failed.")

    if config.CLOUD_SYNC_ENABLED:
        try:
            from cloud_syncer import is_cloud_sync_configured, run_cloud_sync_once

            if is_cloud_sync_configured():
                sync_results = await run_cloud_sync_once()
                cycle["actions"].append({"cloud_sync_files": len(sync_results)})
        except Exception:
            logger.exception("Cloud sync during storage maintenance failed.")

    cycle["finished_at"] = _utcnow_iso()
    return cycle


async def storage_architecture_status() -> dict[str, Any]:
    """Acquisition-ready snapshot of the multi-tier storage stack."""
    from db_upgrade import database_health_report, external_database_status
    from hot_storage import get_hot_storage_stats
    from storage_cost_guard import storage_cost_guard_status

    hot_stats = await get_hot_storage_stats()
    db_health = await database_health_report()
    external = external_database_status()

    hot_spool_mb = _mb(_dir_size_bytes(config.HOT_STORAGE_DIR))
    warm_parquet_mb = _mb(_dir_size_bytes(config.HISTORICAL_PARQUET_DIR))
    history_parquet_mb = _mb(_dir_size_bytes(config.HISTORY_PARQUET_DIR))
    archive_mb = _mb(_dir_size_bytes(config.PARQUET_COMPACTION_ARCHIVE_DIR))

    tiers = {
        "tier0_live": {
            "name": "Live (Redis / memory)",
            "purpose": "Sub-second arbitrage & dashboard quotes",
            "retention": "seconds",
            "backend": "redis + live_book_hub",
        },
        "tier1_hot": {
            "name": "Hot time-series",
            "purpose": "Scalping, OBI, 48h analytics",
            "retention_hours": config.HOT_TIER_RETENTION_HOURS,
            "backend": config.HOT_STORAGE_BACKEND,
            "mirror_sqlite": config.HOT_STORAGE_MIRROR_SQLITE,
            "spool_mb": hot_spool_mb,
            "timescale_configured": external.get("timescale_configured"),
            "clickhouse_configured": external.get("clickhouse_configured"),
        },
        "tier2_warm": {
            "name": "Warm Parquet",
            "purpose": "ML retrain, backtests, weekly reports",
            "retention_days": config.WARM_PARQUET_LOCAL_RETENTION_DAYS,
            "historical_parquet_mb": warm_parquet_mb,
            "history_parquet_mb": history_parquet_mb,
            "archive_mb": archive_mb,
        },
        "tier3_cold": {
            "name": "Cold object storage",
            "purpose": "Long-term archive, due diligence exports",
            "cloud_sync_enabled": config.CLOUD_SYNC_ENABLED,
            "s3_bucket": bool(config.AWS_S3_BUCKET),
            "storage_class": config.AWS_S3_STORAGE_CLASS,
            "glacier_transition_days": config.AWS_S3_GLACIER_TRANSITION_DAYS,
        },
        "tier4_ops": {
            "name": "Operational DB",
            "purpose": "Users, signals, oracle scores — NOT raw ticks",
            "engine": external.get("primary"),
            "size_mb": db_health.get("database_size_mb"),
            "market_data_retention_days": config.DB_MARKET_DATA_RETENTION_DAYS,
        },
    }

    compliance = {
        "sqlite_mirror_disabled": not config.HOT_STORAGE_MIRROR_SQLITE,
        "hot_retention_48h": config.HOT_TIER_RETENTION_HOURS <= 48,
        "compaction_enabled": config.PARQUET_COMPACTION_ENABLED,
        "compaction_cutoff_hours": config.COMPACTION_MIN_AGE_HOURS,
        "storage_tier_auto": config.STORAGE_TIER_AUTO,
        "acquisition_ready": (
            not config.HOT_STORAGE_MIRROR_SQLITE
            and config.HOT_TIER_RETENTION_HOURS <= 48
            and config.PARQUET_COMPACTION_ENABLED
        ),
    }

    issues: list[str] = []
    if config.HOT_STORAGE_MIRROR_SQLITE:
        issues.append("CRITICAL: HOT_STORAGE_MIRROR_SQLITE=true — ticks duplicated in SQLite.")
    if (db_health.get("database_size_mb") or 0) > 500:
        issues.append("WARNING: Operational DB >500MB — run maintenance/compaction.")
    if not config.PARQUET_COMPACTION_ENABLED:
        issues.append("WARNING: Parquet compaction disabled — cold tier won't populate.")
    if config.HOT_TIER_RETENTION_HOURS > 48:
        issues.append("WARNING: Hot retention exceeds 48h scalping window.")
    cost = storage_cost_guard_status()
    if cost.get("archive_order_books"):
        issues.append("WARNING: Order book archival enabled — high S3/ClickHouse cost at scale.")
    if cost.get("archive_ticks"):
        issues.append("WARNING: Raw tick archival enabled — can exceed terabytes/week at 100 venues.")
    if (cost.get("weekly_estimate") or {}).get("estimated_hot_gb_per_week", 0) > 50:
        issues.append("WARNING: Estimated weekly hot-tier volume >50 GB — review throttle settings.")

    return {
        "timestamp": _utcnow_iso(),
        "architecture": "multi_tier",
        "tiers": tiers,
        "hot_pipeline": hot_stats.model_dump() if hasattr(hot_stats, "model_dump") else hot_stats,
        "cost_guard": cost,
        "database": db_health,
        "compliance": compliance,
        "issues": issues or ["No critical storage issues detected."],
        "documentation": "STORAGE_ARCHITECTURE.md",
    }


async def _maintenance_loop() -> None:
    interval_hours = max(1, config.STORAGE_TIER_MAINTENANCE_INTERVAL_HOURS)
    logger.info(
        "Storage tier maintenance loop started | interval_hours=%s retention_hot=%sh",
        interval_hours,
        config.HOT_TIER_RETENTION_HOURS,
    )
    while _running:
        try:
            result = await run_storage_maintenance_cycle()
            logger.info(
                "Storage maintenance cycle complete | actions=%s",
                len(result.get("actions") or []),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Storage tier maintenance cycle failed.")
        await asyncio.sleep(interval_hours * 3600)


async def _maybe_legacy_db_cleanup() -> None:
    """One-shot purge of legacy pricing_logs when ops DB is bloated."""
    try:
        from database import fetch_system_telemetry

        telemetry = await fetch_system_telemetry()
        pricing_count = int(telemetry.get("pricing_count") or 0)
        size_mb = round((telemetry.get("database_size_bytes") or 0) / (1024 * 1024), 2)
        if pricing_count < 50_000 and size_mb < 200:
            return
        logger.info(
            "Legacy DB cleanup starting | pricing_rows=%s size_mb=%s",
            pricing_count,
            size_mb,
        )
        result = await run_storage_maintenance_cycle()
        logger.info("Legacy DB cleanup finished | actions=%s", len(result.get("actions") or []))
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Legacy DB cleanup failed.")


async def start_storage_tier_manager() -> None:
    """Bootstrap hot pipeline, compaction scheduler, and maintenance loop."""
    global _scheduler_task, _running
    if _running:
        return
    _running = True

    await ensure_hot_pipeline_started()
    await ensure_compaction_scheduler()

    if config.STORAGE_TIER_AUTO:
        asyncio.create_task(_maybe_legacy_db_cleanup(), name="legacy-db-cleanup")
        _scheduler_task = asyncio.create_task(
            _maintenance_loop(),
            name="storage-tier-maintenance",
        )
        logger.info("Storage tier manager started (STORAGE_TIER_AUTO=true).")


async def purge_legacy_ops_market_data(*, vacuum: bool = True) -> dict[str, Any]:
    """
    One-time cleanup: remove tick data from operational SQLite.

    Safe after HOT_STORAGE_MIRROR_SQLITE=false — ticks live in hot_spool/Parquet.
    """
    from database import get_connection

    result: dict[str, Any] = {"timestamp": _utcnow_iso(), "deleted": {}}
    async with get_connection() as db:
        for table in ("pricing_logs", "order_books"):
            cursor = await db.execute(f"DELETE FROM {table}")
            result["deleted"][table] = int(cursor.rowcount or 0)
        if vacuum:
            await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    if vacuum:
        async with get_connection() as db:
            await db.execute("VACUUM")
        result["vacuum"] = True

    from db_upgrade import database_health_report

    health = await database_health_report()
    result["database_size_mb_after"] = health.get("database_size_mb")
    result["note"] = "Operational DB cleaned — hot/cold tiers unchanged."
    logger.info(
        "Legacy ops market data purged | deleted=%s size_mb=%s",
        result["deleted"],
        result.get("database_size_mb_after"),
    )
    return result


async def stop_storage_tier_manager() -> None:
    global _scheduler_task, _running, _compactor_started
    _running = False

    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None

    if _compactor_started:
        try:
            from parquet_compactor import stop_midnight_compaction_scheduler

            await stop_midnight_compaction_scheduler()
        except Exception:
            logger.exception("Failed to stop parquet compaction scheduler.")
        _compactor_started = False

    try:
        from hot_storage import shutdown_hot_pipeline

        await shutdown_hot_pipeline()
    except Exception:
        logger.exception("Hot pipeline shutdown failed.")
