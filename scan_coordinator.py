"""
BLACKDARK — Shared arbitrage scan coordinator.

Prevents triple/quadruple rescans across instant alerts, Telegram, and B2B hooks.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import config

_lock = asyncio.Lock()
_scan_cache: dict[str, Any] | None = None
_scan_cache_at: float = 0.0
_scan_inflight: asyncio.Task | None = None


def _ttl_sec() -> float:
    return max(0.25, float(getattr(config, "SCAN_CACHE_TTL_SEC", 1.0)))


def _cache_valid() -> bool:
    return _scan_cache is not None and (time.monotonic() - _scan_cache_at) < _ttl_sec()


async def get_shared_scan(
    *,
    quote_amount: float | None = None,
    prefer_live: bool | None = None,
    force_rest: bool = False,
    min_profit_usdt: float | None = None,
    profitable_only: bool = False,
    force_refresh: bool = False,
) -> dict[str, Any]:
    global _scan_cache, _scan_cache_at, _scan_inflight

    if not force_refresh and _cache_valid():
        return dict(_scan_cache or {})

    async with _lock:
        if not force_refresh and _cache_valid():
            return dict(_scan_cache or {})

        if _scan_inflight is not None and not _scan_inflight.done():
            return await _scan_inflight

        async def _run() -> dict[str, Any]:
            from arbitrage_service import scan_arbitrage_opportunities

            live = (
                prefer_live
                if prefer_live is not None
                else getattr(config, "ARBITRAGE_PREFER_LIVE", False)
            )
            return await scan_arbitrage_opportunities(
                quote_amount,
                prefer_live=live,
                force_rest=force_rest,
                min_profit_usdt=min_profit_usdt,
                profitable_only=profitable_only,
            )

        _scan_inflight = asyncio.create_task(_run(), name="shared-arb-scan")
        try:
            result = await _scan_inflight
        finally:
            _scan_inflight = None

        _scan_cache = result
        _scan_cache_at = time.monotonic()
        return dict(result)


def coordinator_stats() -> dict[str, Any]:
    return {
        "ttl_sec": _ttl_sec(),
        "cache_valid": _cache_valid(),
        "cache_age_sec": round(time.monotonic() - _scan_cache_at, 2) if _scan_cache_at else None,
        "scan_inflight": _scan_inflight is not None and not _scan_inflight.done(),
    }
