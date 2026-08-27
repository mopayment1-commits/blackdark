"""
Polygon.io API connector (#86) — silent macro/market ingestion.

NOT a branded surface. Provides equities/macro context for Decision Engine (#48).
Users see natural language like "AI detected S&P 500 down 1.2% — macro risk elevated".
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.PolygonIO")

BASE_URL = "https://api.polygon.io"
_CACHE = IngestionCache(default_ttl_sec=900, max_ttl_sec=86400)
_SPY_TICKER = "SPY"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_IO_API_KEY") or "").strip()
    return key or None


async def _polygon_get(path: str, *, params: dict[str, Any] | None = None, cache_key_str: str, ttl: int) -> dict[str, Any]:
    key = _api_key()
    merged = dict(params or {})
    if key:
        merged["apiKey"] = key
    return await _CACHE.http_get_json(
        f"{BASE_URL}{path}",
        params=merged,
        timeout_sec=3.0,
        cache_key=cache_key_str,
        ttl=ttl,
        source_slug="polygon_io",
    )


async def _fallback_macro_context() -> dict[str, Any]:
    """Fallback: Investing.com RSS high-impact macro tags."""
    from blackdark.ingestion.investing_com_connector import fetch_investing_news_context

    news = await fetch_investing_news_context(limit=30)
    if not news.get("ok"):
        return {"ok": False, "error": "macro_fallback_unavailable"}
    high = [a for a in (news.get("articles") or []) if a.get("high_impact")]
    tags: list[str] = []
    for row in high[:5]:
        tags.extend(row.get("impact_tags") or [])
    return {
        "ok": True,
        "source": "investing_com_fallback",
        "high_impact_tags": sorted(set(tags))[:8],
        "ai_context_line": news.get("ai_context_line"),
        "fallback": True,
    }


async def fetch_polygon_macro_context(*, ticker: str = _SPY_TICKER) -> dict[str, Any]:
    """S&P 500 proxy via SPY snapshot — macro input for crypto decision context."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("POLYGON_IO_CACHE_TTL_SEC", 900)
    ck = cache_key("polygon_macro", ticker)
    cached = _CACHE.get(ck, ttl=ttl)
    if cached:
        return {**cached, "cache_hit": True}

    if not _api_key():
        fb = await _fallback_macro_context()
        elapsed = time.perf_counter() - t0
        return {
            "ok": fb.get("ok", False),
            "feature": "#86",
            "ingestion_role": "macro_context",
            "ticker": ticker,
            "data_state": "DEGRADED",
            "fallback": fb,
            "headline": fb.get("ai_context_line"),
            "latency_ms": round(elapsed * 1000, 1),
            "sla_met": elapsed <= 3.0,
            "timestamp": _utcnow(),
        }

    resp = await _polygon_get(
        f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}",
        cache_key_str=cache_key("polygon_snapshot", ticker),
        ttl=ttl,
    )
    if not resp.get("ok"):
        fb = await _fallback_macro_context()
        stale = _CACHE.get_stale(ck)
        if stale:
            return {**stale, "ok": True, "stale_fallback": True, "fallback": fb}
        elapsed = time.perf_counter() - t0
        return {
            "ok": False,
            "feature": "#86",
            "error": resp.get("error"),
            "fallback": fb if fb.get("ok") else None,
            "data_state": "MISSING",
            "latency_ms": round(elapsed * 1000, 1),
            "timestamp": _utcnow(),
        }

    payload = resp.get("data") or {}
    tick = payload.get("ticker") or {}
    change_pct = tick.get("todaysChangePerc")
    try:
        change_f = float(change_pct) if change_pct is not None else None
    except (TypeError, ValueError):
        change_f = None

    headline = None
    if change_f is not None:
        direction = "down" if change_f < 0 else "up"
        headline = (
            f"AI detected S&P 500 {direction} {abs(change_f):.1f}% — "
            "macro risk context elevated for crypto"
        )

    elapsed = time.perf_counter() - t0
    result = {
        "ok": True,
        "feature": "#86",
        "ingestion_role": "macro_context",
        "ticker": ticker,
        "change_pct": round(change_f, 3) if change_f is not None else None,
        "day_close": (tick.get("day") or {}).get("c"),
        "prev_close": (tick.get("prevDay") or {}).get("c"),
        "headline": headline,
        "data_state": "LIVE",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
    _CACHE.set(ck, result)
    return result


def polygon_io_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "polygon_io_ingestion_connector",
        "role": "macro_context_input",
        "feature": "#86",
        "api_key_configured": bool(_api_key()),
        "cache_ttl_seconds": _CACHE.ttl("POLYGON_IO_CACHE_TTL_SEC", 900),
        "circuit_open": is_open("polygon_io"),
        "fallback_chain": ["polygon_io", "stale_cache", "investing_com_rss"],
        "timestamp": _utcnow(),
    }
