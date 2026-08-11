"""
BLACKDARK — Binance WebSocket trade stream → hot_spool (Point 38 live ticks).

Architecture: WebSocket (live) → hot_storage NDJSON — Oracle reads lake, not WS directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, datetime

import aiohttp

import config
from hot_storage import (
    enqueue_pricing_snapshot,
    enqueue_tick_snapshot,
    get_hot_pipeline,
    start_hot_pipeline,
)

logger = logging.getLogger("BLACKDARK.BinanceWS")

_ws_task: asyncio.Task | None = None
_running = False
_stop_event = asyncio.Event()


async def _interruptible_sleep(seconds: float) -> None:
    """Wait for stop or timeout — preferred over bare sleep polling (S7484)."""
    try:
        await asyncio.wait_for(_stop_event.wait(), timeout=max(0.01, float(seconds)))
    except asyncio.TimeoutError:
        return

_ticks_received = 0
_last_tick_at: str | None = None
_last_price: dict[str, float] = {}
_reconnect_count = 0


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _ws_symbols() -> list[str]:
    raw = os.getenv(
        "BINANCE_WS_SYMBOLS",
        "BTC,ETH,SOL,BNB,XRP,ADA,DOGE,AVAX,LINK,DOT",
    )
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
    if not symbols:
        symbols = list(config.WHITELIST_ASSETS)
    return symbols


def ws_stats() -> dict:
    return {
        "enabled": os.getenv("BINANCE_WS_ENABLED", "true").lower() in {"1", "true", "yes"},
        "running": _running,
        "symbols": _ws_symbols(),
        "ticks_received": _ticks_received,
        "last_tick_at": _last_tick_at,
        "last_prices": dict(_last_price),
        "reconnect_count": _reconnect_count,
    }


async def _ensure_hot_pipeline() -> None:
    if get_hot_pipeline() is None:
        await start_hot_pipeline()
        logger.info("Hot pipeline started for Binance WebSocket ingest.")


def _handle_trade_message(payload: dict) -> None:
    global _ticks_received, _last_tick_at

    data = payload.get("data") or payload
    symbol_raw = str(data.get("s") or "").upper()
    if not symbol_raw.endswith("USDT"):
        return

    asset = symbol_raw.replace("USDT", "")
    price = float(data.get("p") or 0)
    qty = float(data.get("q") or 0)
    if price <= 0:
        return

    side = "buy" if data.get("m") is False else "sell"
    trade_ms = int(data.get("T") or 0)
    ts = _utcnow_iso()
    notional = price * qty

    enqueue_tick_snapshot(
        exchange="binance",
        symbol=f"{asset}/USDT",
        side=side,
        price=price,
        quantity=qty,
        notional_usd=notional,
        trade_time_ms=trade_ms,
        timestamp=ts,
    )
    enqueue_pricing_snapshot(
        exchange="binance",
        symbol=f"{asset}/USDT",
        price=price,
        volume=qty,
        timestamp=ts,
        market_type="spot",
    )

    _ticks_received += 1
    _last_tick_at = ts
    _last_price[asset] = price


async def _run_stream_loop() -> None:
    global _running, _reconnect_count

    symbols = _ws_symbols()
    streams = "/".join(f"{s.lower()}usdt@trade" for s in symbols)
    url = f"wss://stream.binance.com:9443/stream?streams={streams}"

    await _ensure_hot_pipeline()
    _stop_event.clear()
    _running = True
    logger.info("Binance WebSocket connecting | symbols=%s", ",".join(symbols))

    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while _running:
            try:
                async with session.ws_connect(url, heartbeat=30) as ws:
                    logger.info("Binance WebSocket connected.")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            payload = json.loads(msg.data)
                            _handle_trade_message(payload)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _reconnect_count += 1
                logger.warning("Binance WebSocket disconnected: %s — retry in 5s", exc)
                await _interruptible_sleep(5)


def start_binance_ws_ingest() -> None:
    global _ws_task
    enabled = os.getenv("BINANCE_WS_ENABLED", "true").lower() in {"1", "true", "yes"}
    if not enabled:
        logger.info("Binance WebSocket ingest disabled (BINANCE_WS_ENABLED=false).")
        return
    if _ws_task is not None and not _ws_task.done():
        return
    _ws_task = asyncio.create_task(_run_stream_loop(), name="binance-ws-ingest")


async def stop_binance_ws_ingest() -> None:
    global _running, _ws_task
    _stop_event.set()
    _running = False
    if _ws_task is not None:
        _ws_task.cancel()
        await asyncio.gather(_ws_task, return_exceptions=True)
        _ws_task = None
    logger.info("Binance WebSocket ingest stopped.")
