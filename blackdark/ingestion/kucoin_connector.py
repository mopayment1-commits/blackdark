"""
KuCoin API connector (#69) — silent Data Ingestion Layer.

NOT a branded surface. Detects KuCoin listings before Binance with honest lead-time tracking.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from blackdark.ingestion.exchange_listing_tracker import lead_time_hours, record_sightings

logger = logging.getLogger("BLACKDARK.KuCoinConnector")

BASE_URL = "https://api.kucoin.com/api/v1"
_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=86400)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _usdt_symbols(tickers: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for row in tickers:
        sym = str(row.get("symbol") or "")
        if sym.endswith("-USDT"):
            base = sym.replace("-USDT", "").replace("XBT", "BTC")
            out.add(base.upper())
    return out


async def _fetch_binance_usdt_symbols() -> set[str]:
    resp = await _CACHE.http_get_json(
        "https://api.binance.com/api/v3/exchangeInfo",
        timeout_sec=3.0,
        cache_key=cache_key("binance_exchange_info"),
        ttl=_CACHE.ttl("BINANCE_CACHE_TTL_SEC", 3600),
        source_slug="binance_spot",
    )
    if not resp.get("ok"):
        return set()
    symbols = (resp.get("data") or {}).get("symbols") or []
    return {
        str(s.get("baseAsset") or "").upper()
        for s in symbols
        if isinstance(s, dict) and str(s.get("quoteAsset")) == "USDT" and s.get("status") == "TRADING"
    }


async def fetch_kucoin_listing_intelligence(*, min_volume_usd: float = 50_000) -> dict[str, Any]:
    """KuCoin spot tickers + early listing detection vs Binance (#69)."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("KUCOIN_CACHE_TTL_SEC", 300)
    resp = await _CACHE.http_get_json(
        f"{BASE_URL}/market/allTickers",
        timeout_sec=3.0,
        cache_key=cache_key("kucoin_all_tickers"),
        ttl=ttl,
        source_slug="kucoin",
    )
    if not resp.get("ok"):
        stale = _CACHE.get_stale(cache_key("kucoin_all_tickers"))
        if stale:
            return {"ok": True, "feature": "#69", "stale_fallback": True, "data_state": "DEGRADED"}
        return {"ok": False, "feature": "#69", "error": resp.get("error"), "data_state": "MISSING"}

    payload = resp.get("data") or {}
    tickers = (payload.get("data") or {}).get("ticker") or []
    if not isinstance(tickers, list):
        tickers = []

    kucoin_symbols = _usdt_symbols(tickers)
    record_sightings("kucoin", kucoin_symbols)
    binance_symbols = await _fetch_binance_usdt_symbols()
    if binance_symbols:
        record_sightings("binance", binance_symbols)

    kucoin_only = sorted(kucoin_symbols - binance_symbols) if binance_symbols else []
    candidates: list[dict[str, Any]] = []
    for row in tickers:
        if not isinstance(row, dict):
            continue
        sym = str(row.get("symbol") or "")
        if not sym.endswith("-USDT"):
            continue
        asset = sym.replace("-USDT", "").replace("XBT", "BTC").upper()
        if asset not in kucoin_only:
            continue
        vol = float(row.get("volValue") or 0)
        if vol < min_volume_usd:
            continue
        lead_h = lead_time_hours(source_exchange="kucoin", symbol=asset, target_exchange="binance")
        candidates.append(
            {
                "symbol": asset,
                "pair": sym,
                "price": float(row.get("last") or 0),
                "change_24h_pct": float(row.get("changeRate") or 0) * 100,
                "volume_usd": round(vol, 2),
                "lead_time_hours": lead_h,
            }
        )
    candidates.sort(key=lambda x: x.get("volume_usd") or 0, reverse=True)

    headline = None
    if candidates:
        top = candidates[0]
        lead = top.get("lead_time_hours")
        if lead and lead >= 1:
            headline = f"KuCoin-listed token {top['symbol']} detected {int(lead)} hours before Binance listing"
        else:
            headline = f"KuCoin-listed token {top['symbol']} detected — not yet on Binance"

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#69",
        "ingestion_role": "exchange_listing_intelligence",
        "exchange": "kucoin",
        "kucoin_only_count": len(kucoin_only),
        "early_listing_candidates": candidates[:15],
        "headline": headline,
        "ai_context_line": headline,
        "cache_hit": resp.get("cache_hit"),
        "data_state": "LIVE" if binance_symbols else "DEGRADED",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_kucoin_spot_ticker(symbol: str = "BTC") -> dict[str, Any]:
    sym = symbol.upper().replace("BTC", "XBT") if symbol.upper() == "BTC" else symbol.upper()
    pair = f"{sym}-USDT"
    ttl = _CACHE.ttl("KUCOIN_CACHE_TTL_SEC", 300)
    resp = await _CACHE.http_get_json(
        f"{BASE_URL}/market/allTickers",
        timeout_sec=3.0,
        cache_key=cache_key("kucoin_ticker", pair),
        ttl=ttl,
        source_slug="kucoin",
    )
    if not resp.get("ok"):
        return {"ok": False, "symbol": symbol.upper(), "error": resp.get("error")}
    tickers = ((resp.get("data") or {}).get("data") or {}).get("ticker") or []
    row = next((t for t in tickers if isinstance(t, dict) and t.get("symbol") == pair), {})
    return {
        "ok": bool(row),
        "feature": "#69",
        "symbol": symbol.upper(),
        "pair": pair,
        "price_usd": float(row.get("last") or 0),
        "change_24h_pct": float(row.get("changeRate") or 0) * 100,
        "volume_usd": float(row.get("volValue") or 0),
        "source": "kucoin",
        "cache_hit": resp.get("cache_hit"),
        "timestamp": _utcnow(),
    }


def kucoin_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "kucoin_ingestion_connector",
        "role": "exchange_listing_input",
        "feature": "#69",
        "cache_ttl_seconds": _CACHE.ttl("KUCOIN_CACHE_TTL_SEC", 300),
        "circuit_open": is_open("kucoin"),
        "fallback_chain": ["kucoin_api", "stale_cache"],
        "timestamp": _utcnow(),
    }
