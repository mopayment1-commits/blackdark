"""
BLACKDARK — Startup verification for Redis + Kafka price infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.PriceInfra")


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

    redis_ok = False
    if getattr(config, "REDIS_PRICE_CACHE_ENABLED", True):
        try:
            from redis_price_cache import cache_stats, ensure_redis_ready

            redis_ok = await ensure_redis_ready(retries=2, delay_sec=0.5)
            details["redis"] = cache_stats()
        except RuntimeError as exc:
            details["redis"] = {"error": str(exc), "deferred": True}
            if redis_required:
                raise
            logger.warning("Redis deferred — running WS + in-memory fallback | %s", exc)
            redis_ok = True
    else:
        redis_ok = True
        details["redis"] = "disabled"

    kafka_ok = False
    if getattr(config, "KAFKA_PRICE_STREAM_ENABLED", True):
        try:
            from bd_platform.kafka_bridge import bus_status, ensure_kafka_ready

            kafka_ok = await ensure_kafka_ready(retries=2, delay_sec=0.5)
            details["kafka"] = bus_status()
        except RuntimeError as exc:
            details["kafka"] = {"error": str(exc), "deferred": True}
            if kafka_required:
                raise
            logger.warning("Kafka deferred — inline stream processor only | %s", exc)
            kafka_ok = True
    else:
        kafka_ok = True
        details["kafka"] = "disabled"

    try:
        from service_bus import start_service_bus

        await start_service_bus()
    except Exception:
        logger.debug("Service bus start skipped", exc_info=True)

    details["ok"] = redis_ok and kafka_ok
    details["mode"] = "full_infra" if (redis_required and kafka_required) else "ws_only_deferred_infra"
    logger.info(
        "Price infrastructure | mode=%s redis=%s kafka=%s",
        details["mode"],
        redis_ok,
        kafka_ok,
    )
    return details
