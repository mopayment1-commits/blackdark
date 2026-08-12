"""
BLACKDARK — WebSocket-only price stream engine.

Policy (strict):
  - Spot top-of-book from persistent multiplexed WS: Binance, OKX, Bybit
  - NO HTTP/REST for live price ingestion when PRICE_FEED_WS_ONLY=true
  - Each tick → live_book_hub + Redis cache + Kafka/Redpanda topic (optional)
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

import config
from live_book_hub import update_top_of_book

logger = logging.getLogger("BLACKDARK.PriceStreamEngine")

TOPIC = getattr(config, "PRICE_STREAM_TOPIC", "blackdark.price.ticks")
_ticks_total = 0
_kafka_published = 0
_redis_written = 0
_hot_archived = 0
_hot_throttled = 0
_last_hot_write_ms: dict[str, int] = {}
_processor_task: asyncio.Task | None = None


def _stream_processor_stats() -> dict[str, Any]:
    try:
        from price_stream_processor import processor_stats

        return processor_stats()
    except ImportError:
        return {}


def ws_only_mode() -> bool:
    return getattr(config, "PRICE_FEED_WS_ONLY", True)


def allowed_ws_venues() -> frozenset[str]:
    return getattr(config, "WS_PRICE_VENUES", frozenset({"binance", "okx", "bybit"}))


async def emit_tick(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    bid_qty: float,
    ask: float,
    ask_qty: float,
    market_type: str = "spot",
) -> None:
    """Single ingress for WS ticks — memory, Redis, Kafka."""
    global _ticks_total, _kafka_published, _redis_written

    ex = exchange.strip().lower()
    if ex not in allowed_ws_venues():
        return

    update_top_of_book(ex, symbol, bid=bid, bid_qty=bid_qty, ask=ask, ask_qty=ask_qty, market_type=market_type)
    _ticks_total += 1

    from stream_freshness_truth import fanout_safe, label_tick

    labeled = fanout_safe(
        label_tick(
            exchange=ex,
            symbol=symbol,
            bid=bid,
            ask=ask,
            provider_ts_ms=int(time.time() * 1000),
        )
    )

    try:
        from canonical_adoption import adopt_tick_quote

        adopt_tick_quote(
            venue=ex,
            symbol=symbol,
            bid=bid,
            ask=ask,
            source=f"ws:{ex}",
            provider_timestamp=labeled.get("provider_ts_ms"),
            bid_qty=bid_qty,
            ask_qty=ask_qty,
            require_live=False,
        )
    except Exception:
        logger.debug("Canonical quote adopt skipped", exc_info=True)

    payload = {
        "exchange": ex,
        "symbol": symbol.strip().upper(),
        "bid": bid,
        "ask": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,
        "market_type": market_type,
        "ts_ms": labeled["ingest_ts_ms"],
        "provider_ts_ms": labeled.get("provider_ts_ms"),
        "freshness_class": labeled["freshness_class"],
        "is_live": labeled["is_live"],
        "stream_status": labeled["stream_status"],
        "display_badge": labeled.get("display_badge"),
        "executable_quotes": labeled.get("executable_quotes"),
    }

    if getattr(config, "REDIS_PRICE_CACHE_ENABLED", True):
        try:
            from redis_price_cache import set_top_of_book

            if await set_top_of_book(ex, symbol, bid=bid, ask=ask, bid_qty=bid_qty, ask_qty=ask_qty):
                _redis_written += 1
        except Exception:
            logger.debug("Redis tick write skipped", exc_info=True)

    if getattr(config, "KAFKA_PRICE_STREAM_ENABLED", True):
        try:
            from bd_platform.kafka_bridge import publish as kafka_publish

            result = await kafka_publish(TOPIC, payload)
            if result.get("transport") == "kafka":
                _kafka_published += 1
        except Exception:
            logger.debug("Kafka tick publish skipped", exc_info=True)

    # Inline stream worker (same process) + Kafka consumer (multi-worker scale-out)
    try:
        from price_stream_processor import process_tick

        await process_tick(payload)
    except Exception:
        logger.debug("Inline stream processor skipped", exc_info=True)

    if config.HOT_STORAGE_ARCHIVE_WS_TICKS:
        await _archive_top_of_book_to_hot_tier(
            exchange=ex,
            symbol=payload["symbol"],
            bid=bid,
            ask=ask,
            market_type=market_type,
            ts_ms=payload["ts_ms"],
        )


def _hot_throttle_key(exchange: str, symbol: str) -> str:
    return f"{exchange}:{symbol}"


def _should_throttle_hot_write(exchange: str, symbol: str, ts_ms: int) -> bool:
    throttle_ms = max(100, config.HOT_STORAGE_SYMBOL_THROTTLE_MS)
    key = _hot_throttle_key(exchange, symbol)
    last = _last_hot_write_ms.get(key, 0)
    if ts_ms - last < throttle_ms:
        return True
    _last_hot_write_ms[key] = ts_ms
    return False


async def _archive_top_of_book_to_hot_tier(
    *,
    exchange: str,
    symbol: str,
    bid: float,
    ask: float,
    market_type: str,
    ts_ms: int,
) -> None:
    global _hot_archived, _hot_throttled

    if _should_throttle_hot_write(exchange, symbol, ts_ms):
        _hot_throttled += 1
        return

    try:
        from hot_storage import enqueue_pricing_snapshot, get_hot_pipeline, start_hot_pipeline

        if get_hot_pipeline() is None:
            await start_hot_pipeline()
        mid = (bid + ask) / 2.0 if bid and ask else bid or ask
        ts_iso = datetime.fromtimestamp(ts_ms / 1000, tz=UTC).isoformat()
        if enqueue_pricing_snapshot(
            exchange=exchange,
            symbol=symbol,
            price=float(mid),
            volume=None,
            timestamp=ts_iso,
            market_type=market_type,
        ):
            _hot_archived += 1
    except Exception:
        logger.debug("Hot tier WS archive skipped", exc_info=True)


async def start_stream_processor() -> asyncio.Task | None:
    """Start Kafka consumer workers (OHLC, spreads, alerts)."""
    global _processor_task
    if _processor_task is not None:
        return _processor_task

    try:
        from price_infra import ensure_price_infrastructure
        from price_stream_processor import start_stream_workers

        await ensure_price_infrastructure()
        _processor_task = await start_stream_workers()
        if _processor_task:
            logger.info("Price stream processor started | topic=%s", TOPIC)
    except Exception as exc:
        logger.warning("Price stream processor not started: %s", exc)
    return _processor_task


async def stop_stream_processor() -> None:
    global _processor_task
    from price_stream_processor import stop_stream_workers

    await stop_stream_workers()
    _processor_task = None


def feed_engine_status() -> dict[str, Any]:
    from exchange_ws_hub import ws_hub_stats
    from live_book_hub import hub_stats

    redis_stats: dict[str, Any] = {}
    try:
        from redis_price_cache import cache_stats

        redis_stats = cache_stats()
    except ImportError:
        pass

    kafka_stats: dict[str, Any] = {}
    try:
        from bd_platform.kafka_bridge import bus_status

        kafka_stats = bus_status()
    except ImportError:
        pass

    return {
        "architecture": "ws_only" if ws_only_mode() else "hybrid",
        "policy": {
            "rest_price_ingestion": "forbidden" if ws_only_mode() else "allowed_legacy",
            "ws_venues": sorted(allowed_ws_venues()),
            "multiplexed_websockets": True,
        },
        "ticks_total": _ticks_total,
        "kafka_ticks_published": _kafka_published,
        "redis_ticks_written": _redis_written,
        "hot_tier_archived": _hot_archived,
        "hot_tier_throttled": _hot_throttled,
        "stream_processor": _stream_processor_stats(),
        "websocket_hub": ws_hub_stats(),
        "live_book": hub_stats(),
        "redis_cache": redis_stats,
        "kafka_bus": kafka_stats,
    }
