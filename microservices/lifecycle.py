"""
BLACKDARK — Microservice lifecycle (boot / shutdown per SERVICE_MODE).

Modes:
  web         — API + UI + B2B WebSocket (no heavy ingestion loops)
  aggregator  — market polling + exchange WS + hot storage
  arbitrage   — scan + alerts + auto-execution + low latency
  ingestion   — news/macro/data lake ingestion scheduler
  all         — monolith (legacy single-process)
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.Microservices")

VALID_MODES = frozenset({"web", "aggregator", "arbitrage", "ingestion", "all"})


@dataclass
class ServiceContext:
    mode: str = "all"
    tasks: dict[str, asyncio.Task | None] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)


def current_mode() -> str:
    mode = os.getenv("SERVICE_MODE", getattr(config, "SERVICE_MODE", "all")).strip().lower()
    return mode if mode in VALID_MODES else "all"


async def startup(mode: str | None = None, ctx: ServiceContext | None = None) -> ServiceContext:
    from database import init_db
    from service_bus import start_service_bus

    ctx = ctx or ServiceContext()
    ctx.mode = mode or current_mode()
    await init_db()
    await start_service_bus()

    try:
        from bd_platform.kafka_bridge import start_kafka_consumer

        await start_kafka_consumer()
        ctx.flags["kafka_consumer"] = True
    except Exception:
        logger.debug("Kafka consumer not started.")

    if ctx.mode == "web":
        await _boot_web(ctx)
    elif ctx.mode == "aggregator":
        await _boot_aggregator(ctx)
    elif ctx.mode == "arbitrage":
        await _boot_arbitrage(ctx)
    elif ctx.mode == "ingestion":
        _boot_ingestion(ctx)
    else:
        logger.info("SERVICE_MODE=all — use dashboard monolith lifespan.")

    logger.info("Microservice started | mode=%s tasks=%s", ctx.mode, list(ctx.tasks.keys()))
    return ctx


async def shutdown(ctx: ServiceContext) -> None:
    from service_bus import stop_service_bus

    for name, task in tuple(ctx.tasks.items()):
        if task is None:
            continue
        if name == "aggregator":
            task.cancel()
        elif name == "ingestion":
            from ingestion_scheduler import stop_ingestion_scheduler

            await stop_ingestion_scheduler()
            task.cancel()
        elif name == "telegram":
            from telegram_monitor import stop_telegram_monitor

            await stop_telegram_monitor()
        elif name == "telegram_poller":
            from telegram_bot_poller import stop_telegram_poller

            await stop_telegram_poller()
        elif name == "instant_alerts":
            from instant_alert_engine import stop_instant_alert_engine

            await stop_instant_alert_engine()
        elif name == "auto_exec":
            from execution_engine import stop_auto_execution_loop

            await stop_auto_execution_loop()
        elif name == "ml_flywheel":
            from ml_flywheel_scheduler import stop_ml_flywheel

            await stop_ml_flywheel()
        elif name == "forecast_audit":
            task.cancel()
        else:
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    if ctx.flags.get("b2b_ws"):
        from b2b_websocket_hub import stop_b2b_websocket_hub

        await stop_b2b_websocket_hub()
    if ctx.flags.get("exchange_ws"):
        from exchange_ws_hub import stop_exchange_ws_hub

        await stop_exchange_ws_hub()

    await stop_service_bus()
    try:
        from bd_platform.kafka_bridge import stop_kafka_consumer

        await stop_kafka_consumer()
    except Exception:
        pass
    from postgres_backend import close_pool

    await close_pool()
    logger.info("Microservice stopped | mode=%s", ctx.mode)


async def _boot_web(ctx: ServiceContext) -> None:
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    from b2b_websocket_hub import start_b2b_websocket_hub
    from telegram_bot_poller import start_telegram_poller
    from telegram_monitor import start_telegram_monitor

    ctx.tasks["telegram"] = start_telegram_monitor()
    ctx.tasks["telegram_poller"] = start_telegram_poller()
    await start_b2b_websocket_hub()
    ctx.flags["b2b_ws"] = True

    if config.ML_FLYWHEEL_ENABLED:
        from ml_flywheel_scheduler import start_ml_flywheel

        start_ml_flywheel()
        ctx.flags["ml_flywheel"] = True


async def _boot_aggregator(ctx: ServiceContext) -> None:
    os.environ.setdefault("MANIFEST_AUTO_APPROVE", "true")
    os.environ.setdefault("MANIFEST_REQUIRE_REVIEW", "false")

    async def _aggregator_wrapper() -> None:
        try:
            from aggregator import run_aggregator

            await run_aggregator()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Aggregator worker failed.")

    ctx.tasks["aggregator"] = asyncio.create_task(_aggregator_wrapper(), name="ms-aggregator")
    from exchange_ws_hub import start_exchange_ws_hub

    await start_exchange_ws_hub()
    ctx.flags["exchange_ws"] = True


async def _boot_arbitrage(ctx: ServiceContext) -> None:
    from exchange_ws_hub import start_exchange_ws_hub
    from execution_engine import start_auto_execution_loop
    from instant_alert_engine import start_instant_alert_engine

    ctx.tasks["instant_alerts"] = start_instant_alert_engine()
    await start_exchange_ws_hub()
    ctx.flags["exchange_ws"] = True
    ctx.tasks["auto_exec"] = start_auto_execution_loop()


def _boot_ingestion(ctx: ServiceContext) -> None:
    async def _ingestion_wrapper() -> None:
        try:
            from ingestion_scheduler import start_ingestion_scheduler

            bootstrap = os.getenv("INGESTION_BOOTSTRAP_ON_START", "true").lower() in {"1", "true", "yes"}
            await start_ingestion_scheduler(bootstrap=bootstrap)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ingestion worker failed.")

    ctx.tasks["ingestion"] = asyncio.create_task(_ingestion_wrapper(), name="ms-ingestion")


def service_info(ctx: ServiceContext | None = None) -> dict[str, Any]:
    from service_bus import bus_stats

    mode = ctx.mode if ctx else current_mode()
    infra: dict = {}
    try:
        from bd_platform.infra_status import infra_matrix

        infra = infra_matrix()
    except Exception:
        pass
    return {
        "service_mode": mode,
        "architecture": "microservices",
        "valid_modes": sorted(VALID_MODES),
        "tasks": list((ctx.tasks if ctx else {}).keys()),
        "flags": dict(ctx.flags if ctx else {}),
        "service_bus": bus_stats(),
        "scale_ready": bool(os.getenv("REDIS_URL")),
        "infra": infra,
    }
