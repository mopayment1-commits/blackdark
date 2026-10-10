"""
DexScreener API connector — DEX liquidity/pair ingestion (#49).

NOT a user-facing feature. Silent Data Ingestion Layer for liquidity drain signals.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from path_safety import safe_url_segment

logger = logging.getLogger("BLACKDARK.DexScreenerConnector")

BASE_URL = "https://api.dexscreener.com"
_CACHE = IngestionCache(default_ttl_sec=3600, max_ttl_sec=86400)
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_pair(row: dict[str, Any]) -> dict[str, Any]:
    liq = (row.get("liquidity") or {}) if isinstance(row.get("liquidity"), dict) else {}
    vol = (row.get("volume") or {}) if isinstance(row.get("volume"), dict) else {}
    price = (row.get("priceUsd") or row.get("priceNative") or 0)
    try:
        price_f = float(price)
    except (TypeError, ValueError):
        price_f = 0.0
    try:
        liq_usd = float(liq.get("usd") or 0)
    except (TypeError, ValueError):
        liq_usd = 0.0
    try:
        vol_24h = float(vol.get("h24") or 0)
    except (TypeError, ValueError):
        vol_24h = 0.0
    base = row.get("baseToken") or {}
    quote = row.get("quoteToken") or {}
    return {
        "pair_address": row.get("pairAddress"),
        "chain": row.get("chainId"),
        "dex": row.get("dexId"),
        "base_symbol": str(base.get("symbol") or "").upper(),
        "quote_symbol": str(quote.get("symbol") or "").upper(),
        "price_usd": price_f,
        "liquidity_usd": liq_usd,
        "volume_24h_usd": vol_24h,
        "price_change_24h_pct": float((row.get("priceChange") or {}).get("h24") or 0),
        "url": row.get("url"),
    }


def _liquidity_drain_signal(pairs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Detect thin liquidity / drain risk from normalized pairs."""
    if not pairs:
        return None
    top = max(pairs, key=lambda p: float(p.get("liquidity_usd") or 0))
    liq = float(top.get("liquidity_usd") or 0)
    vol = float(top.get("volume_24h_usd") or 0)
    change = float(top.get("price_change_24h_pct") or 0)
    drain_score = 0
    if liq > 0 and vol > liq * 2:
        drain_score += 35
    if change <= -8:
        drain_score += 30
    if liq < 50_000:
        drain_score += 25
    if drain_score < 40:
        return None
    return {
        "signal": "liquidity_drain_risk",
        "score": min(100, drain_score),
        "pair": f"{top.get('base_symbol')}/{top.get('quote_symbol')}",
        "liquidity_usd": liq,
        "volume_24h_usd": vol,
        "price_change_24h_pct": change,
        "headline": (
            f"Liquidity stress on {top.get('base_symbol')}: "
            f"${liq:,.0f} pool vs ${vol:,.0f} 24h volume"
        ),
    }


async def _geckoterminal_fallback(query: str) -> list[dict[str, Any]]:
    """Fallback when DexScreener unavailable."""
    q = safe_url_segment(query).upper()
    token_map = {
        "BTC": ("eth", "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
        "ETH": ("eth", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
        "SOL": ("solana", "So11111111111111111111111111111111111111112"),
    }
    net, addr = token_map.get(q, ("eth", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"))
    url = f"https://api.geckoterminal.com/api/v2/networks/{net}/tokens/{addr}/pools"
    timeout = aiohttp.ClientTimeout(total=3)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
    except (aiohttp.ClientError, TimeoutError):
        return []

    pairs: list[dict[str, Any]] = []
    for row in (data.get("data") or [])[:10]:
        attrs = (row.get("attributes") or {}) if isinstance(row, dict) else {}
        try:
            liq = float((attrs.get("reserve_in_usd") or 0))
        except (TypeError, ValueError):
            liq = 0.0
        pairs.append(
            {
                "pair_address": (row.get("id") or "").split("_")[-1],
                "chain": net,
                "dex": "geckoterminal_fallback",
                "base_symbol": q,
                "quote_symbol": "USD",
                "price_usd": float(attrs.get("base_token_price_usd") or 0),
                "liquidity_usd": liq,
                "volume_24h_usd": float(attrs.get("volume_usd", {}).get("h24") or 0)
                if isinstance(attrs.get("volume_usd"), dict)
                else 0.0,
                "price_change_24h_pct": 0.0,
                "url": None,
                "fallback": True,
            }
        )
    return pairs


async def fetch_dex_pairs(query: str = "BTC") -> dict[str, Any]:
    """Normalized DEX pair search — primary DexScreener ingestion entrypoint."""
    t0 = time.perf_counter()
    q = safe_url_segment(query)
    ttl = _CACHE.ttl("DEXSCREENER_CACHE_TTL_SEC", 3600)
    key = cache_key("dexscreener_search", q)
    resp = await _CACHE.http_get(
        f"{BASE_URL}/latest/dex/search",
        params={"q": q},
        timeout_sec=3.0,
        cache_key=key,
        ttl=ttl,
    )

    pairs: list[dict[str, Any]] = []
    fallback_used = False
    if resp.get("ok"):
        raw_pairs = (resp.get("data") or {}).get("pairs") or []
        if isinstance(raw_pairs, list):
            pairs = [_normalize_pair(p) for p in raw_pairs[:25] if isinstance(p, dict)]
    else:
        pairs = await _geckoterminal_fallback(q)
        fallback_used = bool(pairs)

    if not pairs and not resp.get("ok"):
        return {
            "ok": False,
            "query": q,
            "error": resp.get("error"),
            "pairs": [],
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }

    signal = _liquidity_drain_signal(pairs)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "query": q,
        "source": "geckoterminal_fallback" if fallback_used else "dexscreener",
        "ingestion_role": "dex_liquidity",
        "pairs": pairs,
        "count": len(pairs),
        "liquidity_signal": signal,
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback") or fallback_used,
        "fallback": fallback_used,
        "rate_limited": resp.get("rate_limited"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


def dexscreener_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "dexscreener_ingestion_connector",
        "role": "dex_liquidity_ingestion",
        "feature": "#49",
        "base_url": BASE_URL,
        "cache_ttl_seconds": _CACHE.ttl("DEXSCREENER_CACHE_TTL_SEC", 3600),
        "rate_limited": _CACHE.rate_limited(),
        "fallback_chain": ["dexscreener_api", "stale_cache", "geckoterminal"],
        "timestamp": _utcnow(),
    }
