"""
BLACKDARK — Startup verification for Redis + Kafka price infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.PriceInfra")


async def _ensure_redis(details: dict[str, Any], *, required: bool) -> bool:
    if not getattr(config, "REDIS_PRICE_CACHE_ENABLED", True):
        details["redis"] = "disabled"
        return True
    try:
        from redis_price_cache import cache_stats, ensure_redis_ready

        redis_ok = await ensure_redis_ready(retries=2, delay_sec=0.5)
        details["redis"] = cache_stats()
        return redis_ok
    except RuntimeError as exc:
        details["redis"] = {"error": str(exc), "deferred": True}
        if required:
            raise
        logger.warning("Redis deferred — running WS + in-memory fallback | %s", exc)
        return True


async def _ensure_kafka(details: dict[str, Any], *, required: bool) -> bool:
    if not getattr(config, "KAFKA_PRICE_STREAM_ENABLED", True):
        details["kafka"] = "disabled"
        return True
    try:
        from bd_platform.kafka_bridge import bus_status, ensure_kafka_ready

        kafka_ok = await ensure_kafka_ready(retries=2, delay_sec=0.5)
        details["kafka"] = bus_status()
        return kafka_ok
    except RuntimeError as exc:
        details["kafka"] = {"error": str(exc), "deferred": True}
        if required:
            raise
        logger.warning("Kafka deferred — inline stream processor only | %s", exc)
        return True


async def _start_service_bus() -> None:
    try:
        from service_bus import start_service_bus

        await start_service_bus()
    except Exception:
        logger.debug("Service bus start skipped", exc_info=True)


async def ensure_price_infrastructure() -> dict[str, Any]:
    """Verify Redis + Kafka when required; warn-only when deferred (local dev)."""
    if not getattr(config, "PRICE_FEED_WS_ONLY", True):
        return {"strict": False, "redis": "skipped", "kafka": "skipped", "ok": True}

    redis_required = getattr(config, "REDIS_REQUIRED", False)
    kafka_required = getattr(config, "KAFKA_REQUIRED", False)
    details: dict[str, Any] = {
        "strict": redis_required or kafka_required,
        "infra_deferred": not (redis_required and kafka_required),
    }

    redis_ok = await _ensure_redis(details, required=redis_required)
    kafka_ok = await _ensure_kafka(details, required=kafka_required)
    await _start_service_bus()

    details["ok"] = redis_ok and kafka_ok
    details["mode"] = "full_infra" if (redis_required and kafka_required) else "ws_only_deferred_infra"
    logger.info(
        "Price infrastructure | mode=%s redis=%s kafka=%s",
        details["mode"],
        redis_ok,
        kafka_ok,
    )
    return details
