"""
Binance API connector (#21) — silent Data Ingestion Layer source.

NOT a standalone user feature. Spot/futures market data with:
- Optional BINANCE_API_KEY
- TTL cache (1–24h)
- Rate-limit backoff on HTTP 429
- Fallback: stale cache → CoinGecko
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.canonical.resolver import resolve_asset
from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.BinanceConnector")

SPOT_BASE = "https://api.binance.com"
FUTURES_BASE = "https://fapi.binance.com"
_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=86400)
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_PAIR_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT", "BNB": "BNBUSDT"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("BINANCE_API_KEY") or "").strip()
    return key or None


def _headers() -> dict[str, str]:
    headers = dict(_HEADERS)
    key = _api_key()
    if key:
        headers["X-MBX-APIKEY"] = key
    return headers


def _pair(symbol: str) -> str:
    return _PAIR_MAP.get(symbol.upper(), f"{symbol.upper()}USDT")


async def _binance_get(
    base: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    cache_key_str: str,
    ttl: int,
    source_slug: str,
) -> dict[str, Any]:
    headers = _headers()
    resp = await _CACHE.http_get_json(
        f"{base}{path}",
        params=params,
        headers=headers,
        timeout_sec=3.0,
        cache_key=cache_key_str,
        ttl=ttl,
        source_slug=source_slug,
    )
    if resp.get("ok"):
        return {**resp, "source": "binance"}
    return resp


async def fetch_binance_spot_ticker(symbol: str = "BTC") -> dict[str, Any]:
    """Normalized spot 24h ticker."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    pair = _pair(sym)
    ttl = _CACHE.ttl("BINANCE_CACHE_TTL_SEC", 300)
    resp = await _binance_get(
        SPOT_BASE,
        "/api/v3/ticker/24hr",
        params={"symbol": pair},
        cache_key_str=cache_key("binance_spot", pair),
        ttl=ttl,
        source_slug="binance_spot",
    )
    if not resp.get("ok"):
        return await _spot_fallback(sym, error=resp.get("error"))

    row = resp.get("data") or {}
    price = float(row.get("lastPrice") or 0)
    if price <= 0:
        return await _spot_fallback(sym, error="empty_price")

    resolved = resolve_asset(sym)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#21",
        "symbol": sym,
        "canonical_id": resolved.canonical_id,
        "pair": pair,
        "price_usd": price,
        "change_24h_pct": float(row.get("priceChangePercent") or 0),
        "volume_24h": float(row.get("volume") or 0),
        "quote_volume_24h": float(row.get("quoteVolume") or 0),
        "source": "binance",
        "ingestion_role": "market_data",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_binance_futures_funding(symbol: str = "BTC") -> dict[str, Any]:
    """Futures premium index + funding rate."""
    sym = symbol.upper()
    pair = _pair(sym)
    ttl = _CACHE.ttl("BINANCE_CACHE_TTL_SEC", 300)
    resp = await _binance_get(
        FUTURES_BASE,
        "/fapi/v1/premiumIndex",
        params={"symbol": pair},
        cache_key_str=cache_key("binance_futures", pair),
        ttl=ttl,
        source_slug="binance_futures",
    )
    if not resp.get("ok"):
        return {"ok": False, "symbol": sym, "error": resp.get("error"), "data_state": "MISSING"}

    row = resp.get("data") or {}
    return {
        "ok": True,
        "feature": "#21",
        "symbol": sym,
        "pair": pair,
        "mark_price": float(row.get("markPrice") or 0),
        "index_price": float(row.get("indexPrice") or 0),
        "funding_rate": float(row.get("lastFundingRate") or 0),
        "source": "binance_futures",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "timestamp": _utcnow(),
    }


async def _spot_fallback(symbol: str, *, error: str | None = None) -> dict[str, Any]:
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_price

    row = await fetch_coingecko_price(symbol)
    if row.get("ok"):
        row.update({"fallback": True, "binance_error": error, "source": "coingecko_fallback"})
        return row
    return {"ok": False, "symbol": symbol, "error": error or "binance_unavailable", "data_state": "MISSING"}


def binance_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "binance_ingestion_connector",
        "role": "market_data_source",
        "feature": "#21",
        "spot_base": SPOT_BASE,
        "futures_base": FUTURES_BASE,
        "cache_ttl_seconds": _CACHE.ttl("BINANCE_CACHE_TTL_SEC", 300),
        "api_key_configured": bool(_api_key()),
        "rate_limited": _CACHE.rate_limited(),
        "circuit_breakers": {
            "binance_spot": is_open("binance_spot"),
            "binance_futures": is_open("binance_futures"),
        },
        "fallback_chain": ["binance_api", "stale_cache", "coingecko"],
        "timestamp": _utcnow(),
    }
