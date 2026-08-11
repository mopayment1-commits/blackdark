"""
BLACKDARK — B2B WebSocket Stream (Tier 2 institutional).

Low-latency push channel for hedge funds / prop desks:
  arbitrage · oracle · whale · heartbeat · snapshot
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.B2BWebSocket")

_dedupe_cache: dict[str, float] = {}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _cooldown_sec() -> float:
    return max(0.5, float(getattr(config, "B2B_WS_EVENT_COOLDOWN_SEC", 3)))


def _dedupe_ok(key: str) -> bool:
    now = time.monotonic()
    last = _dedupe_cache.get(key, 0.0)
    if now - last < _cooldown_sec():
        return False
    _dedupe_cache[key] = now
    return True


@dataclass
class B2BClient:
    websocket: Any
    api_key: str
    is_demo: bool
    connected_at: str = field(default_factory=_utcnow_iso)
    events_sent: int = 0


class B2BWebSocketHub:
    """In-process pub/sub for authenticated B2B WebSocket clients."""

    def __init__(self) -> None:
        self._clients: list[B2BClient] = []
        self._lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(), name="b2b-ws-heartbeat")
        logger.info("B2B WebSocket hub started")

    async def stop(self) -> None:
        self._running = False
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            await asyncio.gather(self._heartbeat_task, return_exceptions=True)
            self._heartbeat_task = None
        async with self._lock:
            clients = list(self._clients)
            self._clients.clear()
        for client in clients:
            try:
                await client.websocket.close()
            except Exception:
                pass
        logger.info("B2B WebSocket hub stopped")

    async def register(self, websocket: Any, api_key: str, *, is_demo: bool) -> B2BClient:
        max_conn = int(getattr(config, "B2B_WS_MAX_CONNECTIONS", 50))
        async with self._lock:
            if len(self._clients) >= max_conn:
                raise RuntimeError("B2B WebSocket connection limit reached")
        client = B2BClient(websocket=websocket, api_key=api_key, is_demo=is_demo)
        async with self._lock:
            self._clients.append(client)
        await self._send(
            client,
            {
                "type": "connected",
                "channel": "b2b_institutional_stream",
                "feed_version": config.B2B_FEED_VERSION,
                "demo_mode": is_demo,
                "latency_target_ms": int(getattr(config, "B2B_WS_LATENCY_TARGET_MS", 500)),
                "timestamp": _utcnow_iso(),
            },
        )
        await self._send_snapshot(client)
        logger.info("B2B WS client connected | demo=%s total=%d", is_demo, len(self._clients))
        return client

    async def unregister(self, client: B2BClient) -> None:
        async with self._lock:
            try:
                self._clients.remove(client)
            except ValueError:
                pass
        logger.info("B2B WS client disconnected | total=%d", len(self._clients))

    async def _send(self, client: B2BClient, payload: dict[str, Any]) -> None:
        await client.websocket.send_json(payload)
        client.events_sent += 1

    async def _send_snapshot(self, client: B2BClient) -> None:
        from whale_tracker import InstitutionalDataExporter

        exporter = InstitutionalDataExporter()
        limit = config.B2B_DEMO_EXPORT_LIMIT if client.is_demo else min(25, config.B2B_DEFAULT_EXPORT_LIMIT)
        try:
            feed = await exporter.export_institutional_feed(provided_key=client.api_key, limit=limit)
            await self._send(
                client,
                {
                    "type": "snapshot",
                    "record_count": feed.get("record_count"),
                    "feed_version": feed.get("feed_version"),
                    "signature": feed.get("signature"),
                    "records": feed.get("records"),
                    "timestamp": _utcnow_iso(),
                },
            )
        except Exception:
            logger.exception("B2B WS snapshot failed")

    async def broadcast(self, event_type: str, payload: dict[str, Any], *, dedupe_key: str | None = None) -> int:
        if dedupe_key and not _dedupe_ok(dedupe_key):
            return 0

        envelope = {
            "type": event_type,
            "timestamp": _utcnow_iso(),
            "feed_version": config.B2B_FEED_VERSION,
            **payload,
        }

        async with self._lock:
            clients = list(self._clients)
        if not clients:
            return 0

        sent = 0
        dead: list[B2BClient] = []
        for client in clients:
            try:
                await self._send(client, envelope)
                sent += 1
            except Exception:
                dead.append(client)
        for client in dead:
            await self.unregister(client)
        if sent:
            logger.debug("B2B WS broadcast | type=%s sent=%d", event_type, sent)
        return sent

    async def _heartbeat_loop(self) -> None:
        interval = max(5, int(getattr(config, "B2B_WS_HEARTBEAT_SEC", 15)))
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self.broadcast(
                    "heartbeat",
                    {
                        "clients": len(self._clients),
                        "status": "live",
                    },
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("B2B WS heartbeat failed")

    def stats(self) -> dict[str, Any]:
        return {
            "enabled": getattr(config, "B2B_WS_ENABLED", True),
            "running": self._running,
            "connected_clients": len(self._clients),
            "demo_clients": sum(1 for c in self._clients if c.is_demo),
            "heartbeat_sec": int(getattr(config, "B2B_WS_HEARTBEAT_SEC", 15)),
            "event_cooldown_sec": _cooldown_sec(),
            "latency_target_ms": int(getattr(config, "B2B_WS_LATENCY_TARGET_MS", 500)),
        }


_hub: B2BWebSocketHub | None = None


def get_b2b_ws_hub() -> B2BWebSocketHub:
    global _hub
    if _hub is None:
        _hub = B2BWebSocketHub()
    return _hub


async def start_b2b_websocket_hub() -> None:
    if not getattr(config, "B2B_WS_ENABLED", True):
        return
    await get_b2b_ws_hub().start()


async def stop_b2b_websocket_hub() -> None:
    global _hub
    if _hub is not None:
        await _hub.stop()


async def publish_arbitrage_opportunity(opportunity: dict[str, Any]) -> int:
    if not getattr(config, "B2B_WS_ENABLED", True):
        return 0
    key = "|".join(
        [
            str(opportunity.get("kind") or ""),
            str(opportunity.get("asset") or ""),
            str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or ""),
            str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or ""),
        ]
    )
    return await get_b2b_ws_hub().broadcast(
        "arbitrage_opportunity",
        {"opportunity": opportunity},
        dedupe_key=key or None,
    )


async def publish_oracle_signal(signal: dict[str, Any]) -> int:
    if not getattr(config, "B2B_WS_ENABLED", True):
        return 0
    key = f"oracle|{signal.get('asset')}|{signal.get('oracle_verdict') or signal.get('verdict')}"
    return await get_b2b_ws_hub().broadcast(
        "oracle_signal",
        {"signal": signal},
        dedupe_key=key,
    )
