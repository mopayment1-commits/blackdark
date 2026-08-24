"""
CoinGecko API connector — primary Data Ingestion Layer source (#34).

NOT a standalone user feature. Foundation connector with:
- Auth via COINGECKO_API_KEY (demo/pro)
- TTL cache (default 1h, max 24h)
- Rate-limit backoff on HTTP 429
- Canonical normalization via blackdark.canonical
- Fallback: stale cache → Kraken public ticker
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

from blackdark.canonical.resolver import resolve_asset
from blackdark.canonical.vendor_maps import COINGECKO_IDS
from data_lake import store_snapshot
from database import upsert_ingestion_health

logger = logging.getLogger("BLACKDARK.CoinGeckoConnector")

BASE_URL = "https://api.coingecko.com/api/v3"
_CACHE: dict[str, tuple[float, Any]] = {}
_RATE_LIMIT_UNTIL = 0.0
_DEFAULT_TTL = int(os.getenv("COINGECKO_CACHE_TTL_SEC", "3600"))
_MAX_TTL = 86400
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cache_ttl() -> int:
    raw = int(os.getenv("COINGECKO_CACHE_TTL_SEC", str(_DEFAULT_TTL)))
    return max(60, min(_MAX_TTL, raw))


def _api_headers() -> dict[str, str]:
    headers = dict(_HEADERS)
    key = (os.getenv("COINGECKO_API_KEY") or "").strip()
    if key:
        headers["x-cg-demo-api-key"] = key
    return headers


def coingecko_id_for(symbol: str) -> str | None:
    """Resolve platform symbol → CoinGecko coin id via canonical metadata."""
    resolved = resolve_asset(symbol)
    if resolved.asset:
        cg = resolved.asset.external_ids.get("coingecko_id")
        if cg:
            return cg
    return COINGECKO_IDS.get(symbol.upper())


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    if time.time() - row[0] < _cache_ttl():
        return row[1]
    return None


def _cache_get_stale(key: str) -> Any | None:
    row = _CACHE.get(key)
    return row[1] if row else None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


async def _kraken_fallback_price(symbol: str) -> dict[str, Any] | None:
    """Tertiary fallback when CoinGecko is unavailable."""
    pair_map = {"BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD"}
    pair = pair_map.get(symbol.upper())
    if not pair:
        return None
    url = "https://api.kraken.com/0/public/Ticker"
    timeout = aiohttp.ClientTimeout(total=4)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.get(url, params={"pair": pair}) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        result = (data.get("result") or {}).values()
        row = next(iter(result), None)
        if not row:
            return None
        last = float((row.get("c") or [0])[0])
        if last <= 0:
            return None
        return {
            "price_usd": last,
            "change_24h_pct": 0.0,
            "source": "kraken_fallback",
            "fallback": True,
        }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        return None


async def _request(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    cache_key: str | None = None,
) -> dict[str, Any]:
    global _RATE_LIMIT_UNTIL
    key = cache_key or f"{path}?{json.dumps(params or {}, sort_keys=True)}"
    cached = _cache_get(key)
    if cached is not None:
        out = dict(cached) if isinstance(cached, dict) else {"data": cached}
        out["cache_hit"] = True
        return out

    if time.time() < _RATE_LIMIT_UNTIL:
        stale = _cache_get_stale(key)
        if stale is not None:
            out = dict(stale) if isinstance(stale, dict) else {"data": stale}
            out["cache_hit"] = True
            out["stale_fallback"] = True
            out["rate_limited"] = True
            return out
        return {"ok": False, "error": "rate_limited", "data": None}

    url = f"{BASE_URL}/{path.lstrip('/')}"
    timeout = aiohttp.ClientTimeout(total=8)
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_api_headers()) as session:
            async with session.get(url, params=params) as resp:
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                if resp.status == 429:
                    _RATE_LIMIT_UNTIL = time.time() + 60
                    stale = _cache_get_stale(key)
                    if stale is not None:
                        out = dict(stale) if isinstance(stale, dict) else {"data": stale}
                        out.update(
                            {
                                "ok": True,
                                "cache_hit": True,
                                "stale_fallback": True,
                                "rate_limited": True,
                                "latency_ms": latency_ms,
                            }
                        )
                        return out
                    return {"ok": False, "error": "rate_limited", "latency_ms": latency_ms}
                if resp.status != 200:
                    stale = _cache_get_stale(key)
                    if stale is not None:
                        out = dict(stale) if isinstance(stale, dict) else {"data": stale}
                        out.update({"ok": True, "stale_fallback": True, "http_status": resp.status})
                        return out
                    return {"ok": False, "error": f"http_{resp.status}", "latency_ms": latency_ms}
                data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError) as exc:
        stale = _cache_get_stale(key)
        if stale is not None:
            out = dict(stale) if isinstance(stale, dict) else {"data": stale}
            out.update({"ok": True, "stale_fallback": True, "error": str(exc)})
            return out
        return {"ok": False, "error": str(exc)}

    result = {
        "ok": True,
        "data": data,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "timestamp": _utcnow(),
        "cache_hit": False,
    }
    _cache_set(key, result)
    return result


def _normalize_price_row(symbol: str, price_usd: float, change_pct: float, *, source: str) -> dict[str, Any]:
    resolved = resolve_asset(symbol)
    return {
        "symbol": resolved.symbol or symbol.upper(),
        "canonical_id": resolved.canonical_id,
        "coingecko_id": coingecko_id_for(symbol),
        "price_usd": price_usd,
        "change_24h_pct": change_pct,
        "source": source,
        "resolve_found": resolved.found,
    }


async def fetch_coingecko_price(symbol: str = "BTC") -> dict[str, Any]:
    """Normalized single-asset price — primary ingestion entrypoint."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    cg_id = coingecko_id_for(sym)
    if not cg_id:
        fb = await _kraken_fallback_price(sym)
        if fb:
            row = _normalize_price_row(sym, fb["price_usd"], fb.get("change_24h_pct", 0), source="kraken_fallback")
            row.update({"ok": True, "fallback": True, "latency_ms": round((time.perf_counter() - t0) * 1000, 1)})
            return row
        return {"ok": False, "symbol": sym, "error": "unsupported_symbol"}

    resp = await _request(
        "simple/price",
        params={
            "ids": cg_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        cache_key=f"price:{cg_id}",
    )
    if not resp.get("ok"):
        fb = await _kraken_fallback_price(sym)
        if fb:
            row = _normalize_price_row(sym, fb["price_usd"], 0, source="kraken_fallback")
            row.update({"ok": True, "fallback": True, "coingecko_error": resp.get("error")})
            return row
        return {"ok": False, "symbol": sym, "error": resp.get("error")}

    data = resp.get("data") or {}
    row = data.get(cg_id) or {}
    price = float(row.get("usd") or 0)
    if price <= 0:
        return {"ok": False, "symbol": sym, "error": "empty_price"}

    out = _normalize_price_row(
        sym,
        price,
        float(row.get("usd_24h_change") or 0),
        source="coingecko",
    )
    out.update(
        {
            "ok": True,
            "cache_hit": resp.get("cache_hit"),
            "stale_fallback": resp.get("stale_fallback"),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "sla_met": (time.perf_counter() - t0) <= 3.0,
        }
    )
    return out


async def fetch_coingecko_markets(*, per_page: int = 100) -> dict[str, Any]:
    """Top markets normalized with canonical IDs."""
    resp = await _request(
        "coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
        },
        cache_key=f"markets:{per_page}",
    )
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error"), "markets": []}

    markets: list[dict[str, Any]] = []
    for row in resp.get("data") or []:
        if not isinstance(row, dict):
            continue
        sym = str(row.get("symbol") or "").upper()
        resolved = resolve_asset(sym)
        markets.append(
            {
                "canonical_id": resolved.canonical_id,
                "symbol": resolved.symbol or sym,
                "coingecko_id": row.get("id"),
                "name": row.get("name"),
                "price_usd": row.get("current_price"),
                "market_cap_usd": row.get("market_cap"),
                "volume_24h_usd": row.get("total_volume"),
                "change_24h_pct": row.get("price_change_percentage_24h"),
            }
        )
    return {
        "ok": True,
        "count": len(markets),
        "markets": markets,
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": resp.get("latency_ms"),
        "sla_met": (resp.get("latency_ms") or 9999) <= 3000,
    }


