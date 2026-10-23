"""
FRED (Federal Reserve Economic Data) API — macro context (rates, CPI, GDP).

Requires free API key: https://fred.stlouisfed.org/docs/api/api_key.html
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

from config import (
    DATA_DIR,
    FRED_API_KEY,
    FRED_CACHE_TTL_SEC,
    FRED_DAILY_LIMIT,
    FRED_RPS_LIMIT,
)

logger = logging.getLogger("BLACKDARK.FRED")

_BASE = "https://api.stlouisfed.org/fred/series/observations"
_TIMEOUT = aiohttp.ClientTimeout(total=14)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

_USAGE_PATH = DATA_DIR / "fred_api_usage.json"
_CACHE: dict[str, tuple[float, Any]] = {}
_RPS_TIMES: deque[float] = deque(maxlen=FRED_RPS_LIMIT * 2)

_SERIES: dict[str, dict[str, Any]] = {
    "fed_funds_rate": {
        "series_id": "FEDFUNDS",
        "title": "Federal funds effective rate",
        "unit": "percent",
    },
    "cpi": {
        "series_id": "CPIAUCSL",
        "title": "Consumer Price Index (all urban)",
        "unit": "index",
        "yoy": True,
    },
    "gdp": {
        "series_id": "GDP",
        "title": "Gross Domestic Product",
        "unit": "billions_usd",
    },
    "treasury_10y": {
        "series_id": "DGS10",
        "title": "10-Year Treasury constant maturity",
        "unit": "percent",
    },
}


def _utc_day() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _load_usage() -> dict[str, Any]:
    try:
        if _USAGE_PATH.exists():
            raw = json.loads(_USAGE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"day": _utc_day(), "count": 0}


def _save_usage(row: dict[str, Any]) -> None:
    try:
        _USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _USAGE_PATH.write_text(json.dumps(row), encoding="utf-8")
    except OSError:
        logger.debug("fred usage persist failed")


def usage_stats() -> dict[str, Any]:
    row = _load_usage()
    day = _utc_day()
    count = int(row.get("count") or 0) if row.get("day") == day else 0
    return {
        "configured": bool(FRED_API_KEY),
        "day_utc": day,
        "calls_today": count,
        "daily_limit": FRED_DAILY_LIMIT,
        "rps_limit": FRED_RPS_LIMIT,
        "remaining_today": max(0, FRED_DAILY_LIMIT - count),
        "attribution": "Data: Federal Reserve Economic Data (FRED)",
    }


def _try_consume_quota() -> bool:
    if not FRED_API_KEY:
        return False
    now = time.time()
    while _RPS_TIMES and now - _RPS_TIMES[0] > 1.0:
        _RPS_TIMES.popleft()
    if len(_RPS_TIMES) >= FRED_RPS_LIMIT:
        return False
    row = _load_usage()
    day = _utc_day()
    if row.get("day") != day:
        row = {"day": day, "count": 0}
    count = int(row.get("count") or 0)
    if count >= FRED_DAILY_LIMIT:
        logger.warning("FRED daily limit reached (%s)", FRED_DAILY_LIMIT)
        return False
    row["count"] = count + 1
    row["day"] = day
    _save_usage(row)
    _RPS_TIMES.append(now)
    return True


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > FRED_CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


def _parse_value(raw: str | None) -> float | None:
    if raw in (None, ".", ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


async def _fetch_observations(
    series_id: str,
    *,
    limit: int = 2,
) -> list[dict[str, Any]]:
    if not _try_consume_quota():
        return []
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": str(max(1, min(limit, 24))),
    }
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=_HEADERS) as session:
            async with session.get(_BASE, params=params) as resp:
                if resp.status != 200:
                    logger.debug("FRED HTTP %s series=%s", resp.status, series_id)
                    return []
                data = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return []
    obs = data.get("observations") if isinstance(data, dict) else None
    if not isinstance(obs, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in obs:
        if not isinstance(item, dict):
            continue
        val = _parse_value(item.get("value"))
        if val is None:
            continue
        rows.append({"date": item.get("date"), "value": val})
    return rows


async def _indicator_from_series(key: str, meta: dict[str, Any]) -> dict[str, Any] | None:
    sid = meta["series_id"]
    limit = 14 if meta.get("yoy") else 2
    obs = await _fetch_observations(sid, limit=limit)
    if not obs:
        return None
    latest = obs[0]
    row: dict[str, Any] = {
        "series_id": sid,
        "title": meta.get("title"),
        "unit": meta.get("unit"),
        "date": latest.get("date"),
        "value": latest.get("value"),
    }
    if meta.get("yoy") and len(obs) >= 13:
        try:
            yoy = (float(latest["value"]) / float(obs[12]["value"]) - 1.0) * 100.0
            row["yoy_change_pct"] = round(yoy, 2)
        except (TypeError, ValueError, ZeroDivisionError, KeyError):
            pass
    if len(obs) >= 2 and not meta.get("yoy"):
        try:
            prev = float(obs[1]["value"])
            cur = float(latest["value"])
            if prev != 0:
                row["change_from_prior"] = round(cur - prev, 4)
        except (TypeError, ValueError, KeyError):
            pass
    return row


async def fetch_macro_context() -> dict[str, Any]:
    """Inflation (CPI YoY), policy rate, GDP level, 10Y yield — cached bundle."""
    stats = usage_stats()
    if not stats["configured"]:
        return {"ok": False, "error": "not_configured", "usage": stats}
    if stats["remaining_today"] <= 0:
        return {"ok": False, "error": "daily_limit_exceeded", "usage": stats}

    cached = _cache_get("macro_context")
    if cached is not None:
        return cached

    indicators: dict[str, Any] = {}
    for key, meta in _SERIES.items():
        ind = await _indicator_from_series(key, meta)
        if ind:
            indicators[key] = ind

    out = {
        "ok": bool(indicators),
        "fetched_ok": bool(indicators),
        "source": "fred",
        "attribution": stats["attribution"],
        "indicators": indicators,
        "usage": usage_stats(),
    }
    if out["ok"]:
        _cache_set("macro_context", out)
    return out
