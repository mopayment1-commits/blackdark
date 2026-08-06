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
from types import SimpleNamespace
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
    uptime_probe_task: asyncio.Task | None = None
    glass_box_task: asyncio.Task | None = None
    extras: dict[str, Any] = field(default_factory=dict)


async def run_background_startup(state: RuntimeState) -> None:
    """Start all non-critical services after HTTP is already live."""
    try:
        from bd_platform.auto_keys import apply_keys_to_process_env

        applied = apply_keys_to_process_env()
        if applied:
            logger.info("Platform keys loaded from keys/platform_keys.env (%s)", applied)
    except Exception:
        logger.debug("Platform auto-keys skip", exc_info=True)

    if os.getenv("UNIVERSE_AUTO_ACTIVATE", "false").lower() in {"1", "true", "yes"}:
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

    try:
        from execution_keys import apply_exchange_keys_to_env

        applied_exec = apply_exchange_keys_to_env()
        if applied_exec:
            logger.info("Exchange keys loaded from keys/exchange_keys.env (%s)", applied_exec)
    except Exception:
        logger.debug("Exchange keys auto-load skip", exc_info=True)

    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    run_agg = os.getenv("RUN_AGGREGATOR", "true").lower() in {"1", "true", "yes"}
    if config.PRICE_FEED_WS_ONLY:
        run_agg = os.getenv("RUN_AGGREGATOR", "false").lower() in {"1", "true", "yes"}
    if run_agg:
        os.environ.setdefault("MANIFEST_AUTO_APPROVE", "true")
        os.environ.setdefault("MANIFEST_REQUIRE_REVIEW", "false")

        async def _aggregator_wrapper() -> None:
            try:
                from aggregator import run_aggregator

                await run_aggregator()
            except asyncio.CancelledError:
                logger.info("Aggregator background task cancelled.")
            except Exception:
                logger.exception("Aggregator background task failed.")

        state.aggregator_task = asyncio.create_task(_aggregator_wrapper())
        logger.info("Aggregator background task started (RUN_AGGREGATOR=true).")

    from telegram_monitor import start_telegram_monitor

    state.telegram_task = await start_telegram_monitor()
    from telegram_bot_poller import start_telegram_poller

    state.telegram_poller_task = await start_telegram_poller()

    from instant_alert_engine import start_instant_alert_engine

    state.instant_alert_task = await start_instant_alert_engine()

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

    from gas_oracle import start_gas_oracle_loop
    from fee_matrix import start_fee_matrix_scheduler

    await start_gas_oracle_loop()
    await start_fee_matrix_scheduler()

    if config.STORAGE_TIER_AUTO:
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

    run_ingestion = os.getenv("INGESTION_ENABLED", "true").lower() in {"1", "true", "yes"}
    if config.PRICE_FEED_WS_ONLY:
        run_ingestion = os.getenv("INGESTION_ENABLED", "false").lower() in {"1", "true", "yes"}
    if run_ingestion:

        async def _ingestion_wrapper() -> None:
            try:
                from ingestion_scheduler import start_ingestion_scheduler

                bootstrap = os.getenv("INGESTION_BOOTSTRAP_ON_START", "false").lower() in {
                    "1",
                    "true",
                    "yes",
                }
                await start_ingestion_scheduler(bootstrap=bootstrap)
            except asyncio.CancelledError:
                logger.info("Ingestion scheduler cancelled.")
            except Exception:
                logger.exception("Ingestion scheduler failed.")

        state.ingestion_task = asyncio.create_task(_ingestion_wrapper())
        logger.info("Ingestion scheduler task started (INGESTION_ENABLED=true).")

    if os.getenv("FORECAST_ENABLED", "true").lower() in {"1", "true", "yes"}:

        async def _forecast_audit_loop() -> None:
            interval = max(300, int(os.getenv("FORECAST_AUDIT_INTERVAL_SEC", "3600")))
            while True:
                try:
                    from forecast_engine import run_forecast_audit

                    audit = await run_forecast_audit()
                    from ml.labeling_pipeline import resolve_mature_predictions

                    oracle_resolved = await resolve_mature_predictions()
                    oracle_resolved_count = (oracle_resolved or {}).get("resolved_24h", 0)
                    retrain_result = None
                    if os.getenv("ORACLE_RETRAIN_ENABLED", "true").lower() in {"1", "true", "yes"}:
                        from oracle_retrainer import run_oracle_retrain_step

                        retrain_result = await run_oracle_retrain_step()
                    if audit.get("resolved") or oracle_resolved_count or (retrain_result or {}).get("adjusted"):
                        logger.info(
                            "Forecast/oracle audit | forecasts_resolved=%s oracle_resolved=%s retrain=%s",
                            audit.get("resolved", 0),
                            oracle_resolved_count,
                            (retrain_result or {}).get("adjusted"),
                        )
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Forecast audit loop failed.")
                await asyncio.sleep(interval)

        state.forecast_audit_task = asyncio.create_task(_forecast_audit_loop())
        logger.info("Forecast audit loop started (FORECAST_ENABLED=true).")

    if config.ML_FLYWHEEL_ENABLED:
        from ml_flywheel_scheduler import start_ml_flywheel

        await start_ml_flywheel()
        state.ml_flywheel_started = True
        logger.info("ML flywheel started (ML_FLYWHEEL_ENABLED=true).")

    # Glass Box auto-seal cadence (product loop; announce timing remains human H2)
    if os.getenv("GLASS_BOX_AUTO_SEAL", "true").lower() in {"1", "true", "yes"}:
        async def _glass_box_seal_loop() -> None:
            import asyncio

            # First seal shortly after boot, then daily
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

        state.glass_box_task = asyncio.create_task(_glass_box_seal_loop())
        logger.info("Glass Box auto-seal cadence started.")

    if os.getenv("WEEKLY_REPORT_AUTO", "false").lower() in {"1", "true", "yes"}:

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

        state.weekly_report_task = asyncio.create_task(_weekly_report_loop())
        logger.info("Weekly report scheduler started.")

    if os.getenv("DAILY_REPORT_AUTO", "false").lower() in {"1", "true", "yes"}:

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

        state.daily_report_task = asyncio.create_task(_daily_report_loop())
        logger.info("Daily report scheduler started.")

    if os.getenv("AUTO_EXECUTION_LOOP", "false").lower() in {"1", "true", "yes"}:
        from execution_engine import start_auto_execution_loop

        state.auto_exec_task = await start_auto_execution_loop()

    if os.getenv("DB_MAINTENANCE_AUTO", "false").lower() in {"1", "true", "yes"}:

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

        state.db_maintenance_task = asyncio.create_task(_db_maintenance_loop())
        logger.info("DB maintenance scheduler started.")

    if os.getenv("CLOUD_SYNC_ENABLED", "false").lower() in {"1", "true", "yes"}:

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

        state.cloud_sync_task = asyncio.create_task(_cloud_sync_loop())
        logger.info("Cloud sync scheduler started (CLOUD_SYNC_ENABLED=true).")

    try:
        from uptime_probe_loop import start_uptime_probe_loop

        state.uptime_probe_task = await start_uptime_probe_loop()
    except Exception:
        logger.exception("Uptime self-probe loop failed to start")

    logger.info("BLACKDARK background startup complete.")


