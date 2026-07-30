"""

BLACKDARK — Non-blocking ultra-low latency tick ingress.



WS loops enqueue ticks; worker pool drains without blocking the read buffer.

Sliding-window: only the latest tick per venue/symbol is kept when queue pressure hits.

Overflow strategy: latest tick preserved in _latest_only + pending recovery flush (no silent drop).

"""



from __future__ import annotations



import asyncio

import logging

import time

from typing import Any



import config



logger = logging.getLogger("BLACKDARK.UltraTickIngress")



_queue: asyncio.Queue[dict[str, Any]] | None = None

_workers: list[asyncio.Task] = []

_overflow_flusher: asyncio.Task | None = None

_running = False

_latest_only: dict[str, dict[str, Any]] = {}

_pending_recovery: set[str] = set()

_ticks_enqueued = 0

_ticks_processed = 0

_ticks_coalesced = 0

_ticks_priority_bypass = 0

_backpressure_events = 0

_ticks_recovered = 0

_queue_high_water_mark = 0

_latency_by_symbol: dict[str, float] = {}





def _enabled() -> bool:

    return getattr(config, "ULTRA_WS_STREAMER_ENABLED", True)





def _worker_count() -> int:

    return max(2, int(getattr(config, "ULTRA_WS_WORKER_COUNT", 4)))





def _queue_size() -> int:

    return int(getattr(config, "ULTRA_WS_QUEUE_SIZE", 20_000))





def _overflow_flush_interval_sec() -> float:

    return float(getattr(config, "ULTRA_WS_OVERFLOW_FLUSH_SEC", 0.005))





def _tick_key(exchange: str, symbol: str) -> str:

    return f"{exchange.lower()}|{symbol.upper()}"





def _priority_symbols() -> frozenset[str]:
    raw = getattr(config, "ULTRA_WS_PRIORITY_SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT")
    if isinstance(raw, str):
        return frozenset(s.strip().upper() for s in raw.split(",") if s.strip())
    return frozenset(str(s).strip().upper() for s in raw if str(s).strip())





async def _emit_priority_tick(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    bid_qty: float,
    ask: float,
    ask_qty: float,
    exchange_ts_ms: int | None,
    market_type: str,
    packet_arrival_at: float | None,
) -> None:
    global _ticks_priority_bypass, _ticks_processed
    from exchange_time_sync import record_exchange_timestamp
    from price_stream_engine import emit_tick
    from ws_stream_resilience import record_message

    record_exchange_timestamp(exchange, exchange_ts_ms)
    record_message(exchange, "priority", latency_ms=0.0)
    await emit_tick(
        exchange,
        symbol,
        bid=bid,
        bid_qty=bid_qty,
        ask=ask,
        ask_qty=ask_qty,
        market_type=market_type,
        exchange_ts_ms=exchange_ts_ms,
        packet_arrival_at=packet_arrival_at,
    )
    _ticks_priority_bypass += 1
    _ticks_processed += 1





def _ingress_latency_ms(enqueued_at: float) -> float:

    return (time.perf_counter() - enqueued_at) * 1000.0





def _track_queue_depth() -> None:

    global _queue_high_water_mark

    if _queue is None:

        return

    depth = _queue.qsize()

    if depth > _queue_high_water_mark:

        _queue_high_water_mark = depth





def _schedule_recovery(key: str) -> None:

    global _backpressure_events

    _backpressure_events += 1

    _pending_recovery.add(key)

    if _overflow_flusher is None or _overflow_flusher.done():

        _start_overflow_flusher()





def _start_overflow_flusher() -> None:

    global _overflow_flusher

    if not _running or _queue is None:

        return

    _overflow_flusher = asyncio.create_task(_overflow_flusher_loop(), name="ultra-tick-overflow-flush")





async def _try_enqueue_latest(key: str) -> bool:

    """Re-queue the latest tick for a venue/symbol after backpressure."""

    global _ticks_recovered

    if _queue is None:

        return False

    payload = _latest_only.get(key)

    if payload is None:

        _pending_recovery.discard(key)

        return False

    try:

        _queue.put_nowait(payload)

        _ticks_recovered += 1

        _pending_recovery.discard(key)

        _track_queue_depth()

        return True

    except asyncio.QueueFull:

        return False





async def _overflow_flusher_loop() -> None:

    """Drain pending latest ticks when queue pressure eases."""

    while _running and _pending_recovery:

        pending = list(_pending_recovery)

        for key in pending:

            await _try_enqueue_latest(key)

        await asyncio.sleep(_overflow_flush_interval_sec())





