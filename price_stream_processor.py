"""
BLACKDARK — Kafka stream processing pipeline for WS price ticks.

Workers:
  1. OHLC aggregation → Redis
  2. Cross-venue spread detection
  3. Opportunity + alert publishing (Kafka topics)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.PriceStreamProcessor")

TOPIC_TICKS = getattr(config, "PRICE_STREAM_TOPIC", "blackdark.price.ticks")
TOPIC_OPPORTUNITIES = "blackdark.opportunities"
TOPIC_ALERTS = "blackdark.alerts"

_ticks_processed = 0
_spreads_detected = 0
_opportunities_published = 0
_alerts_published = 0
_recent_opportunities: list[dict[str, Any]] = []
_recent_spreads: list[dict[str, Any]] = []
_worker_task: asyncio.Task | None = None
_running = False


def _asset_from_symbol(symbol: str) -> str:
    return symbol.replace("/USDT", "").replace("USDC", "").upper()


async def process_tick(tick: dict[str, Any]) -> None:
    """Full stream worker — called from Kafka consumer or inline emit path."""
    global _ticks_processed, _spreads_detected, _opportunities_published, _alerts_published

    _ticks_processed += 1
    symbol = str(tick.get("symbol") or "").upper()
    exchange = str(tick.get("exchange") or "").lower()
    bid = float(tick.get("bid") or 0)
    ask = float(tick.get("ask") or 0)
    ts_ms = int(tick.get("ts_ms") or time.time() * 1000)
    if not symbol or bid <= 0 or ask <= 0:
        return

    mid = (bid + ask) / 2.0
    try:
        from redis_price_cache import record_ohlc_tick

        await record_ohlc_tick(symbol, mid=mid, ts_ms=ts_ms)
    except Exception:
        logger.debug("OHLC record skipped", exc_info=True)

    spread = await _detect_cross_spread(symbol, ts_ms)
    if not spread:
        return

    _spreads_detected += 1
    _recent_spreads.append(spread)
    if len(_recent_spreads) > 100:
        _recent_spreads.pop(0)

    if spread.get("spread_bps", 0) < float(getattr(config, "ARBITRAGE_ALERT_MIN_PROFIT_PCT", 0.05)) * 100:
        return

    opp = {
        **spread,
        "kind": "stream_cross_exchange",
        "source": "price_stream_processor",
        "trigger_exchange": exchange,
    }
    _recent_opportunities.append(opp)
    if len(_recent_opportunities) > 50:
        _recent_opportunities.pop(0)

    await _publish(TOPIC_OPPORTUNITIES, opp)
    _opportunities_published += 1

    if spread.get("spread_bps", 0) >= 5.0:
        alert = {
            "type": "cross_spread",
            "asset": spread.get("asset"),
            "spread_bps": spread.get("spread_bps"),
            "buy_exchange": spread.get("buy_exchange"),
            "sell_exchange": spread.get("sell_exchange"),
            "ts_ms": ts_ms,
        }
        await _publish(TOPIC_ALERTS, alert)
        _alerts_published += 1


async def _detect_cross_spread(symbol: str, ts_ms: int) -> dict[str, Any] | None:
    asset = _asset_from_symbol(symbol)
    if not asset:
        return None

    prices: dict[str, dict[str, float]] = {}
    for venue in config.WS_PRICE_VENUES:
        from live_book_hub import get_best_price

        row = get_best_price(venue, f"{asset}/USDT")
        if row:
            prices[venue] = row
        else:
            try:
                from redis_price_cache import get_best_price as redis_price

                row = await redis_price(venue, f"{asset}/USDT")
                if row:
                    prices[venue] = row
            except Exception:
                logger.debug("redis operation skipped", exc_info=True)

    if len(prices) < 2:
        return None

    buy_ex = min(prices, key=lambda v: prices[v]["ask"])
    sell_ex = max(prices, key=lambda v: prices[v]["bid"])
    if buy_ex == sell_ex:
        return None

    buy_ask = prices[buy_ex]["ask"]
    sell_bid = prices[sell_ex]["bid"]
    if sell_bid <= buy_ask:
        return None

    spread_bps = ((sell_bid - buy_ask) / buy_ask) * 10_000
    if spread_bps < 1.0:
        return None

    return {
        "asset": asset,
        "symbol": f"{asset}/USDT",
        "buy_exchange": buy_ex,
        "sell_exchange": sell_ex,
        "buy_price": buy_ask,
        "sell_price": sell_bid,
        "spread_bps": round(spread_bps, 2),
        "ts_ms": ts_ms,
    }


async def _publish(topic: str, payload: dict[str, Any]) -> None:
    try:
        from bd_platform.kafka_bridge import publish as kafka_publish

        await kafka_publish(topic, payload)
    except Exception:
        logger.debug("Kafka publish failed | topic=%s", topic, exc_info=True)

    try:
        from service_bus import publish as bus_publish

        await bus_publish(topic, payload)
    except Exception:
        logger.debug("service bus publish skipped", exc_info=True)


async def start_stream_workers() -> asyncio.Task | None:
    """Kafka consumer worker — for dedicated replicas; inline path handles same-process ticks."""
    global _worker_task, _running
    if _worker_task is not None:
        return _worker_task
    _running = True

    inline = getattr(config, "PRICE_STREAM_INLINE_PROCESS", True)
    if inline:
        logger.info("Price stream inline processor active — Kafka consumer reserved for worker replicas")
        return None

    async def _on_message(topic: str, payload: dict[str, Any]) -> None:
        if topic != TOPIC_TICKS and not topic.endswith(".price.ticks"):
            return
        await process_tick(payload)

    try:
        from bd_platform.kafka_bridge import ensure_kafka_ready, start_kafka_consumer

        await ensure_kafka_ready()
        _worker_task = await start_kafka_consumer(_on_message, topics=(TOPIC_TICKS, TOPIC_OPPORTUNITIES))
        if _worker_task:
            logger.info("Price stream Kafka workers started | topics=%s,%s", TOPIC_TICKS, TOPIC_OPPORTUNITIES)
    except Exception as exc:
        logger.warning("Stream workers deferred: %s", exc)
    return _worker_task


async def stop_stream_workers() -> None:
    global _worker_task, _running
    _running = False
    from bd_platform.kafka_bridge import stop_kafka_consumer

    await stop_kafka_consumer()
    _worker_task = None


def processor_stats() -> dict[str, Any]:
    return {
        "running": _running,
        "ticks_processed": _ticks_processed,
        "spreads_detected": _spreads_detected,
        "opportunities_published": _opportunities_published,
        "alerts_published": _alerts_published,
        "recent_spreads": _recent_spreads[-8:],
        "recent_opportunities": _recent_opportunities[-8:],
        "topics": [TOPIC_TICKS, TOPIC_OPPORTUNITIES, TOPIC_ALERTS],
    }
