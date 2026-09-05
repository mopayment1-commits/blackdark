"""
Gate.io API connector (#60) — silent Data Ingestion Layer.

NOT a branded surface. Detects Gate-only listings vs Binance for early altcoin signals.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from blackdark.ingestion.exchange_listing_tracker import record_sightings

logger = logging.getLogger("BLACKDARK.GateIOConnector")

BASE_URL = "https://api.gateio.ws/api/v4"
_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=86400)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _usdt_pairs(rows: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        pair = str(row.get("currency_pair") or row.get("symbol") or "")
        if pair.endswith("_USDT"):
            out.add(pair.split("_")[0].upper())
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


async def fetch_gateio_listing_intelligence(*, min_volume_usd: float = 50_000) -> dict[str, Any]:
    """Gate.io spot tickers + early listing detection vs Binance (#60)."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("GATEIO_CACHE_TTL_SEC", 300)
    resp = await _CACHE.http_get_json(
        f"{BASE_URL}/spot/tickers",
        timeout_sec=3.0,
        cache_key=cache_key("gateio_tickers"),
        ttl=ttl,
        source_slug="gateio",
    )
    if not resp.get("ok"):
        stale = _CACHE.get_stale(cache_key("gateio_tickers"))
        if stale:
            rows = stale.get("data") if isinstance(stale.get("data"), list) else []
            return {
                "ok": True,
                "feature": "#60",
                "stale_fallback": True,
                "tickers": rows[:10] if isinstance(rows, list) else [],
                "data_state": "DEGRADED",
            }
        return {"ok": False, "feature": "#60", "error": resp.get("error"), "data_state": "MISSING"}

    rows = resp.get("data") or []
    if not isinstance(rows, list):
        rows = []

    gate_symbols = _usdt_pairs(rows)
    record_sightings("gateio", gate_symbols)
    binance_symbols = await _fetch_binance_usdt_symbols()
    if binance_symbols:
        record_sightings("binance", binance_symbols)

    gate_only = sorted(gate_symbols - binance_symbols) if binance_symbols else []
    liquid_gate_only: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        pair = str(row.get("currency_pair") or "")
        asset = pair.split("_")[0].upper() if "_" in pair else ""
        if asset not in gate_only:
            continue
        vol = float(row.get("quote_volume") or 0)
        if vol < min_volume_usd:
            continue
        liquid_gate_only.append(
            {
                "symbol": asset,
                "pair": pair,
                "price": float(row.get("last") or 0),
                "change_24h_pct": float(row.get("change_percentage") or 0),
                "volume_usd": round(vol, 2),
            }
        )
    liquid_gate_only.sort(key=lambda x: x.get("volume_usd") or 0, reverse=True)

    headline = None
    if liquid_gate_only:
        top = liquid_gate_only[0]["symbol"]
        headline = f"First platform to surface {top} before Binance listing — early altcoin signal"
    elif gate_only:
        headline = f"Gate-only altcoin candidates detected ({len(gate_only)}) — not yet on Binance"

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#60",
        "ingestion_role": "exchange_listing_intelligence",
        "exchange": "gateio",
        "gate_only_count": len(gate_only),
        "gate_only_liquid": liquid_gate_only[:15],
        "headline": headline,
        "ai_context_line": headline,
        "cache_hit": resp.get("cache_hit"),
        "data_state": "LIVE" if binance_symbols else "DEGRADED",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_gateio_spot_ticker(symbol: str = "BTC") -> dict[str, Any]:
    """Normalized spot ticker for a single asset."""
    sym = symbol.upper()
    pair = f"{sym}_USDT"
    ttl = _CACHE.ttl("GATEIO_CACHE_TTL_SEC", 300)
    resp = await _CACHE.http_get_json(
        f"{BASE_URL}/spot/tickers",
        params={"currency_pair": pair},
        timeout_sec=3.0,
        cache_key=cache_key("gateio_ticker", pair),
        ttl=ttl,
        source_slug="gateio",
    )
    if not resp.get("ok"):
        return {"ok": False, "symbol": sym, "error": resp.get("error")}
    rows = resp.get("data") or []
    row = rows[0] if isinstance(rows, list) and rows else (resp.get("data") if isinstance(resp.get("data"), dict) else {})
    return {
        "ok": True,
        "feature": "#60",
        "symbol": sym,
        "pair": pair,
        "price_usd": float(row.get("last") or 0),
        "change_24h_pct": float(row.get("change_percentage") or 0),
        "volume_usd": float(row.get("quote_volume") or 0),
        "source": "gateio",
        "cache_hit": resp.get("cache_hit"),
        "timestamp": _utcnow(),
    }


def gateio_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "gateio_ingestion_connector",
        "role": "exchange_listing_input",
        "feature": "#60",
        "cache_ttl_seconds": _CACHE.ttl("GATEIO_CACHE_TTL_SEC", 300),
        "circuit_open": is_open("gateio"),
        "fallback_chain": ["gateio_api", "stale_cache", "binance_exchange_info"],
        "timestamp": _utcnow(),
    }