async def shutdown_runtime(state: RuntimeState) -> None:
    if state.ml_flywheel_started:
        from ml_flywheel_scheduler import stop_ml_flywheel

        await stop_ml_flywheel()

    from instant_alert_engine import stop_instant_alert_engine

    await stop_instant_alert_engine()

    from b2b_websocket_hub import stop_b2b_websocket_hub

    await stop_b2b_websocket_hub()

    from exchange_ws_hub import stop_exchange_ws_hub

    await stop_exchange_ws_hub()

    from price_stream_engine import stop_stream_processor

    await stop_stream_processor()

    from gas_oracle import stop_gas_oracle_loop
    from fee_matrix import stop_fee_matrix_scheduler

    await stop_gas_oracle_loop()
    await stop_fee_matrix_scheduler()

    if config.STORAGE_TIER_AUTO:
        try:
            from storage_tier_manager import stop_storage_tier_manager

            await stop_storage_tier_manager()
        except Exception:
            logger.exception("Storage tier manager shutdown failed.")

    for task in (
        state.uptime_probe_task,
        state.cloud_sync_task,
        state.db_maintenance_task,
        state.weekly_report_task,
        state.daily_report_task,
        state.forecast_audit_task,
    ):
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    if state.auto_exec_task is not None:
        from execution_engine import stop_auto_execution_loop

        await stop_auto_execution_loop()

    if state.ingestion_task is not None:
        from ingestion_scheduler import stop_ingestion_scheduler

        await stop_ingestion_scheduler()
        state.ingestion_task.cancel()
        try:
            await state.ingestion_task
        except asyncio.CancelledError:
            pass

    if state.telegram_task is not None:
        from telegram_monitor import stop_telegram_monitor

        await stop_telegram_monitor()

    if state.telegram_poller_task is not None:
        from telegram_bot_poller import stop_telegram_poller

        await stop_telegram_poller()

    if state.aggregator_task is not None:
        state.aggregator_task.cancel()
        try:
            await state.aggregator_task
        except asyncio.CancelledError:
            pass
