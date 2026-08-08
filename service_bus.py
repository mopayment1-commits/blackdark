"""
BLACKDARK — Inter-service message bus (Redis pub/sub + local fallback).

Connects microservices: aggregator → arbitrage → web without shared memory.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger("BLACKDARK.ServiceBus")

ChannelHandler = Callable[[dict[str, Any]], Awaitable[None]]

_redis_client: Any = None
_subscribers: dict[str, list[ChannelHandler]] = defaultdict(list)
_listener_task: asyncio.Task | None = None
_local_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
_published_total = 0
_received_total = 0


def redis_url() -> str:
    return os.getenv("REDIS_URL", "").strip()


def bus_enabled() -> bool:
    return bool(redis_url()) or os.getenv("SERVICE_BUS_LOCAL", "true").lower() in {"1", "true", "yes"}


async def _get_redis() -> Any | None:
    global _redis_client
    url = redis_url()
    if not url:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as redis

        _redis_client = redis.from_url(url, decode_responses=True)
        await _redis_client.ping()
        logger.info("Service bus connected to Redis.")
        return _redis_client
    except Exception:
        logger.exception("Redis unavailable — using in-process service bus fallback.")
        _redis_client = None
        return None


async def publish(channel: str, payload: dict[str, Any]) -> bool:
    global _published_total
    if not bus_enabled():
        return False

    message = json.dumps({"channel": channel, **payload}, separators=(",", ":"))
    client = await _get_redis()
    if client is not None:
        try:
            await client.publish(channel, message)
            _published_total += 1
            return True
        except Exception:
            logger.exception("Redis publish failed | channel=%s", channel)

    queue = _local_queues[channel]
    await queue.put(payload)
    _published_total += 1
    for handler in _subscribers[channel]:
        try:
            await handler(payload)
        except Exception:
            logger.exception("Local bus handler failed | channel=%s", channel)
    return True


def subscribe(channel: str, handler: ChannelHandler) -> None:
    _subscribers[channel].append(handler)


async def _redis_listener_loop() -> None:
    client = await _get_redis()
    if client is None:
        return

    pubsub = client.pubsub()
    channels = list(_subscribers.keys()) or ["blackdark.market.updated", "blackdark.arbitrage.hot"]
    await pubsub.subscribe(*channels)
    logger.info("Service bus listening | channels=%s", channels)

    async for raw in pubsub.listen():
        if raw.get("type") != "message":
            continue
        try:
            payload = json.loads(raw.get("data") or "{}")
        except json.JSONDecodeError:
            continue
        channel = str(raw.get("channel") or payload.get("channel") or "")
        handlers = _subscribers.get(channel, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception:
                logger.exception("Redis handler failed | channel=%s", channel)


async def start_service_bus() -> None:
    global _listener_task
    if not bus_enabled():
        return
    subscribe("blackdark.market.updated", _on_market_updated)
    subscribe("blackdark.arbitrage.hot", _on_arbitrage_hot)
    client = await _get_redis()
    if client is not None and (_listener_task is None or _listener_task.done()):
        _listener_task = asyncio.create_task(_redis_listener_loop(), name="service-bus-redis")


async def stop_service_bus() -> None:
    global _listener_task, _redis_client
    if _listener_task is not None:
        _listener_task.cancel()
        try:
            await _listener_task
        except asyncio.CancelledError:
            pass
        _listener_task = None
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None


async def _on_market_updated(payload: dict[str, Any]) -> None:
    global _received_total
    _received_total += 1
    try:
        from market_cache import refresh_from_database

        await refresh_from_database(force=False)
    except Exception:
        logger.debug("Market cache refresh on bus event failed", exc_info=True)


async def _on_arbitrage_hot(payload: dict[str, Any]) -> None:
    global _received_total
    _received_total += 1
    logger.debug("Hot arbitrage event received | asset=%s", payload.get("asset"))


def bus_stats() -> dict[str, Any]:
    return {
        "enabled": bus_enabled(),
        "redis_configured": bool(redis_url()),
        "redis_connected": _redis_client is not None,
        "published_total": _published_total,
        "received_total": _received_total,
        "subscribers": {k: len(v) for k, v in _subscribers.items()},
    }
