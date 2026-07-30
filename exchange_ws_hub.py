"""
BLACKDARK — Ultra-Low Latency WebSocket streamer (Binance, OKX, Bybit).

Persistent multiplexed WSS + non-blocking tick ingress + exponential backoff reconnect.
Target: 200–500ms heartbeat, 5–10 updates/sec per asset, sub-second arb path.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

import aiohttp

import config
from ultra_tick_ingress import enqueue_ws_tick
from ws_stream_resilience import (
    all_stream_health,
    liveliness_watchdog,
    record_message,
    register_ws_connection,
    resilience_stats,
    run_resilient_stream,
    unregister_ws_connection,
)

logger = logging.getLogger("BLACKDARK.ExchangeWS")

_tasks: list[asyncio.Task] = []
_running = False
_hub_started_at: float | None = None
_messages_total = 0
_failover_activations = 0
_rest_fallback_ticks = 0


def _enabled() -> bool:
    return os.getenv("EXCHANGE_WS_ENABLED", "true").lower() in {"1", "true", "yes"}


def _symbols() -> list[str]:
    limit = int(getattr(config, "WS_HUB_SYMBOL_LIMIT", 105))
    assets = config.tracked_asset_list()[:limit]
    return [f"{a}/USDT" for a in assets]


def _priority_symbol_order() -> list[str]:
    priority = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
    base = _symbols()
    return priority + [s for s in base if s not in priority]


def _okx_symbols() -> list[str]:
    skip = getattr(config, "OKX_SKIP_SYMBOLS", None)
    if skip is None:
        skip = {
            "AGIX/USDT", "AKT/USDT", "API3/USDT", "BAND/USDT", "CYBER/USDT", "FET/USDT",
            "GLM/USDT", "ID/USDT", "ILV/USDT", "JASMY/USDT", "KAS/USDT",
            "MANTA/USDT", "MATIC/USDT", "MC/USDT", "MKR/USDT", "MNT/USDT",
            "OCEAN/USDT", "PYR/USDT", "QNT/USDT", "ROSE/USDT", "RUNE/USDT",
            "SUPER/USDT", "TON/USDT", "XMR/USDT",
        }
    return [s for s in _priority_symbol_order() if s not in skip]


def _bybit_symbols() -> list[str]:
    skip = getattr(config, "BYBIT_SKIP_SYMBOLS", None)
    if skip is None:
        skip = {
            "AGIX/USDT", "AKT/USDT", "API3/USDT", "ASI/USDT", "BAND/USDT",
            "CYBER/USDT", "FET/USDT", "GLM/USDT", "GNO/USDT", "ID/USDT",
            "ILV/USDT", "IOTA/USDT", "JASMY/USDT", "KAS/USDT", "MANTA/USDT",
            "MATIC/USDT", "MC/USDT", "MKR/USDT", "MNT/USDT", "NEO/USDT",
            "OCEAN/USDT", "PYR/USDT", "QNT/USDT", "RAY/USDT", "ROSE/USDT",
            "RUNE/USDT", "SUPER/USDT", "TAO/USDT", "TON/USDT", "XMR/USDT",
        }
    return [s for s in _priority_symbol_order() if s not in skip]


def _chunked(items: list[str], size: int) -> list[list[str]]:
    if size <= 0:
        return [items]
    return [items[i : i + size] for i in range(0, len(items), size)]


def _inc_messages() -> None:
    global _messages_total
    _messages_total += 1


def ws_hub_stats() -> dict[str, Any]:
    from live_book_hub import hub_stats

    try:
        from ultra_tick_ingress import ingress_stats

        ingress = ingress_stats()
    except ImportError:
        ingress = {}

    venues = sorted(config.live_price_venues() if hasattr(config, "live_price_venues") else config.WS_PRICE_VENUES)
    return {
        "running": _running,
        "enabled": _enabled(),
        "ws_only_mode": config.PRICE_FEED_WS_ONLY,
        "messages_total": _messages_total,
        "exchanges": venues,
        "transport": "ultra_low_latency_websocket",
        "reconnect_max_sec": getattr(config, "WS_RECONNECT_MAX_SEC", 1.0),
        "live_book": hub_stats(),
        "stream_health": all_stream_health(),
        "resilience": resilience_stats(),
        "tick_ingress": ingress,
        "failover_activations": _failover_activations,
        "rest_fallback_ticks": _rest_fallback_ticks,
        "venue_breadth": __import__("config").venue_breadth_policy(),
    }


async def _dispatch_tick(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    bid_qty: float,
    ask: float,
    ask_qty: float,
    exchange_ts_ms: int | None = None,
    packet_arrival_at: float | None = None,
) -> None:
    await enqueue_ws_tick(
        exchange,
        symbol,
        bid=bid,
        bid_qty=bid_qty,
        ask=ask,
        ask_qty=ask_qty,
        exchange_ts_ms=exchange_ts_ms,
        packet_arrival_at=packet_arrival_at,
    )
    _inc_messages()


async def _binance_book_ticker_loop() -> None:
    symbols = _symbols()
    chunk_size = int(getattr(config, "WS_HUB_STREAM_CHUNK", 40))
    chunks = _chunked(symbols, chunk_size)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20)

    async def _run_chunk(chunk: list[str]) -> None:
        stream_name = f"bookTicker-{len(chunk)}"
        url = f"wss://stream.binance.com:9443/stream?streams=" + "/".join(
            f"{s.replace('/', '').lower()}@bookTicker" for s in chunk
        )

        async def _consume(health: Any) -> None:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(url, heartbeat=20) as ws:
                    register_ws_connection("binance", stream_name, ws)
                    health.connected = True
                    logger.info("Binance bookTicker WS connected | streams=%d", len(chunk))
                    try:
                        async for msg in ws:
                            if msg.type != aiohttp.WSMsgType.TEXT:
                                continue
                            recv_at = time.perf_counter()
                            payload = json.loads(msg.data)
                            data = payload.get("data") or payload
                            sym = str(data.get("s") or "").upper()
                            if not sym.endswith("USDT"):
                                continue
                            asset = sym.replace("USDT", "")
                            exchange_ts = int(data.get("E") or data.get("T") or 0) or None
                            await _dispatch_tick(
                                "binance",
                                f"{asset}/USDT",
                                bid=float(data.get("b") or 0),
                                bid_qty=float(data.get("B") or 0),
                                ask=float(data.get("a") or 0),
                                ask_qty=float(data.get("A") or 0),
                                exchange_ts_ms=exchange_ts,
                                packet_arrival_at=recv_at,
                            )
                            record_message("binance", stream_name, latency_ms=(time.perf_counter() - recv_at) * 1000)
                    finally:
                        unregister_ws_connection("binance", stream_name)

        await run_resilient_stream("binance", stream_name, _consume, running=lambda: _running)

    await asyncio.gather(*(_run_chunk(chunk) for chunk in chunks))


async def _okx_bbo_loop() -> None:
    url = "wss://ws.okx.com:8443/ws/v5/public"
    symbols = _okx_symbols()
    chunk_size = int(getattr(config, "WS_OKX_SUBSCRIBE_CHUNK", 20))
    chunks = _chunked(symbols, chunk_size)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20)

    async def _consume(health: Any) -> None:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.ws_connect(url, heartbeat=20) as ws:
                register_ws_connection("okx", "bbo-tbt", ws)
                for chunk in chunks:
                    args = [{"channel": "bbo-tbt", "instId": s.replace("/", "-")} for s in chunk]
                    await ws.send_str(json.dumps({"op": "subscribe", "args": args}))
                    await asyncio.sleep(0.05)
                health.connected = True
                logger.info("OKX bbo-tbt WS connected | chunks=%d symbols=%d", len(chunks), len(symbols))
                try:
                    async for msg in ws:
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        recv_at = time.perf_counter()
                        payload = json.loads(msg.data)
                        if payload.get("event"):
                            if payload.get("event") == "error":
                                logger.debug("OKX subscribe skipped | %s", payload.get("msg"))
                            continue
                        inst_from_arg = str((payload.get("arg") or {}).get("instId") or "").replace("-", "/").upper()
                        for row in payload.get("data") or []:
                            inst = str(row.get("instId") or inst_from_arg).replace("-", "/").upper()
                            if not inst or "/" not in inst or not inst.endswith("/USDT"):
                                continue
                            bids = row.get("bids") or []
                            asks = row.get("asks") or []
                            if not bids or not asks:
                                continue
                            exchange_ts = int(row.get("ts") or 0) or None
                            await _dispatch_tick(
                                "okx",
                                inst,
                                bid=float(bids[0][0]),
                                bid_qty=float(bids[0][1]),
                                ask=float(asks[0][0]),
                                ask_qty=float(asks[0][1]),
                                exchange_ts_ms=exchange_ts,
                                packet_arrival_at=recv_at,
                            )
                            record_message("okx", "bbo-tbt", latency_ms=(time.perf_counter() - recv_at) * 1000)
                finally:
                    unregister_ws_connection("okx", "bbo-tbt")

    await run_resilient_stream("okx", "bbo-tbt", _consume, running=lambda: _running)


async def _bybit_orderbook_loop() -> None:
    url = "wss://stream.bybit.com/v5/public/spot"
    priority = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
    symbols = _bybit_symbols()
    tail = [s for s in symbols if s not in priority]
    chunk_size = int(getattr(config, "WS_BYBIT_SUBSCRIBE_CHUNK", 10))
    chunks = [[s] for s in priority] + _chunked(tail, chunk_size)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20)

    async def _consume(health: Any) -> None:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.ws_connect(url, heartbeat=20) as ws:
                register_ws_connection("bybit", "orderbook.1", ws)
                for chunk in chunks:
                    topics = [f"orderbook.1.{s.replace('/', '')}" for s in chunk]
                    await ws.send_str(json.dumps({"op": "subscribe", "args": topics}))
                    await asyncio.sleep(0.15)
                health.connected = True
                logger.info("Bybit orderbook.1 WS connected | chunks=%d symbols=%d", len(chunks), len(symbols))
                try:
                    async for msg in ws:
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        recv_at = time.perf_counter()
                        payload = json.loads(msg.data)
                        if payload.get("success") is False:
                            logger.debug("Bybit subscribe skipped | %s", payload.get("ret_msg"))
                            continue
                        if payload.get("op") == "subscribe":
                            continue
                        topic = str(payload.get("topic") or "")
                        data = payload.get("data") or {}
                        if not topic.startswith("orderbook.1."):
                            continue
                        raw = topic.replace("orderbook.1.", "")
                        symbol = f"{raw[:-4]}/USDT" if raw.endswith("USDT") else raw
                        bids = data.get("b") or []
                        asks = data.get("a") or []
                        if not bids or not asks:
                            continue
                        exchange_ts = int(data.get("ts") or payload.get("ts") or 0) or None
                        await _dispatch_tick(
                            "bybit",
                            symbol,
                            bid=float(bids[0][0]),
                            bid_qty=float(bids[0][1]),
                            ask=float(asks[0][0]),
                            ask_qty=float(asks[0][1]),
                            exchange_ts_ms=exchange_ts,
                            packet_arrival_at=recv_at,
                        )
                        record_message("bybit", "orderbook.1", latency_ms=(time.perf_counter() - recv_at) * 1000)
                finally:
                    unregister_ws_connection("bybit", "orderbook.1")

    await run_resilient_stream("bybit", "orderbook.1", _consume, running=lambda: _running)


async def _kraken_ticker_poll_loop() -> None:
    """Optional REST supplement — disabled in strict ultra WS-only mode."""
    if getattr(config, "ULTRA_WS_KRAKEN_REST_DISABLED", False):
        return
    pair_map = {"BTC": "XBTUSDT", "DOGE": "XDGUSDT"}
    assets = config.tracked_asset_list()[: min(25, int(getattr(config, "WS_HUB_SYMBOL_LIMIT", 105)))]
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while _running:
            for asset in assets:
                pair = pair_map.get(asset, f"{asset}USDT")
                url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        result = data.get("result") or {}
                        for tick in result.values():
                            bid = float((tick.get("b") or [0])[0])
                            ask = float((tick.get("a") or [0])[0])
                            vol = float((tick.get("v") or [0, 0])[1] or 0)
                            if bid > 0 and ask > 0:
                                await _dispatch_tick(
                                    "kraken",
                                    f"{asset}/USDT",
                                    bid=bid,
                                    bid_qty=max(vol, 1.0),
                                    ask=ask,
                                    ask_qty=max(vol, 1.0),
                                )
                except (aiohttp.ClientError, TypeError, ValueError):
                    pass
            await asyncio.sleep(max(0.2, float(getattr(config, "KRAKEN_POLL_INTERVAL_SEC", 1.0))))


def _failover_stale_threshold_sec() -> float:
    return float(getattr(config, "WS_FAILOVER_STALE_SEC", 5.0))


def _failover_warmup_sec() -> float:
    return float(getattr(config, "WS_FAILOVER_WARMUP_SEC", 30.0))


async def _venue_failover_loop() -> None:
    """REST fallback when WS venue stream is stale or disconnected."""
    global _failover_activations, _rest_fallback_ticks
    interval = float(getattr(config, "WS_FAILOVER_CHECK_SEC", 2.0))
    threshold_sec = _failover_stale_threshold_sec()

    while _running:
        try:
            if _hub_started_at is not None and (time.monotonic() - _hub_started_at) < _failover_warmup_sec():
                await asyncio.sleep(interval)
                continue

            from live_book_hub import get_quote_age_ms, is_quote_fresh
            from ws_stream_resilience import all_stream_health

            health_rows = {r["exchange"]: r for r in all_stream_health()}
            venues = sorted(
                config.live_price_venues() if hasattr(config, "live_price_venues") else config.WS_PRICE_VENUES
            )
            assets = ["BTC", "ETH", "SOL", "BNB"] + [
                a
                for a in config.tracked_asset_list()[: min(10, int(getattr(config, "WS_HUB_SYMBOL_LIMIT", 105)))]
                if a not in {"BTC", "ETH", "SOL", "BNB"}
            ]

            for venue in venues:
                row = health_rows.get(venue, {})
                disconnected = not row.get("connected", True)
                idle_ms = row.get("idle_ms")
                stream_stale = idle_ms is not None and idle_ms > threshold_sec * 1000

                for asset in assets:
                    sym = f"{asset}/USDT"
                    age_ms = get_quote_age_ms(venue, sym)
                    quote_stale = age_ms is None or age_ms > threshold_sec * 1000
                    if not (disconnected or stream_stale or quote_stale):
                        continue
                    if is_quote_fresh(venue, sym, max_age_ms=threshold_sec * 500):
                        continue

                    try:
                        import aiohttp
                        from market_context import (
                            _fetch_bybit_ticker,
                            _fetch_kraken_ticker,
                            _fetch_okx_ticker,
                            _HTTP_HEADERS,
                            _HTTP_TIMEOUT,
                        )

                        fetchers = {
                            "okx": _fetch_okx_ticker,
                            "bybit": _fetch_bybit_ticker,
                            "kraken": _fetch_kraken_ticker,
                        }
                        async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT, headers=_HTTP_HEADERS) as session:
                            rest_row = None
                            if venue == "binance":
                                pair = f"{asset}USDT"
                                from market_context import _fetch_binance_host_ticker

                                for host in ("data-api.binance.vision", "api.binance.us"):
                                    rest_row = await _fetch_binance_host_ticker(pair, host, session=session)
                                    if rest_row:
                                        break
                            else:
                                fetcher = fetchers.get(venue, _fetch_okx_ticker)
                                rest_row = await fetcher(asset, session=session)
                        if not rest_row:
                            continue
                        bid = float(rest_row.get("bid") or rest_row.get("price") or 0)
                        ask = float(rest_row.get("ask") or rest_row.get("price") or 0)
                        if bid <= 0 or ask <= 0:
                            continue
                        await _dispatch_tick(
                            venue,
                            sym,
                            bid=bid,
                            bid_qty=1.0,
                            ask=ask,
                            ask_qty=1.0,
                            exchange_ts_ms=int(time.time() * 1000),
                        )
                        _failover_activations += 1
                        _rest_fallback_ticks += 1
                        logger.info(
                            "WS failover REST tick | venue=%s symbol=%s disconnected=%s idle_ms=%s",
                            venue,
                            sym,
                            disconnected,
                            idle_ms,
                        )
                    except Exception:
                        logger.debug("Failover REST fetch skipped | %s %s", venue, sym, exc_info=True)
        except Exception:
            logger.debug("Failover loop iteration skipped", exc_info=True)
        await asyncio.sleep(interval)


async def start_exchange_ws_hub() -> None:
    global _running, _tasks, _hub_started_at
    if not _enabled():
        logger.info("Exchange WS hub disabled (EXCHANGE_WS_ENABLED=false).")
        return
    if _running:
        return
    _running = True
    _hub_started_at = time.monotonic()

    from ultra_tick_ingress import start_ultra_tick_ingress

    await start_ultra_tick_ingress()

    _tasks = [
        asyncio.create_task(_binance_book_ticker_loop(), name="ws-binance-book"),
        asyncio.create_task(_okx_bbo_loop(), name="ws-okx-bbo"),
        asyncio.create_task(_bybit_orderbook_loop(), name="ws-bybit-book"),
        asyncio.create_task(liveliness_watchdog(running=lambda: _running), name="ws-liveliness"),
        asyncio.create_task(_venue_failover_loop(), name="ws-failover"),
    ]
    if getattr(config, "KRAKEN_POLL_ENABLED", True) and not getattr(config, "ULTRA_WS_KRAKEN_REST_DISABLED", False):
        _tasks.append(asyncio.create_task(_kraken_ticker_poll_loop(), name="poll-kraken"))
    logger.info(
        "Ultra-Low Latency WS hub started | ws_only=%s venues=%s symbols=%d reconnect_max=%ss",
        config.PRICE_FEED_WS_ONLY,
        ",".join(sorted(config.live_price_venues() if hasattr(config, "live_price_venues") else config.WS_PRICE_VENUES)),
        len(_symbols()),
        getattr(config, "WS_RECONNECT_MAX_SEC", 1.0),
    )


async def stop_exchange_ws_hub() -> None:
    global _running, _tasks
    _running = False
    for task in _tasks:
        task.cancel()
    if _tasks:
        await asyncio.gather(*_tasks, return_exceptions=True)
    _tasks = []
    try:
        from ultra_tick_ingress import stop_ultra_tick_ingress

        await stop_ultra_tick_ingress()
    except ImportError:
        pass
    logger.info("Exchange WS hub stopped.")
