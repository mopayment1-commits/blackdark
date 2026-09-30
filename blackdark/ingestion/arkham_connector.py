"""
Arkham Intelligence connector — entity/flow input for Alpha Engine (#15).

NOT a standalone AI engine. When ARKHAM_API_KEY is set, calls api.arkm.com.
Fallback: whale alerts + institutional flows from platform lake (free-tier proxy).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp
from urllib.parse import urlparse

from path_safety import safe_url_segment

logger = logging.getLogger("BLACKDARK.ArkhamConnector")

ARKHAM_ALLOWED_HOST = "api.arkm.com"
ARKHAM_HTTPS_ORIGIN = f"https://{ARKHAM_ALLOWED_HOST}"
BASE_URL = ARKHAM_HTTPS_ORIGIN
_CACHE: dict[str, tuple[float, Any]] = {}
_RATE_LIMIT_UNTIL = 0.0
_DEFAULT_TTL = int(os.getenv("ARKHAM_CACHE_TTL_SEC", "3600"))
_MAX_TTL = 86400
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}

_ENTITY_QUERIES: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binance",
    "USDT": "tether",
    "USDC": "usd-coin",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("ARKHAM_API_KEY") or "").strip()
    return key or None


def _cache_ttl() -> int:
    raw = int(os.getenv("ARKHAM_CACHE_TTL_SEC", str(_DEFAULT_TTL)))
    return max(60, min(_MAX_TTL, raw))


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if row and time.time() - row[0] < _cache_ttl():
        return row[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


def _assert_arkham_https_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Arkham API requires https, got {parsed.scheme!r}")
    host = (parsed.hostname or "").lower()
    if host != ARKHAM_ALLOWED_HOST:
        raise ValueError(f"Arkham host not allowlisted: {host!r}")
    return url


async def _api_get(url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    global _RATE_LIMIT_UNTIL
    key = _api_key()
    if not key or time.time() < _RATE_LIMIT_UNTIL:
        return None
    try:
        safe_url = _assert_arkham_https_url(url)
    except ValueError:
        return None
    headers = {**_HEADERS, "API-Key": key}
    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(safe_url, params=params) as resp:
                if resp.status == 429:
                    _RATE_LIMIT_UNTIL = time.time() + 60
                    return None
                if resp.status != 200:
                    return None
                return await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        return None


async def _fallback_entity_input(symbol: str) -> dict[str, Any]:
    """Free-tier proxy: whale/flow signals without Arkham API key."""
    from database import fetch_latest_whale_alerts

    sym = symbol.upper()
    alerts = await fetch_latest_whale_alerts(limit=30)
    asset_alerts = [a for a in alerts if str(a.get("asset") or "").upper() == sym]
    inflow = sum(1 for a in asset_alerts if str(a.get("flow_type") or "").lower() in {"in", "deposit"})
    outflow = sum(1 for a in asset_alerts if str(a.get("flow_type") or "").lower() in {"out", "withdrawal"})
    net = inflow - outflow
    # score: more exchange outflows → slightly bullish accumulation signal
    flow_score = 50 + min(20, max(-20, net * 5))

    return {
        "source": "platform_whale_flow_proxy",
        "fallback": True,
        "entity": _ENTITY_QUERIES.get(sym, sym.lower()),
        "whale_alert_count": len(asset_alerts),
        "inflow_signals": inflow,
        "outflow_signals": outflow,
        "entity_flow_score": round(flow_score, 2),
        "alpha_score": round(flow_score, 2),
        "note": "Arkham API unavailable — whale/institutional flow proxy",
    }


def entity_flow_alpha_score(flow_score: float) -> float:
    return max(0.0, min(100.0, flow_score))


async def fetch_entity_intelligence_input(
    symbol: str = "BTC",
    *,
    address: str | None = None,
) -> dict[str, Any]:
    """Normalized entity/flow input for Alpha Engine — not a standalone engine."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    cache_key = f"arkham:{sym}:{address or ''}"
    cached = _cache_get(cache_key)
    if cached:
        out = dict(cached)
        out["cache_hit"] = True
        return out

    api_data = None
    if address and _api_key():
        try:
            addr_seg = safe_url_segment(str(address).strip())
        except ValueError:
            addr_seg = None
        if addr_seg:
            api_data = await _api_get(f"{ARKHAM_HTTPS_ORIGIN}/intelligence/address/{addr_seg}")
    elif _api_key():
        query = _ENTITY_QUERIES.get(sym)
        if query is None:
            try:
                query = safe_url_segment(sym.lower())
            except ValueError:
                query = None
        if query:
            api_data = await _api_get(
                f"{ARKHAM_HTTPS_ORIGIN}/intelligence/search",
                params={"query": query},
            )

    if api_data:
        entities = api_data.get("entities") or api_data.get("results") or []
        labels = []
        if isinstance(api_data.get("arkhamEntity"), dict):
            labels.append(api_data["arkhamEntity"].get("name"))
        for ent in entities[:3]:
            if isinstance(ent, dict):
                labels.append(ent.get("name") or ent.get("id"))
        flow_score = 55.0 if labels else 50.0
        result = {
            "ok": True,
            "surface": "arkham_entity_input",
            "alpha_engine_role": "entity_flow_input",
            "symbol": sym,
            "source": "arkham_api",
            "fallback": False,
            "entity_labels": [l for l in labels if l],
            "entity_flow_score": flow_score,
            "alpha_score": round(flow_score, 2),
            "raw_available": True,
            "api_key_configured": True,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "sla_met": (time.perf_counter() - t0) <= 3.0,
            "timestamp": _utcnow(),
        }
    else:
        fb = await _fallback_entity_input(sym)
        result = {
            "ok": True,
            "surface": "arkham_entity_input",
            "alpha_engine_role": "entity_flow_input",
            "symbol": sym,
            "source": fb.get("source"),
            "fallback": True,
            "entity_labels": [],
            "entity_flow_score": fb.get("entity_flow_score", 50),
            "alpha_score": fb.get("alpha_score", 50),
            "whale_alert_count": fb.get("whale_alert_count", 0),
            "api_key_configured": bool(_api_key()),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "sla_met": (time.perf_counter() - t0) <= 3.0,
            "timestamp": _utcnow(),
        }

    _cache_set(cache_key, result)
    return result


def arkham_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "arkham_connector",
        "role": "alpha_engine_entity_input",
        "api_key_configured": bool(_api_key()),
        "cache_ttl_seconds": _cache_ttl(),
        "fallback_chain": ["arkham_api", "whale_flow_proxy"],
        "timestamp": _utcnow(),
    }
