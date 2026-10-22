"""
mempool.space public API (no key) — Bitcoin recommended fees and block tip.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.MempoolSpace")

_BASE = "https://mempool.space/api"
_TIMEOUT = aiohttp.ClientTimeout(total=12)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SEC = 60.0


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > _CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


async def _get_json(path: str) -> Any | None:
    url = f"{_BASE}{path}"
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=_HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.debug("mempool.space HTTP %s %s", resp.status, path)
                    return None
                return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def fetch_recommended_fees() -> dict[str, Any] | None:
    cached = _cache_get("fees")
    if cached is not None:
        return cached
    data = await _get_json("/v1/fees/recommended")
    if not isinstance(data, dict):
        return None
    row = {
        "fastest_sat_vb": data.get("fastestFee"),
        "half_hour_sat_vb": data.get("halfHourFee"),
        "hour_sat_vb": data.get("hourFee"),
        "economy_sat_vb": data.get("economyFee"),
        "minimum_sat_vb": data.get("minimumFee"),
        "unit": "sat/vB",
    }
    _cache_set("fees", row)
    return row


async def fetch_block_tip_height() -> int | None:
    cached = _cache_get("tip_height")
    if cached is not None:
        return int(cached)
    data = await _get_json("/blocks/tip/height")
    if isinstance(data, int):
        _cache_set("tip_height", data)
        return data
    if isinstance(data, str) and data.isdigit():
        val = int(data)
        _cache_set("tip_height", val)
        return val
    return None


async def fetch_btc_mempool_context() -> dict[str, Any]:
    fees = await fetch_recommended_fees()
    height = await fetch_block_tip_height()
    ok = fees is not None or height is not None
    return {
        "ok": ok,
        "source": "mempool.space",
        "attribution": "Data: mempool.space",
        "no_api_key": True,
        "recommended_fees": fees,
        "block_tip_height": height,
        "fetched_ok": ok,
    }
