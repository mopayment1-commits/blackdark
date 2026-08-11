"""
BLACKDARK — Exchange ingress guard (anti-DDoS / IP-ban protection).

Prevents parallel REST storms to 100 venues:
- Global exchange concurrency cap
- Per-exchange symbol concurrency cap
- Staggered poll start (jitter)
- Circuit breaker on 429 / rate-limit errors
- Optional proxy rotation (PROXY_URLS)
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time
from typing import Any, Self

import config

logger = logging.getLogger("BLACKDARK.IngressGuard")

_exchange_sem: asyncio.Semaphore | None = None
_symbol_sems: dict[str, asyncio.Semaphore] = {}
_banned_until: dict[str, float] = {}
_error_counts: dict[str, int] = {}
_success_counts: dict[str, int] = {}
_proxy_urls: list[str] = []
_proxy_index = 0


def _enabled() -> bool:
    return getattr(config, "INGRESS_GUARD_ENABLED", True)


def max_exchange_polls() -> int:
    return int(getattr(config, "MAX_CONCURRENT_EXCHANGE_POLLS", 8))


def max_symbol_polls() -> int:
    return int(getattr(config, "MAX_CONCURRENT_SYMBOL_POLLS_PER_EXCHANGE", 4))


def ban_cooldown_sec() -> float:
    return float(getattr(config, "EXCHANGE_BAN_COOLDOWN_SEC", 3600))


def stagger_ms() -> float:
    return float(getattr(config, "EXCHANGE_POLL_STAGGER_MS", 150))


def _exchange_semaphore() -> asyncio.Semaphore:
    global _exchange_sem
    if _exchange_sem is None:
        _exchange_sem = asyncio.Semaphore(max_exchange_polls())
    return _exchange_sem


def _symbol_semaphore(exchange_id: str) -> asyncio.Semaphore:
    ex = exchange_id.lower()
    if ex not in _symbol_sems:
        _symbol_sems[ex] = asyncio.Semaphore(max_symbol_polls())
    return _symbol_sems[ex]


def _load_proxies() -> list[str]:
    global _proxy_urls
    if _proxy_urls:
        return _proxy_urls
    raw = os.getenv("PROXY_URLS", "").strip()
    if not raw:
        return []
    _proxy_urls = [p.strip() for p in raw.split(",") if p.strip()]
    return _proxy_urls


def proxy_rotation_enabled() -> bool:
    return os.getenv("PROXY_ROTATION_ENABLED", "false").lower() in {"1", "true", "yes"}


def get_next_proxy() -> dict[str, str] | None:
    """Round-robin HTTP/HTTPS proxy for CCXT/aiohttp."""
    if not proxy_rotation_enabled():
        return None
    urls = _load_proxies()
    if not urls:
        return None
    global _proxy_index
    url = urls[_proxy_index % len(urls)]
    _proxy_index += 1
    return {"http": url, "https": url}


def is_rate_limit_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    if "429" in text or "rate limit" in text or "too many requests" in text:
        return True
    if "cloudflare" in text or "ddos" in text or "banned" in text:
        return True
    name = type(exc).__name__.lower()
    return "ratelimit" in name or "ddos" in name


def is_exchange_banned(exchange_id: str) -> bool:
    ex = exchange_id.lower()
    until = _banned_until.get(ex, 0.0)
    if until <= time.monotonic():
        _banned_until.pop(ex, None)
        return False
    return True


def ban_exchange(exchange_id: str, *, reason: str = "rate_limit", cooldown_sec: float | None = None) -> None:
    ex = exchange_id.lower()
    cd = cooldown_sec if cooldown_sec is not None else ban_cooldown_sec()
    _banned_until[ex] = time.monotonic() + cd
    logger.warning("Exchange ingress ban | exchange=%s reason=%s cooldown_sec=%.0f", ex, reason, cd)


def record_exchange_success(exchange_id: str) -> None:
    ex = exchange_id.lower()
    _success_counts[ex] = _success_counts.get(ex, 0) + 1
    _error_counts[ex] = 0


def record_exchange_errors(exchange_id: str, errors: list[BaseException]) -> None:
    ex = exchange_id.lower()
    rate_hits = sum(1 for e in errors if is_rate_limit_error(e))
    if rate_hits:
        _error_counts[ex] = _error_counts.get(ex, 0) + rate_hits
        if _error_counts[ex] >= int(getattr(config, "EXCHANGE_RATE_LIMIT_STRIKES", 3)):
            ban_exchange(ex, reason="rate_limit_strikes")
    elif errors:
        _error_counts[ex] = _error_counts.get(ex, 0) + 1


async def stagger_before_poll(exchange_id: str) -> None:
    if not _enabled():
        return
    base = stagger_ms() / 1000.0
    jitter = secrets.SystemRandom().uniform(0, base * 2)
    slot = (hash(exchange_id) % 17) * (base / 17)
    await asyncio.sleep(jitter + slot)


class exchange_poll_slot:
    """Global cap on concurrent exchange REST poll workers."""

    def __init__(self, exchange_id: str) -> None:
        self.exchange_id = exchange_id.lower()
        self._sem = _exchange_semaphore()

    async def __aenter__(self) -> Self:
        if _enabled():
            await self._sem.acquire()
        return self

    async def __aexit__(self, *args: object) -> None:
        if _enabled():
            self._sem.release()


class symbol_poll_slot:
    """Per-exchange cap on concurrent symbol fetches."""

    def __init__(self, exchange_id: str) -> None:
        self.exchange_id = exchange_id.lower()
        self._sem = _symbol_semaphore(exchange_id)

    async def __aenter__(self) -> Self:
        if _enabled():
            await self._sem.acquire()
        return self

    async def __aexit__(self, *args: object) -> None:
        if _enabled():
            self._sem.release()


def ingress_guard_status() -> dict[str, Any]:
    now = time.monotonic()
    banned = {
        ex: round(until - now, 1)
        for ex, until in _banned_until.items()
        if until > now
    }
    return {
        "enabled": _enabled(),
        "max_concurrent_exchange_polls": max_exchange_polls(),
        "max_concurrent_symbol_polls_per_exchange": max_symbol_polls(),
        "stagger_ms": stagger_ms(),
        "ban_cooldown_sec": ban_cooldown_sec(),
        "proxy_rotation_enabled": proxy_rotation_enabled(),
        "proxy_pool_size": len(_load_proxies()),
        "banned_exchanges": banned,
        "error_strikes": dict(_error_counts),
        "success_totals": dict(_success_counts),
        "policy": (
            "REST polling is capped and staggered. WS venues (binance/okx/bybit) skip REST spot. "
            "Enable PROXY_ROTATION_ENABLED + PROXY_URLS for IP rotation in production."
        ),
    }
