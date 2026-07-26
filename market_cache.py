"""
BLACKDARK — In-memory market snapshot cache.

Aggregator/DB writes → scanners read in <5ms instead of re-fetching 21k HTTP calls.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import config

_lock = asyncio.Lock()
_cache: dict[str, Any] | None = None
_cache_at: float = 0.0


def _ttl_sec(source: str | None = None) -> float:
    if source == "live_api":
        return max(1.0, float(getattr(config, "POLL_INTERVAL_SECONDS", 3)))
    return max(0.5, float(getattr(config, "MARKET_CACHE_TTL_SEC", 2.0)))


def _estimate_age_sec(books: dict[str, Any]) -> float:
    newest: float | None = None
    for venue_books in books.values():
        for book in venue_books.values():
            ts = book.get("timestamp")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                if newest is None or age < newest:
                    newest = age
            except (TypeError, ValueError):
                continue
    return max(0.0, newest if newest is not None else 999.0)


def get_cached_snapshots(*, max_age_sec: float | None = None) -> dict[str, Any] | None:
    if _cache is None:
        return None
    source = str((_cache or {}).get("source") or "")
    ttl = max_age_sec if max_age_sec is not None else _ttl_sec(source)
    if time.monotonic() - _cache_at > ttl:
        return None
    return dict(_cache)


def set_cached_snapshots(
    books: dict[str, Any],
    funding: dict[str, Any],
    *,
    source: str,
    age_sec: float | None = None,
) -> None:
    global _cache, _cache_at
    _cache = {
        "books": books,
        "funding": funding,
        "source": source,
        "age_sec": age_sec if age_sec is not None else _estimate_age_sec(books),
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache_at = time.monotonic()


async def refresh_from_database(*, force: bool = False) -> dict[str, Any]:
    cached = get_cached_snapshots()
    if not force and cached and str(cached.get("source")) == "live_api":
        if float(cached.get("age_sec") or 0) <= float(getattr(config, "LIVE_FETCH_STALE_THRESHOLD_SEC", 8)):
            return cached

    from database import fetch_latest_funding_rates, fetch_latest_order_books

    books, funding = await asyncio.gather(
        fetch_latest_order_books(),
        fetch_latest_funding_rates(),
    )
    age_sec = _estimate_age_sec(books)
    if not force and _cache and str(_cache.get("source")) == "live_api":
        if age_sec > float(_cache.get("age_sec") or 999):
            return _cache

    set_cached_snapshots(books, funding, source="database", age_sec=age_sec)
    return _cache or {}


async def get_market_snapshots_cached(*, max_age_sec: float | None = None) -> tuple[dict, dict, str, float]:
    cached = get_cached_snapshots(max_age_sec=max_age_sec)
    if cached:
        return (
            cached["books"],
            cached["funding"],
            str(cached.get("source") or "cache"),
            float(cached.get("age_sec") or 0.0),
        )

    async with _lock:
        cached = get_cached_snapshots(max_age_sec=max_age_sec)
        if cached:
            return (
                cached["books"],
                cached["funding"],
                str(cached.get("source") or "cache"),
                float(cached.get("age_sec") or 0.0),
            )
        payload = await refresh_from_database()
        return (
            payload["books"],
            payload["funding"],
            str(payload.get("source") or "database"),
            float(payload.get("age_sec") or 0.0),
        )


def cache_stats() -> dict[str, Any]:
    age = time.monotonic() - _cache_at if _cache_at else None
    source = (_cache or {}).get("source")
    return {
        "populated": _cache is not None,
        "ttl_sec": _ttl_sec(str(source) if source else None),
        "cache_age_sec": round(age, 2) if age is not None else None,
        "data_age_sec": (_cache or {}).get("age_sec"),
        "source": source,
    }
