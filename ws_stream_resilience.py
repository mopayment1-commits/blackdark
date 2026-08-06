"""
BLACKDARK — WebSocket resilience: exponential backoff + liveliness checks.

Reconnect target: within 1 second. Heartbeat detects frozen streams.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import config

logger = logging.getLogger("BLACKDARK.WSResilience")

StreamHandler = Callable[[Any], Awaitable[None]]


@dataclass
class StreamHealth:
    exchange: str
    stream: str
    connected: bool = False
    last_message_at: float | None = None
    last_reconnect_at: float | None = None
    reconnect_count: int = 0
    frozen_events: int = 0
    latency_ms: float | None = None


_health: dict[str, StreamHealth] = {}
_active_ws: dict[str, Any] = {}
_stale_reconnects = 0


_total_reconnects = 0
_last_backoff_ms: float | None = None
_reconnect_delays_ms: list[float] = []
_max_reconnect_delay_ms: float = 0.0


def _stale_heartbeat_ms() -> float:
    return float(getattr(config, "WS_STALE_HEARTBEAT_MS", 500.0))


def _health_key(exchange: str, stream: str) -> str:
    return f"{exchange.lower()}|{stream}"


def register_ws_connection(exchange: str, stream: str, ws: Any) -> None:
    _active_ws[_health_key(exchange, stream)] = ws


def unregister_ws_connection(exchange: str, stream: str) -> None:
    _active_ws.pop(_health_key(exchange, stream), None)


async def force_stale_reconnect(exchange: str, stream: str) -> bool:
    """Close a frozen WS so run_resilient_stream reconnects within backoff cap."""
    global _stale_reconnects
    key = _health_key(exchange, stream)
    ws = _active_ws.get(key)
    if ws is None:
        return False
    try:
        closed = getattr(ws, "closed", False)
        if not closed:
            await ws.close()
            _stale_reconnects += 1
            health = get_stream_health(exchange, stream)
            health.connected = False
            health.reconnect_count += 1
            logger.warning(
                "WS stale heartbeat reconnect | %s %s idle > %.0fms",
                exchange,
                stream,
                _stale_heartbeat_ms(),
            )
            return True
    except Exception:
        logger.debug("WS force close failed", exc_info=True)
    return False


def get_stream_health(exchange: str, stream: str) -> StreamHealth:
    key = _health_key(exchange, stream)
    if key not in _health:
        _health[key] = StreamHealth(exchange=exchange.lower(), stream=stream)
    return _health[key]


def resilience_stats() -> dict[str, Any]:
    avg_ms = round(sum(_reconnect_delays_ms) / len(_reconnect_delays_ms), 2) if _reconnect_delays_ms else None
    return {
        "stale_heartbeat_ms": _stale_heartbeat_ms(),
        "stale_reconnects": _stale_reconnects,
        "total_reconnects": _total_reconnects,
        "last_backoff_ms": _last_backoff_ms,
        "reconnect_delay_samples": len(_reconnect_delays_ms),
        "avg_reconnect_time_ms": avg_ms,
        "max_reconnect_time_ms": round(_max_reconnect_delay_ms, 2) if _max_reconnect_delay_ms else None,
        "active_connections": len(_active_ws),
        "streams_tracked": len(_health),
    }


def _record_reconnect_delay(delay_sec: float) -> None:
    global _max_reconnect_delay_ms
    ms = round(delay_sec * 1000.0, 2)
    _reconnect_delays_ms.append(ms)
    if len(_reconnect_delays_ms) > 2000:
        _reconnect_delays_ms.pop(0)
    _max_reconnect_delay_ms = max(_max_reconnect_delay_ms, ms)


def all_stream_health() -> list[dict[str, Any]]:
    now = time.monotonic()
    out: list[dict[str, Any]] = []
    for row in _health.values():
        idle_ms = None
        if row.last_message_at:
            idle_ms = round((now - row.last_message_at) * 1000, 1)
        out.append(
            {
                "exchange": row.exchange,
                "stream": row.stream,
                "connected": row.connected,
                "reconnect_count": row.reconnect_count,
                "frozen_events": row.frozen_events,
                "idle_ms": idle_ms,
                "latency_ms": row.latency_ms,
            }
        )
    return out


def _backoff_delay(attempt: int) -> float:
    base = float(getattr(config, "WS_RECONNECT_BASE_SEC", 0.05))
    cap = float(getattr(config, "WS_RECONNECT_MAX_SEC", 1.0))
    delay = min(cap, base * (2 ** min(attempt, 6)))
    return max(0.05, delay)


async def run_resilient_stream(
    exchange: str,
    stream: str,
    connect_and_consume: StreamHandler,
    *,
    running: Callable[[], bool] | None = None,
) -> None:
    """Run a WS consumer with exponential backoff reconnect (cap 1s)."""
    global _total_reconnects, _last_backoff_ms
    health = get_stream_health(exchange, stream)
    attempt = 0

    while running() if running else True:
        try:
            health.connected = True
            health.last_reconnect_at = time.monotonic()
            await connect_and_consume(health)
            attempt = 0
        except asyncio.CancelledError:
            health.connected = False
            raise
        except Exception as exc:
            health.connected = False
            health.reconnect_count += 1
            _total_reconnects += 1
            attempt += 1
            delay = _backoff_delay(attempt)
            _last_backoff_ms = round(delay * 1000, 1)
            _record_reconnect_delay(delay)
            logger.warning(
                "%s %s WS dropped: %s — reconnect in %.0fms (attempt %d)",
                exchange,
                stream,
                exc,
                delay * 1000,
                attempt,
            )
            await asyncio.sleep(delay)


async def liveliness_watchdog(
    *,
    running: Callable[[], bool],
    check_interval_sec: float | None = None,
) -> None:
    """Force reconnect when stream idle exceeds WS_STALE_HEARTBEAT_MS (default 500ms)."""
    stale_ms = _stale_heartbeat_ms()
    timeout = stale_ms / 1000.0
    interval = check_interval_sec or min(0.1, timeout / 2)

    while running():
        now = time.monotonic()
        for health in list(_health.values()):
            if not health.connected or not health.last_message_at:
                continue
            idle = now - health.last_message_at
            if idle > timeout:
                health.frozen_events += 1
                await force_stale_reconnect(health.exchange, health.stream)
                health.last_message_at = now
        await asyncio.sleep(interval)


def record_message(exchange: str, stream: str, *, latency_ms: float | None = None) -> None:
    health = get_stream_health(exchange, stream)
    health.last_message_at = time.monotonic()
    if latency_ms is not None:
        health.latency_ms = round(latency_ms, 2)
