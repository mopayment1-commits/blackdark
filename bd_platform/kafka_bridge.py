"""Apache Kafka bridge — optional producer/consumer; Redis/local fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger("BLACKDARK.KafkaBridge")

_producer: Any = None
_consumer_task: asyncio.Task | None = None
_received: list[dict[str, Any]] = []
KAFKA_TOPICS = ("blackdark.opportunities", "blackdark.executions", "blackdark.alerts")


def kafka_brokers() -> str:
    return os.getenv("KAFKA_BROKERS", "").strip()


def kafka_enabled() -> bool:
    return bool(kafka_brokers())


def bus_status() -> dict[str, Any]:
    from service_bus import bus_enabled, redis_url

    producer_ok = False
    if kafka_enabled():
        producer_ok = _get_producer() is not None
    if kafka_enabled() and producer_ok:
        primary = "kafka"
    elif redis_url():
        primary = "redis"
    else:
        primary = "local"

    return {
        "kafka_configured": kafka_enabled(),
        "kafka_brokers": kafka_brokers() or None,
        "kafka_producer_ok": producer_ok,
        "kafka_topics": list(KAFKA_TOPICS),
        "redis_url_configured": bool(redis_url()),
        "local_bus_enabled": bus_enabled(),
        "primary": primary,
        "messages_buffered_local": len(_received),
        "note": "Set KAFKA_BROKERS=localhost:9092 (docker compose kafka service).",
    }


def _get_producer() -> Any | None:
    global _producer
    if not kafka_enabled():
        return None
    if _producer is not None:
        return _producer
    try:
        from kafka import KafkaProducer

        _producer = KafkaProducer(
            bootstrap_servers=kafka_brokers().split(","),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            acks="all",
            retries=2,
        )
        logger.info("Kafka producer connected to %s", kafka_brokers())
        return _producer
    except Exception as exc:
        logger.warning("Kafka unavailable: %s", exc)
        return None


async def publish(channel: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Publish to Kafka if configured, else service_bus."""
    topic = channel if channel.startswith("blackdark.") else f"blackdark.{channel}"
    producer = _get_producer()
    if producer is not None:
        try:
            producer.send(topic, payload)
            producer.flush(timeout=5)
            return {"transport": "kafka", "channel": topic, "ok": True}
        except Exception as exc:
            logger.warning("Kafka publish failed: %s", exc)

    from service_bus import publish as bus_publish

    await bus_publish(channel, payload)
    return {"transport": "service_bus", "channel": channel, "ok": True}


def _poll_kafka_batch(consumer: Any) -> list[Any]:
    # kafka-python is sync — never block the event loop
    batch = []
    for msg in consumer:
        batch.append(msg)
        if len(batch) >= 50:
            break
    return batch


async def _dispatch_kafka_batch(
    batch: list[Any],
    handler: Callable[[str, dict[str, Any]], Awaitable[None]] | None,
) -> None:
    for msg in batch:
        payload = msg.value if isinstance(msg.value, dict) else {}
        _received.append({"topic": msg.topic, "payload": payload})
        if len(_received) > 200:
            _received.pop(0)
        if handler:
            await handler(msg.topic, payload)


async def _kafka_consumer_loop(
    handler: Callable[[str, dict[str, Any]], Awaitable[None]] | None,
    topics: tuple[str, ...],
) -> None:
    try:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=kafka_brokers().split(","),
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            consumer_timeout_ms=1000,
            group_id=os.getenv("KAFKA_GROUP_ID", "blackdark-workers"),
        )
        logger.info("Kafka consumer started on %s", topics)
        while True:
            batch = await asyncio.to_thread(_poll_kafka_batch, consumer)
            await _dispatch_kafka_batch(batch, handler)
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning("Kafka consumer stopped: %s", exc)


async def start_kafka_consumer(
    handler: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    *,
    topics: tuple[str, ...] = KAFKA_TOPICS,
) -> asyncio.Task | None:
    """Background consumer — no-op if Kafka not configured."""
    await asyncio.sleep(0)
    global _consumer_task
    if not kafka_enabled() or _consumer_task is not None:
        return _consumer_task

    _consumer_task = asyncio.create_task(
        _kafka_consumer_loop(handler, topics),
        name="kafka-consumer",
    )
    return _consumer_task


async def stop_kafka_consumer() -> None:
    global _consumer_task
    if _consumer_task is not None:
        _consumer_task.cancel()
        await asyncio.gather(_consumer_task, return_exceptions=True)
        _consumer_task = None


def recent_messages(limit: int = 20) -> list[dict[str, Any]]:
    return _received[-limit:]
