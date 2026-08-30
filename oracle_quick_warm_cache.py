"""Oracle /quick warm cache — pre-fetch top assets into shared Redis (memory fallback)."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("BLACKDARK.OracleWarmCache")

_scheduler: AsyncIOScheduler | None = None
_started = False
_warm_lock = asyncio.Lock()

_ORACLE_WARM_TOP20 = (
    "BTC",
    "ETH",
    "SOL",
    "BNB",
    "XRP",
    "ADA",
    "DOGE",
    "AVAX",
    "DOT",
    "LINK",
    "ARB",
    "OP",
    "AAVE",
    "UNI",
    "ATOM",
    "LTC",
    "NEAR",
    "APT",
    "INJ",
    "SUI",
)
_ORACLE_WARM_LANGS = ("en", "ar")
_ORACLE_WARM_UX_MODE = "beginner"
_ORACLE_WARM_INTERVAL_SEC = int(os.getenv("ORACLE_WARM_INTERVAL_SEC", "60"))


def _enabled() -> bool:
    return os.getenv("ORACLE_WARM_CACHE_ENABLED", "true").lower() in {"1", "true", "yes"}


def oracle_warm_assets(limit: int = 20) -> list[str]:
    import config

    universe = {str(a).upper() for a in config.UNIVERSE_ASSETS}
    out: list[str] = []
    for asset in _ORACLE_WARM_TOP20:
        if asset in universe and asset not in out:
            out.append(asset)
        if len(out) >= limit:
            return out
    for asset in sorted(universe):
        if asset not in out:
            out.append(asset)
        if len(out) >= limit:
            break
    return out[:limit]


async def _warm_one(asset: str, lang: str, ux_mode: str) -> bool:
    from dashboard import (
        _attach_quick_certificate,
        _attach_quick_freshness,
        _compute_oracle_quick_payload,
    )
    from market_context import normalize_oracle_symbol
    from security_sanitize import sanitize_oracle_payload
    from viral_capacity import quick_cache_set

    resolved, pair = normalize_oracle_symbol(asset)
    try:
        payload = await _compute_oracle_quick_payload(resolved, pair, lang, ux_mode)
    except Exception:
        logger.debug("Oracle warm skip | asset=%s lang=%s", resolved, lang, exc_info=True)
        return False
    _attach_quick_certificate(payload)
    payload = _attach_quick_freshness(payload, resolved)
    quick_cache_set(resolved, lang, ux_mode, sanitize_oracle_payload(payload))
    return True


async def warm_oracle_quick_cache_once() -> dict[str, Any]:
    """Populate shared oracle quick cache (Redis when available, else per-process memory)."""
    if not _enabled():
        return {"ok": False, "reason": "disabled"}
    from viral_capacity import cache_backend

    assets = oracle_warm_assets()
    warmed = 0
    failed = 0
    async with _warm_lock:
        for asset in assets:
            for lang in _ORACLE_WARM_LANGS:
                if await _warm_one(asset, lang, _ORACLE_WARM_UX_MODE):
                    warmed += 1
                else:
                    failed += 1
    logger.info(
        "Oracle quick warm cache | backend=%s assets=%d warmed=%d failed=%d",
        cache_backend(),
        len(assets),
        warmed,
        failed,
    )
    return {
        "ok": True,
        "backend": cache_backend(),
        "assets": len(assets),
        "warmed": warmed,
        "failed": failed,
    }


async def _warm_job() -> None:
    try:
        await warm_oracle_quick_cache_once()
    except Exception:
        logger.exception("Oracle quick warm cache job failed")


def start_oracle_quick_warm_scheduler(loop: asyncio.AbstractEventLoop | None = None) -> dict[str, Any]:
    global _scheduler, _started
    if _started or not _enabled():
        return {"started": False, "reason": "disabled_or_already_started"}
    _scheduler = AsyncIOScheduler(event_loop=loop or asyncio.get_event_loop())
    _scheduler.add_job(
        _warm_job,
        IntervalTrigger(seconds=max(10, _ORACLE_WARM_INTERVAL_SEC)),
        id="oracle_quick_warm",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    _started = True
    logger.info("Oracle quick warm scheduler started (interval=%ss)", _ORACLE_WARM_INTERVAL_SEC)
    return {"started": True, "interval_sec": _ORACLE_WARM_INTERVAL_SEC}


def stop_oracle_quick_warm_scheduler() -> None:
    global _scheduler, _started
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    _started = False