async def enqueue_ws_tick(

    exchange: str,

    symbol: str,

    *,

    bid: float,

    bid_qty: float,

    ask: float,

    ask_qty: float,

    exchange_ts_ms: int | None = None,

    market_type: str = "spot",

    packet_arrival_at: float | None = None,

) -> None:

    """Non-blocking enqueue — never blocks the WS read loop."""

    global _ticks_enqueued

    sym_upper = symbol.strip().upper()
    if sym_upper in _priority_symbols() and _enabled() and _queue is not None:
        from feed_latency_tracker import mark_packet_arrival

        arrival = packet_arrival_at or mark_packet_arrival()
        _ticks_enqueued += 1
        asyncio.create_task(
            _emit_priority_tick(
                exchange.lower(),
                sym_upper,
                bid=bid,
                bid_qty=bid_qty,
                ask=ask,
                ask_qty=ask_qty,
                exchange_ts_ms=exchange_ts_ms,
                market_type=market_type,
                packet_arrival_at=arrival,
            ),
            name=f"priority-tick-{exchange}-{sym_upper}",
        )
        return

    if not _enabled() or _queue is None:

        from price_stream_engine import emit_tick



        await emit_tick(

            exchange,

            symbol,

            bid=bid,

            bid_qty=bid_qty,

            ask=ask,

            ask_qty=ask_qty,

            market_type=market_type,

            exchange_ts_ms=exchange_ts_ms,

        )

        return



    from feed_latency_tracker import mark_packet_arrival



    arrival = packet_arrival_at or mark_packet_arrival()

    payload = {

        "exchange": exchange.lower(),

        "symbol": symbol.upper(),

        "bid": bid,

        "bid_qty": bid_qty,

        "ask": ask,

        "ask_qty": ask_qty,

        "exchange_ts_ms": exchange_ts_ms,

        "market_type": market_type,

        "enqueued_at": time.perf_counter(),

        "packet_arrival_at": arrival,

    }

    key = _tick_key(exchange, symbol)

    _latest_only[key] = payload

    _ticks_enqueued += 1



    try:

        _queue.put_nowait(payload)

        _track_queue_depth()

    except asyncio.QueueFull:

        _schedule_recovery(key)

        logger.debug(

            "Tick ingress backpressure | %s %s | queue=%d pending=%d",

            exchange,

            symbol,

            _queue.qsize() if _queue else 0,

            len(_pending_recovery),

        )





async def _worker_loop(worker_id: int) -> None:

    global _ticks_processed, _ticks_coalesced

    from exchange_time_sync import record_exchange_timestamp

    from price_stream_engine import emit_tick

    from ws_stream_resilience import record_message



    while _running:

        try:

            tick = await _queue.get()

        except asyncio.CancelledError:

            raise



        key = _tick_key(tick["exchange"], tick["symbol"])

        latest = _latest_only.get(key)

        if latest is not tick:

            _ticks_coalesced += 1

            continue



        latency = _ingress_latency_ms(tick["enqueued_at"])

        _latency_by_symbol[tick["symbol"]] = latency

        record_exchange_timestamp(tick["exchange"], tick.get("exchange_ts_ms"))

        record_message(tick["exchange"], "bookTicker", latency_ms=latency)



        await emit_tick(

            tick["exchange"],

            tick["symbol"],

            bid=tick["bid"],

            bid_qty=tick["bid_qty"],

            ask=tick["ask"],

            ask_qty=tick["ask_qty"],

            market_type=tick.get("market_type", "spot"),

            exchange_ts_ms=tick.get("exchange_ts_ms"),

            packet_arrival_at=tick.get("packet_arrival_at"),

        )

        _ticks_processed += 1



        if key in _pending_recovery:

            await _try_enqueue_latest(key)



        if _ticks_processed % 500 == 0:

            sym = tick["symbol"]

            logger.info("Ticker Stream Active: %s | Latency: %.1fms", sym, latency)





async def start_ultra_tick_ingress() -> list[asyncio.Task]:

    global _queue, _workers, _running, _overflow_flusher

    if not _enabled() or _workers:

        return _workers

    _running = True

    _queue = asyncio.Queue(maxsize=_queue_size())

    _workers = [

        asyncio.create_task(_worker_loop(i), name=f"ultra-tick-worker-{i}") for i in range(_worker_count())

    ]

    _start_overflow_flusher()

    logger.info("Ultra tick ingress started | workers=%d queue=%d", _worker_count(), _queue_size())

    return _workers





async def stop_ultra_tick_ingress() -> None:

    global _workers, _running, _queue, _overflow_flusher

    _running = False

    if _overflow_flusher is not None:

        _overflow_flusher.cancel()

        try:

            await _overflow_flusher

        except asyncio.CancelledError:

            pass

        _overflow_flusher = None

    for task in _workers:

        task.cancel()

    if _workers:

        await asyncio.gather(*_workers, return_exceptions=True)

    _workers = []

    _queue = None

    _pending_recovery.clear()





def ingress_stats() -> dict[str, Any]:

    latencies = list(_latency_by_symbol.values())

    backpressure_active = bool(_pending_recovery)

    return {

        "enabled": _enabled(),

        "workers": len(_workers),

        "queue_size": _queue.qsize() if _queue else 0,

        "queue_capacity": _queue_size() if _queue else 0,

        "queue_high_water_mark": _queue_high_water_mark,

        "ticks_enqueued": _ticks_enqueued,

        "ticks_processed": _ticks_processed,

        "ticks_coalesced": _ticks_coalesced,

        "ticks_priority_bypass": _ticks_priority_bypass,

        "backpressure_events": _backpressure_events,

        "ticks_recovered": _ticks_recovered,

        "pending_recovery": len(_pending_recovery),

        "backpressure_active": backpressure_active,

        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,

        "sample_symbols": sorted(_latency_by_symbol.keys())[:5],

    }