async def fetch_coingecko_trending() -> dict[str, Any]:
    resp = await _request("search/trending", cache_key="trending")
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error"), "coins": []}
    coins = ((resp.get("data") or {}).get("coins") or [])[:15]
    return {"ok": True, "coins": coins, "cache_hit": resp.get("cache_hit")}


async def fetch_coingecko_global() -> dict[str, Any]:
    resp = await _request("global", cache_key="global")
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error")}
    return {"ok": True, "global": (resp.get("data") or {}).get("data"), "cache_hit": resp.get("cache_hit")}


async def run_coingecko_primary_ingest() -> dict[str, Any]:
    """
    Priority #1 ingestion pass — CoinGecko markets + prices into data lake.
    Called before other price sources in bootstrap.
    """
    t0 = time.perf_counter()
    markets = await fetch_coingecko_markets(per_page=100)
    trending = await fetch_coingecko_trending()
    global_data = await fetch_coingecko_global()

    payload = {
        "primary_source": "coingecko",
        "markets": markets.get("markets") or [],
        "trending": trending.get("coins") or [],
        "global": global_data.get("global"),
        "ingested_at": _utcnow(),
        "market_count": markets.get("count", 0),
        "fallback_used": markets.get("stale_fallback") or False,
    }
    ok = bool(markets.get("ok"))
    try:
        await store_snapshot("coingecko_primary", "prices", payload, status="ok" if ok else "degraded")
        await upsert_ingestion_health(
            "coingecko_primary",
            "prices",
            ok=ok,
            error=None if ok else str(markets.get("error") or "ingest_failed"),
        )
    except Exception as exc:
        logger.exception("CoinGecko primary lake write failed")
        return {"ok": False, "error": str(exc)}

    # Also persist per-top-asset price rows for fast oracle reads
    top_symbols = [m["symbol"] for m in (markets.get("markets") or [])[:10] if m.get("symbol")]
    price_rows = []
    for sym in top_symbols:
        row = await fetch_coingecko_price(sym)
        if row.get("ok"):
            price_rows.append(row)
    if price_rows:
        await store_snapshot(
            "coingecko_prices",
            "prices",
            {"prices": price_rows, "source": "coingecko_connector"},
        )

    latency = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": ok,
        "surface": "coingecko_primary_ingest",
        "markets": markets.get("count", 0),
        "prices_cached": len(price_rows),
        "latency_ms": latency,
        "sla_met": latency <= 3000,
        "cache_ttl_seconds": _cache_ttl(),
        "api_key_configured": bool(os.getenv("COINGECKO_API_KEY")),
        "timestamp": _utcnow(),
    }


def coingecko_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "coingecko_ingestion_connector",
        "role": "primary_data_ingestion_source",
        "base_url": BASE_URL,
        "cache_ttl_seconds": _cache_ttl(),
        "cache_entries": len(_CACHE),
        "rate_limited_until": _RATE_LIMIT_UNTIL if _RATE_LIMIT_UNTIL > time.time() else None,
        "api_key_configured": bool(os.getenv("COINGECKO_API_KEY")),
        "fallback_chain": ["coingecko_api", "stale_cache", "kraken_public"],
        "timestamp": _utcnow(),
    }
