"""
BLACKDARK — Background service startup/shutdown.

HTTP server binds immediately; heavy services (WS, Kafka, fee matrix, storage)
load in background so /dashboard and /api/* respond within seconds.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.Startup")


@dataclass
class RuntimeState:
    aggregator_task: asyncio.Task | None = None
    telegram_task: asyncio.Task | None = None
    telegram_poller_task: asyncio.Task | None = None
    instant_alert_task: asyncio.Task | None = None
    ingestion_task: asyncio.Task | None = None
    forecast_audit_task: asyncio.Task | None = None
    weekly_report_task: asyncio.Task | None = None
    daily_report_task: asyncio.Task | None = None
    auto_exec_task: asyncio.Task | None = None
    db_maintenance_task: asyncio.Task | None = None
    cloud_sync_task: asyncio.Task | None = None
    ml_flywheel_started: bool = False
    billing_sweeper_started: bool = False
    uptime_probe_task: asyncio.Task | None = None
    glass_box_task: asyncio.Task | None = None
    extras: dict[str, Any] = field(default_factory=dict)


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def _load_platform_keys() -> None:
    try:
        from bd_platform.auto_keys import apply_keys_to_process_env

        applied = apply_keys_to_process_env()
        if applied:
            logger.info("Platform keys loaded from keys/platform_keys.env (%s)", applied)
    except Exception:
        logger.debug("Platform auto-keys skip", exc_info=True)


def _maybe_activate_universe() -> None:
    if not _env_flag("UNIVERSE_AUTO_ACTIVATE", "false"):
        return
    try:
        from universe_rollout import activate_full_universe

        rollout = activate_full_universe(save=True)
        logger.info(
            "Universe rollout | exchanges=%s assets=%s",
            rollout.get("exchanges"),
            rollout.get("assets"),
        )
    except Exception:
        logger.exception("Universe auto-activate failed")


def _load_exchange_keys() -> None:
    try:
        from execution_keys import apply_exchange_keys_to_env

        applied_exec = apply_exchange_keys_to_env()
        if applied_exec:
            logger.info("Exchange keys loaded from keys/exchange_keys.env (%s)", applied_exec)
    except Exception:
        logger.debug("Exchange keys auto-load skip", exc_info=True)


def _configure_stripe() -> None:
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


def _should_run_aggregator() -> bool:
    default = "false" if config.PRICE_FEED_WS_ONLY else "true"
    return _env_flag("RUN_AGGREGATOR", default)


async def _aggregator_wrapper() -> None:
    try:
        from aggregator import run_aggregator

        await run_aggregator()
    except asyncio.CancelledError:
        logger.info("Aggregator background task cancelled.")
        raise
    except Exception:
        logger.exception("Aggregator background task failed.")


def _start_aggregator(state: RuntimeState) -> None:
    if not _should_run_aggregator():
        return
    os.environ.setdefault("MANIFEST_AUTO_APPROVE", "true")
    os.environ.setdefault("MANIFEST_REQUIRE_REVIEW", "false")
    state.aggregator_task = asyncio.create_task(_aggregator_wrapper())
    logger.info("Aggregator background task started (RUN_AGGREGATOR=true).")


async def _start_core_streams(state: RuntimeState) -> None:
    from telegram_monitor import start_telegram_monitor

    state.telegram_task = start_telegram_monitor()
    from telegram_bot_poller import start_telegram_poller

    state.telegram_poller_task = start_telegram_poller()

    from instant_alert_engine import start_instant_alert_engine

    state.instant_alert_task = start_instant_alert_engine()

    from b2b_websocket_hub import start_b2b_websocket_hub

    await start_b2b_websocket_hub()

    from exchange_ws_hub import start_exchange_ws_hub

    await start_exchange_ws_hub()

    from price_stream_engine import start_stream_processor

    await start_stream_processor()
    logger.info(
        "Price stream engine started | ws_only=%s redis=%s kafka=%s",
        config.PRICE_FEED_WS_ONLY,
        config.REDIS_PRICE_CACHE_ENABLED,
        config.KAFKA_PRICE_STREAM_ENABLED,
    )


async def _start_fee_and_gas() -> None:
    await asyncio.sleep(0)
    from fee_matrix import start_fee_matrix_scheduler
    from gas_oracle import start_gas_oracle_loop

    start_gas_oracle_loop()
    start_fee_matrix_scheduler()


async def _start_storage_tier() -> None:
    if not config.STORAGE_TIER_AUTO:
        return
    try:
        from storage_tier_manager import start_storage_tier_manager

        await start_storage_tier_manager()
        logger.info(
            "Multi-tier storage manager started | hot_retention=%sh mirror_sqlite=%s",
            config.HOT_TIER_RETENTION_HOURS,
            config.HOT_STORAGE_MIRROR_SQLITE,
        )
    except Exception:
        logger.exception("Storage tier manager failed to start.")


def _should_run_ingestion() -> bool:
    default = "false" if config.PRICE_FEED_WS_ONLY else "true"
    return _env_flag("INGESTION_ENABLED", default)


async def _ingestion_wrapper() -> None:
    try:
        from ingestion_scheduler import start_ingestion_scheduler

        bootstrap = _env_flag("INGESTION_BOOTSTRAP_ON_START", "false")
        await start_ingestion_scheduler(bootstrap=bootstrap)
    except asyncio.CancelledError:
        logger.info("Ingestion scheduler cancelled.")
        raise
    except Exception:
        logger.exception("Ingestion scheduler failed.")


def _start_ingestion(state: RuntimeState) -> None:
    if not _should_run_ingestion():
        return
    state.ingestion_task = asyncio.create_task(_ingestion_wrapper())
    logger.info("Ingestion scheduler task started (INGESTION_ENABLED=true).")


async def _forecast_audit_loop() -> None:
    interval = max(300, int(os.getenv("FORECAST_AUDIT_INTERVAL_SEC", "3600")))
    while True:
        try:
            await _run_forecast_audit_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Forecast audit loop failed.")
        await asyncio.sleep(interval)


async def _run_forecast_audit_once() -> None:
    from forecast_engine import run_forecast_audit

    audit = await run_forecast_audit()
    from ml.labeling_pipeline import resolve_mature_predictions

    oracle_resolved = await resolve_mature_predictions()
    oracle_resolved_count = (oracle_resolved or {}).get("resolved_24h", 0)
    retrain_result = await _maybe_oracle_retrain()
    if audit.get("resolved") or oracle_resolved_count or (retrain_result or {}).get("adjusted"):
        logger.info(
            "Forecast/oracle audit | forecasts_resolved=%s oracle_resolved=%s retrain=%s",
            audit.get("resolved", 0),
            oracle_resolved_count,
            (retrain_result or {}).get("adjusted"),
        )


async def _maybe_oracle_retrain() -> dict[str, Any] | None:
    if not _env_flag("ORACLE_RETRAIN_ENABLED", "true"):
        return None
    from oracle_retrainer import run_oracle_retrain_step

    return await run_oracle_retrain_step()


def _start_forecast_audit(state: RuntimeState) -> None:
    if not _env_flag("FORECAST_ENABLED", "true"):
        return
    state.forecast_audit_task = asyncio.create_task(_forecast_audit_loop())
    logger.info("Forecast audit loop started (FORECAST_ENABLED=true).")


async def _start_ml_flywheel(state: RuntimeState) -> None:
    await asyncio.sleep(0)
    if not config.ML_FLYWHEEL_ENABLED:
        return
    from ml_flywheel_scheduler import start_ml_flywheel

    start_ml_flywheel()
    state.ml_flywheel_started = True
    logger.info("ML flywheel started (ML_FLYWHEEL_ENABLED=true).")


async def _glass_box_seal_loop() -> None:
    await asyncio.sleep(45)
    while True:
        try:
            from locked_predictions import maybe_auto_seal_from_oracle

            result = await maybe_auto_seal_from_oracle()
            logger.info(
                "Glass Box auto-seal | sealed=%s skipped=%s",
                result.get("sealed"),
                result.get("skipped"),
            )
        except Exception:
            logger.exception("Glass Box auto-seal failed")
        await asyncio.sleep(float(os.getenv("GLASS_BOX_AUTO_SEAL_SEC", str(24 * 3600))))


def _start_glass_box(state: RuntimeState) -> None:
    if not _env_flag("GLASS_BOX_AUTO_SEAL", "true"):
        return
    state.glass_box_task = asyncio.create_task(_glass_box_seal_loop())
    logger.info("Glass Box auto-seal cadence started.")


async def _weekly_report_loop() -> None:
    interval_hours = max(24, int(os.getenv("WEEKLY_REPORT_INTERVAL_HOURS", "168")))
    while True:
        try:
            from weekly_report import build_weekly_report

            report = await build_weekly_report(persist=True)
            logger.info("Weekly report generated | id=%s", report.get("report_id"))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Weekly report auto-generation failed.")
        await asyncio.sleep(interval_hours * 3600)


def _start_weekly_report(state: RuntimeState) -> None:
    if not _env_flag("WEEKLY_REPORT_AUTO", "false"):
        return
    state.weekly_report_task = asyncio.create_task(_weekly_report_loop())
    logger.info("Weekly report scheduler started.")


async def _daily_report_loop() -> None:
    interval_hours = max(12, int(os.getenv("DAILY_REPORT_INTERVAL_HOURS", "24")))
    while True:
        try:
            from daily_report import build_daily_report

            report = await build_daily_report(persist=True)
            logger.info("Daily report generated | id=%s", report.get("report_id"))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Daily report auto-generation failed.")
        await asyncio.sleep(interval_hours * 3600)


def _start_daily_report(state: RuntimeState) -> None:
    if not _env_flag("DAILY_REPORT_AUTO", "false"):
        return
    state.daily_report_task = asyncio.create_task(_daily_report_loop())
    logger.info("Daily report scheduler started.")


async def _start_auto_execution(state: RuntimeState) -> None:
    await asyncio.sleep(0)
    if not _env_flag("AUTO_EXECUTION_LOOP", "false"):
        return
    from execution_engine import start_auto_execution_loop

    state.auto_exec_task = start_auto_execution_loop()


async def _db_maintenance_loop() -> None:
    interval_hours = max(6, int(os.getenv("DB_MAINTENANCE_INTERVAL_HOURS", "24")))
    while True:
        try:
            from db_upgrade import run_sqlite_maintenance

            await run_sqlite_maintenance(vacuum=False)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("DB maintenance loop failed.")
        await asyncio.sleep(interval_hours * 3600)


def _start_db_maintenance(state: RuntimeState) -> None:
    if not _env_flag("DB_MAINTENANCE_AUTO", "false"):
        return
    state.db_maintenance_task = asyncio.create_task(_db_maintenance_loop())
    logger.info("DB maintenance scheduler started.")


async def _cloud_sync_loop() -> None:
    interval_hours = max(1, int(os.getenv("CLOUD_SYNC_INTERVAL_HOURS", "6")))
    while True:
        try:
            from cloud_syncer import is_cloud_sync_configured, run_cloud_sync_once

            if is_cloud_sync_configured():
                results = await run_cloud_sync_once()
                logger.info("Cloud sync batch finished | files=%d", len(results))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Cloud sync loop failed.")
        await asyncio.sleep(interval_hours * 3600)


def _start_cloud_sync(state: RuntimeState) -> None:
    if not _env_flag("CLOUD_SYNC_ENABLED", "false"):
        return
    state.cloud_sync_task = asyncio.create_task(_cloud_sync_loop())
    logger.info("Cloud sync scheduler started (CLOUD_SYNC_ENABLED=true).")


async def _bigquery_export_bootstrap() -> None:
    if not _env_flag("BIGQUERY_EXPORT_ENABLED", "true"):
        return
    try:
        from bigquery_export import (
            bigquery_configured,
            bigquery_live_ready,
            export_ingestion_snapshots_to_bigquery,
            _write_bootstrap_status,
        )
        from database import fetch_ingestion_snapshots_for_export

        if not bigquery_configured() or bigquery_live_ready():
            return
        from bigquery_export import _write_bootstrap_status

        _write_bootstrap_status({"status": "running"})
        wait_sec = int(os.getenv("BIGQUERY_BOOTSTRAP_DELAY_SEC", "15"))
        if wait_sec > 0:
            await asyncio.sleep(wait_sec)

        snapshots = await fetch_ingestion_snapshots_for_export(limit=1)
        if not snapshots:
            try:
                import aiohttp

                from ingestion_fetchers import ingest_category

                logger.info("BigQuery bootstrap — running minimal prices ingest for lake rows")
                timeout = aiohttp.ClientTimeout(total=config.INGESTION_FETCH_TIMEOUT_SECONDS)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    await ingest_category(session, "prices")  # type: ignore[arg-type]
                await asyncio.sleep(int(os.getenv("BIGQUERY_POST_INGESTION_DELAY_SEC", "10")))
            except Exception:
                logger.exception("Minimal ingestion bootstrap before BigQuery export failed")

        evidence = await export_ingestion_snapshots_to_bigquery(operator="startup_bootstrap")
        _write_bootstrap_status({"status": "ok", "export_id": evidence.get("export_id"), "rows_verified": evidence.get("rows_verified")})
        logger.info(
            "BigQuery bootstrap export complete | export_id=%s rows=%s table=%s",
            evidence.get("export_id"),
            evidence.get("rows_verified"),
            evidence.get("table_fqn"),
        )
    except RuntimeError as exc:
        _write_bootstrap_status({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        if str(exc) == "no_ingestion_snapshots_to_export":
            logger.warning("BigQuery bootstrap skipped — no ingestion snapshots yet")
        else:
            logger.warning("BigQuery bootstrap export deferred: %s", exc)
    except Exception as exc:
        diag: dict[str, Any] | None = None
        try:
            from bigquery_export import _bigquery_diagnostics, _build_client

            diag = _bigquery_diagnostics(_build_client())
        except Exception:
            diag = None
        payload: dict[str, Any] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        if diag:
            payload["diagnostics"] = diag
        _write_bootstrap_status(payload)
        logger.exception("BigQuery bootstrap export failed")


def _start_bigquery_export_bootstrap(state: RuntimeState) -> None:
    """Legacy hook retained for tests; export now runs awaited in run_background_startup."""
    _ = state


async def _start_uptime_probe(state: RuntimeState) -> None:
    await asyncio.sleep(0)
    try:
        from uptime_probe_loop import start_uptime_probe_loop

        state.uptime_probe_task = start_uptime_probe_loop()
    except Exception:
        logger.exception("Uptime self-probe loop failed to start")


async def run_background_startup(state: RuntimeState) -> None:
    """Start all non-critical services after HTTP is already live."""
    _load_platform_keys()
    _maybe_activate_universe()
    _load_exchange_keys()
    _configure_stripe()
    _start_aggregator(state)
    await _start_core_streams(state)
    await _start_fee_and_gas()
    await _start_storage_tier()
    _start_ingestion(state)
    await _maybe_run_bigquery_export_bootstrap()
    await _maybe_run_dbt_bootstrap()
    _start_forecast_audit(state)
    await _start_ml_flywheel(state)
    _start_glass_box(state)
    _start_weekly_report(state)
    _start_daily_report(state)
    await _start_auto_execution(state)
    _start_db_maintenance(state)
    _start_cloud_sync(state)
    await _start_uptime_probe(state)
    _start_billing_sweeper(state)
    await _start_data_engine(state)
    logger.info("BLACKDARK background startup complete.")


async def _start_data_engine(state: RuntimeState) -> None:
    if not _env_flag("DATA_ENGINE_ENABLED", "true"):
        return
    try:
        from blackdark.data.jobs import bootstrap_data_engine, start_data_engine_jobs

        boot = await bootstrap_data_engine()
        if boot.get("ok"):
            state.extras["data_engine_jobs"] = start_data_engine_jobs()
            logger.info("Wave 01 data engine bootstrapped | %s", boot)
    except Exception:
        logger.exception("Wave 01 data engine startup failed")


async def _maybe_run_dbt_bootstrap() -> None:
    if not _env_flag("DBT_RUN_ENABLED", "true"):
        return
    try:
        from bigquery_export import bigquery_live_ready
        from dbt_connector import dbt_configured, dbt_live_ready, run_dbt_pipeline, _write_bootstrap_status

        if not dbt_configured() or not bigquery_live_ready() or dbt_live_ready():
            return
        _write_bootstrap_status({"status": "running"})
        wait_sec = int(os.getenv("DBT_BOOTSTRAP_DELAY_SEC", "20"))
        if wait_sec > 0:
            await asyncio.sleep(wait_sec)
        evidence = await run_dbt_pipeline(operator="startup_bootstrap")
        _write_bootstrap_status(
            {
                "status": "ok",
                "run_id": evidence.get("run_id"),
                "mart_rows_verified": evidence.get("mart_rows_verified"),
            }
        )
        logger.info(
            "dbt bootstrap complete | run_id=%s mart_rows=%s",
            evidence.get("run_id"),
            evidence.get("mart_rows_verified"),
        )
    except RuntimeError as exc:
        from dbt_connector import _write_bootstrap_status

        _write_bootstrap_status({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        logger.warning("dbt bootstrap deferred: %s", exc)
    except Exception as exc:
        from dbt_connector import _write_bootstrap_status

        _write_bootstrap_status({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        logger.exception("CAP-649 dbt bootstrap failed")


async def _maybe_run_bigquery_export_bootstrap() -> None:
    if not _env_flag("BIGQUERY_EXPORT_ENABLED", "true"):
        return
    try:
        from bigquery_export import bigquery_configured, bigquery_live_ready

        if bigquery_configured() and not bigquery_live_ready():
            await _bigquery_export_bootstrap()
    except Exception:
        logger.exception("CAP-658 awaited BigQuery bootstrap export failed")


def _start_billing_sweeper(state: RuntimeState) -> None:
    try:
        from billing.sweeper import start_billing_sweeper

        start_billing_sweeper()
        state.billing_sweeper_started = True
    except Exception:
        logger.exception("Billing sweeper failed to start")


async def _stop_ml_flywheel(state: RuntimeState) -> None:
    if not state.ml_flywheel_started:
        return
    from ml_flywheel_scheduler import stop_ml_flywheel

    await stop_ml_flywheel()


async def _stop_storage_tier() -> None:
    if not config.STORAGE_TIER_AUTO:
        return
    try:
        from storage_tier_manager import stop_storage_tier_manager

        await stop_storage_tier_manager()
    except Exception:
        logger.exception("Storage tier manager shutdown failed.")


async def _cancel_tasks(*tasks: asyncio.Task | None) -> None:
    for task in tasks:
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def shutdown_runtime(state: RuntimeState) -> None:
    await _stop_ml_flywheel(state)

    from instant_alert_engine import stop_instant_alert_engine

    await stop_instant_alert_engine()

    from b2b_websocket_hub import stop_b2b_websocket_hub

    await stop_b2b_websocket_hub()

    from exchange_ws_hub import stop_exchange_ws_hub

    await stop_exchange_ws_hub()

    from price_stream_engine import stop_stream_processor

    await stop_stream_processor()

    from fee_matrix import stop_fee_matrix_scheduler
    from gas_oracle import stop_gas_oracle_loop

    await stop_gas_oracle_loop()
    await stop_fee_matrix_scheduler()
    await _stop_storage_tier()

    await _cancel_tasks(
        state.uptime_probe_task,
        state.cloud_sync_task,
        state.db_maintenance_task,
        state.weekly_report_task,
        state.daily_report_task,
        state.forecast_audit_task,
    )

    if state.auto_exec_task is not None:
        from execution_engine import stop_auto_execution_loop

        await stop_auto_execution_loop()

    if state.ingestion_task is not None:
        from ingestion_scheduler import stop_ingestion_scheduler

        await stop_ingestion_scheduler()
        state.ingestion_task.cancel()
        await asyncio.gather(state.ingestion_task, return_exceptions=True)

    if state.telegram_task is not None:
        from telegram_monitor import stop_telegram_monitor

        await stop_telegram_monitor()

    if state.telegram_poller_task is not None:
        from telegram_bot_poller import stop_telegram_poller

        await stop_telegram_poller()

    if state.aggregator_task is not None:
        state.aggregator_task.cancel()
        await asyncio.gather(state.aggregator_task, return_exceptions=True)
