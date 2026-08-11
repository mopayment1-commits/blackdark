"""
BLACKDARK — Multi-exchange WebSocket bookTicker hub (Low Latency Engine).

Binance + OKX + Bybit top-of-book → live_book_hub → arbitrage scan in <500ms.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import aiohttp

import config
from live_book_hub import update_top_of_book

logger = logging.getLogger("BLACKDARK.ExchangeWS")

_tasks: list[asyncio.Task] = []
_running = False
_messages_total = 0


def _enabled() -> bool:
    return os.getenv("EXCHANGE_WS_ENABLED", "true").lower() in {"1", "true", "yes"}


def _symbols() -> list[str]:
    assets = sorted(config.WHITELIST_ASSETS)
    return [f"{a}/USDT" for a in assets]


def ws_hub_stats() -> dict[str, Any]:
    from live_book_hub import hub_stats

    return {
        "running": _running,
        "enabled": _enabled(),
        "messages_total": _messages_total,
        "exchanges": ["binance", "okx", "bybit", "kraken"],
        "live_book": hub_stats(),
    }


def _inc_messages() -> None:
    global _messages_total
    _messages_total += 1


async def _binance_book_ticker_loop() -> None:
    streams = "/".join(f"{s.replace('/', '').lower()}@bookTicker" for s in _symbols())
    url = f"wss://stream.binance.com:9443/stream?streams={streams}"
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while _running:
            try:
                async with session.ws_connect(url, heartbeat=20) as ws:
                    logger.info("Binance bookTicker WS connected.")
                    async for msg in ws:
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        payload = json.loads(msg.data)
                        data = payload.get("data") or payload
                        sym = str(data.get("s") or "").upper()
                        if not sym.endswith("USDT"):
                            continue
                        asset = sym.replace("USDT", "")
                        update_top_of_book(
                            "binance",
                            f"{asset}/USDT",
                            bid=float(data.get("b") or 0),
                            bid_qty=float(data.get("B") or 0),
                            ask=float(data.get("a") or 0),
                            ask_qty=float(data.get("A") or 0),
                        )
                        _inc_messages()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Binance bookTicker WS error: %s — retry 3s", exc)
                await asyncio.sleep(3)


async def _okx_bbo_loop() -> None:
    url = "wss://ws.okx.com:8443/ws/v5/public"
    args = [{"channel": "bbo-tbt", "instId": s.replace("/", "-")} for s in _symbols()]
    sub = json.dumps({"op": "subscribe", "args": args})
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while _running:
            try:
                async with session.ws_connect(url, heartbeat=20) as ws:
                    await ws.send_str(sub)
                    logger.info("OKX bbo-tbt WS connected.")
                    async for msg in ws:
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        payload = json.loads(msg.data)
                        if payload.get("event"):
                            continue
                        for row in payload.get("data") or []:
                            inst = str(row.get("instId") or "").replace("-", "/")
                            bids = row.get("bids") or []
                            asks = row.get("asks") or []
                            if not bids or not asks:
                                continue
                            update_top_of_book(
                                "okx",
                                inst,
                                bid=float(bids[0][0]),
                                bid_qty=float(bids[0][1]),
                                ask=float(asks[0][0]),
                                ask_qty=float(asks[0][1]),
                            )
                            _inc_messages()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("OKX bbo-tbt WS error: %s — retry 3s", exc)
                await asyncio.sleep(3)


async def _bybit_orderbook_loop() -> None:
    url = "wss://stream.bybit.com/v5/public/spot"
    topics = [f"orderbook.1.{s.replace('/', '')}" for s in _symbols()]
    sub = json.dumps({"op": "subscribe", "args": topics})
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while _running:
            try:
                async with session.ws_connect(url, heartbeat=20) as ws:
                    await ws.send_str(sub)
                    logger.info("Bybit orderbook.1 WS connected.")
                    async for msg in ws:
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        payload = json.loads(msg.data)
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
                        update_top_of_book(
                            "bybit",
                            symbol,
                            bid=float(bids[0][0]),
                            bid_qty=float(bids[0][1]),
                            ask=float(asks[0][0]),
                            ask_qty=float(asks[0][1]),
                        )
                        _inc_messages()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Bybit orderbook WS error: %s — retry 3s", exc)
                await asyncio.sleep(3)


async def _kraken_ticker_poll_loop() -> None:
    """REST poll fallback for Kraken (WS v2 optional later)."""
    pairs = {"BTC": "XBTUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while _running:
            for asset, pair in pairs.items():
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
                            if bid > 0 and ask > 0:
                                update_top_of_book(
                                    "kraken",
                                    f"{asset}/USDT",
                                    bid=bid,
                                    bid_qty=1.0,
                                    ask=ask,
                                    ask_qty=1.0,
                                )
                                _inc_messages()
                except (aiohttp.ClientError, TypeError, ValueError):
                    logger.debug("optional operation skipped", exc_info=True)
            await asyncio.sleep(1)


async def start_exchange_ws_hub() -> None:
    global _running, _tasks
    if not _enabled():
        logger.info("Exchange WS hub disabled (EXCHANGE_WS_ENABLED=false).")
        return
    if _running:
        return
    _running = True
    _tasks = [
        asyncio.create_task(_binance_book_ticker_loop(), name="ws-binance-book"),
        asyncio.create_task(_okx_bbo_loop(), name="ws-okx-bbo"),
        asyncio.create_task(_bybit_orderbook_loop(), name="ws-bybit-book"),
        asyncio.create_task(_kraken_ticker_poll_loop(), name="poll-kraken"),
    ]
    logger.info("Exchange WS hub started | venues=binance,okx,bybit,kraken symbols=%d", len(_symbols()))


async def stop_exchange_ws_hub() -> None:
    global _running, _tasks
    _running = False
    for task in _tasks:
        task.cancel()
    if _tasks:
        await asyncio.gather(*_tasks, return_exceptions=True)
    _tasks = []
    logger.info("Exchange WS hub stopped.")
