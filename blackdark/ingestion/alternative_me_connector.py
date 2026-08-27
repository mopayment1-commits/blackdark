"""
Alternative.me API connector — sentiment data source (#14).

NOT a standalone feature. Fear & Greed Index feeds Alpha Engine (#13).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from data_lake import store_snapshot
from database import upsert_ingestion_health

logger = logging.getLogger("BLACKDARK.AlternativeMe")

BASE_URL = "https://api.alternative.me/fng"
_CACHE: dict[str, tuple[float, Any]] = {}
_RATE_LIMIT_UNTIL = 0.0
_DEFAULT_TTL = int(os.getenv("ALTERNATIVE_ME_CACHE_TTL_SEC", "3600"))
_MAX_TTL = 86400
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cache_ttl() -> int:
    raw = int(os.getenv("ALTERNATIVE_ME_CACHE_TTL_SEC", str(_DEFAULT_TTL)))
    return max(60, min(_MAX_TTL, raw))


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if row and time.time() - row[0] < _cache_ttl():
        return row[1]
    return None


def _cache_get_stale(key: str) -> Any | None:
    row = _CACHE.get(key)
    return row[1] if row else None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


def _synthetic_fallback() -> dict[str, Any]:
    """Neutral fallback when API unavailable."""
    return {
        "value": 50,
        "value_classification": "Neutral",
        "timestamp": _utcnow(),
        "source": "synthetic_neutral",
        "fallback": True,
    }


async def _request(*, limit: int = 1, cache_key: str) -> dict[str, Any]:
    global _RATE_LIMIT_UNTIL
    cached = _cache_get(cache_key)
    if cached is not None:
        return {**cached, "cache_hit": True}

    if time.time() < _RATE_LIMIT_UNTIL:
        stale = _cache_get_stale(cache_key)
        if stale:
            return {**stale, "cache_hit": True, "stale_fallback": True, "rate_limited": True}
        return {"ok": False, "error": "rate_limited", "rows": [_synthetic_fallback()]}

    url = BASE_URL
    timeout = aiohttp.ClientTimeout(total=5)
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.get(url, params={"limit": str(limit)}) as resp:
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                if resp.status == 429:
                    _RATE_LIMIT_UNTIL = time.time() + 30
                    stale = _cache_get_stale(cache_key)
                    rows = (stale or {}).get("rows") or [_synthetic_fallback()]
                    return {
                        "ok": True,
                        "rows": rows,
                        "stale_fallback": True,
                        "rate_limited": True,
                        "latency_ms": latency_ms,
                    }
                if resp.status != 200:
                    stale = _cache_get_stale(cache_key)
                    rows = (stale or {}).get("rows") or [_synthetic_fallback()]
                    return {
                        "ok": True,
                        "rows": rows,
                        "stale_fallback": True,
                        "http_status": resp.status,
                        "latency_ms": latency_ms,
                    }
                data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError) as exc:
        stale = _cache_get_stale(cache_key)
        rows = (stale or {}).get("rows") or [_synthetic_fallback()]
        return {"ok": True, "rows": rows, "stale_fallback": True, "error": str(exc)}

    rows = []
    for row in (data.get("data") or [])[:limit]:
        if not isinstance(row, dict):
            continue
        try:
            val = int(row.get("value") or 50)
        except (TypeError, ValueError):
            val = 50
        rows.append(
            {
                "value": max(0, min(100, val)),
                "value_classification": row.get("value_classification") or "Unknown",
                "timestamp": row.get("timestamp"),
                "source": "alternative.me",
            }
        )
    if not rows:
        rows = [_synthetic_fallback()]

    result = {
        "ok": True,
        "rows": rows,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "timestamp": _utcnow(),
        "cache_hit": False,
    }
    _cache_set(cache_key, result)
    return result


def fear_greed_alpha_score(value: int) -> float:
    """Map F&G 0-100 to alpha-friendly 0-100 (contrarian lean at extremes)."""
    v = max(0, min(100, value))
    if v <= 25:
        return 55 + (25 - v) * 1.2  # extreme fear → mild bullish tilt
    if v >= 75:
        return 45 - (v - 75) * 1.2  # extreme greed → mild bearish tilt
    return 50 + (50 - v) * 0.3


async def fetch_fear_greed_index(*, limit: int = 1) -> dict[str, Any]:
    """Normalized Fear & Greed for Alpha Engine input."""
    t0 = time.perf_counter()
    resp = await _request(limit=limit, cache_key=f"fng:{limit}")
    row = (resp.get("rows") or [_synthetic_fallback()])[0]
    value = int(row.get("value") or 50)
    out = {
        "ok": True,
        "surface": "alternative_me_fear_greed",
        "alpha_engine_role": "sentiment_input",
        "value": value,
        "label": row.get("value_classification") or "Neutral",
        "alpha_score": round(fear_greed_alpha_score(value), 2),
        "source": row.get("source") or "alternative.me",
        "fallback": bool(row.get("fallback") or resp.get("stale_fallback")),
        "cache_hit": resp.get("cache_hit"),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 3.0,
        "timestamp": _utcnow(),
    }
    return out


async def run_alternative_me_ingest() -> dict[str, Any]:
    fg = await fetch_fear_greed_index()
    payload = {
        "fear_greed_index": fg.get("value"),
        "fear_greed_label": fg.get("label"),
        "alpha_score": fg.get("alpha_score"),
        "source": "alternative_me_connector",
        "ingested_at": _utcnow(),
    }
    ok = bool(fg.get("ok"))
    await store_snapshot("fear_greed", "sentiment", payload, status="ok" if ok else "degraded")
    await upsert_ingestion_health(
        "fear_greed",
        "sentiment",
        ok=ok,
        error=None if ok else "alternative_me_ingest_failed",
    )
    return {"ok": ok, "surface": "alternative_me_ingest", **fg}


def alternative_me_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "alternative_me_connector",
        "role": "alpha_engine_sentiment_input",
        "cache_ttl_seconds": _cache_ttl(),
        "cache_entries": len(_CACHE),
        "fallback_chain": ["alternative.me_api", "stale_cache", "synthetic_neutral"],
        "timestamp": _utcnow(),
    }
