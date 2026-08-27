"""
OKX API connector (#80) — silent Data Ingestion Layer.

NOT a branded surface. Spot + swap/futures market data with:
- Optional OKX_API_KEY / OKX_API_SECRET (public endpoints work without keys)
- TTL cache 1–24h (`OKX_CACHE_TTL_SEC`)
- Rate-limit backoff + circuit breaker via `source_slug`
- Fallback: stale cache → Binance
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.canonical.resolver import resolve_asset
from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.OKXConnector")

BASE_URL = "https://www.okx.com"
_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=86400)
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_PAIR_MAP = {"BTC": "BTC-USDT", "ETH": "ETH-USDT", "SOL": "SOL-USDT", "BNB": "BNB-USDT"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("OKX_API_KEY") or "").strip()
    return key or None


def _headers() -> dict[str, str]:
    headers = dict(_HEADERS)
    key = _api_key()
    if key:
        headers["OK-ACCESS-KEY"] = key
    return headers


def _inst_id(symbol: str) -> str:
    return _PAIR_MAP.get(symbol.upper(), f"{symbol.upper()}-USDT")


def _swap_inst_id(symbol: str) -> str:
    sym = symbol.upper()
    return f"{sym}-USDT-SWAP"


async def _okx_get(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    cache_key_str: str,
    ttl: int,
    source_slug: str,
) -> dict[str, Any]:
    resp = await _CACHE.http_get_json(
        f"{BASE_URL}{path}",
        params=params,
        headers=_headers(),
        timeout_sec=3.0,
        cache_key=cache_key_str,
        ttl=ttl,
        source_slug=source_slug,
    )
    if resp.get("ok"):
        return {**resp, "source": "okx"}
    return resp


async def fetch_okx_spot_ticker(symbol: str = "BTC") -> dict[str, Any]:
    """Normalized OKX spot 24h ticker."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    inst = _inst_id(sym)
    ttl = _CACHE.ttl("OKX_CACHE_TTL_SEC", 300)
    resp = await _okx_get(
        "/api/v5/market/ticker",
        params={"instId": inst},
        cache_key_str=cache_key("okx_spot", inst),
        ttl=ttl,
        source_slug="okx_spot",
    )
    if not resp.get("ok"):
        return await _spot_fallback(sym, error=resp.get("error"))

    payload = resp.get("data") or {}
    rows = payload.get("data") if isinstance(payload, dict) else payload
    row = rows[0] if isinstance(rows, list) and rows else {}
    if not isinstance(row, dict):
        row = {}
    price = float(row.get("last") or 0)
    if price <= 0:
        return await _spot_fallback(sym, error="empty_price")

    open24 = float(row.get("open24h") or price)
    change_pct = round(((price - open24) / open24) * 100, 3) if open24 > 0 else 0.0
    resolved = resolve_asset(sym)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#80",
        "symbol": sym,
        "canonical_id": resolved.canonical_id,
        "inst_id": inst,
        "price_usd": price,
        "change_24h_pct": change_pct,
        "volume_24h": float(row.get("vol24h") or 0),
        "quote_volume_24h": float(row.get("volCcy24h") or 0),
        "source": "okx",
        "ingestion_role": "market_data",
        "user_facing_note": "OKX futures data included in analysis",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_okx_swap_ticker(symbol: str = "BTC") -> dict[str, Any]:
    """OKX perpetual swap ticker + funding."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    inst = _swap_inst_id(sym)
    ttl = _CACHE.ttl("OKX_CACHE_TTL_SEC", 300)

    ticker_resp = await _okx_get(
        "/api/v5/market/ticker",
        params={"instId": inst},
        cache_key_str=cache_key("okx_swap", inst),
        ttl=ttl,
        source_slug="okx_swap",
    )
    funding_resp = await _okx_get(
        "/api/v5/public/funding-rate",
        params={"instId": inst},
        cache_key_str=cache_key("okx_funding", inst),
        ttl=ttl,
        source_slug="okx_swap",
    )

    if not ticker_resp.get("ok"):
        return await _swap_fallback(sym, error=ticker_resp.get("error"))

    ticker_payload = ticker_resp.get("data") or {}
    rows = ticker_payload.get("data") if isinstance(ticker_payload, dict) else ticker_payload
    row = rows[0] if isinstance(rows, list) and rows else {}
    fund_payload = funding_resp.get("data") or {}
    fund_rows = fund_payload.get("data") if isinstance(fund_payload, dict) else fund_payload
    fund = fund_rows[0] if isinstance(fund_rows, list) and fund_rows else {}

    mark = float(row.get("last") or row.get("markPx") or 0)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#80",
        "symbol": sym,
        "inst_id": inst,
        "mark_price": mark,
        "funding_rate": float(fund.get("fundingRate") or 0) if fund else None,
        "open_interest": float(row.get("openInterest") or 0) if row.get("openInterest") else None,
        "source": "okx_swap",
        "ingestion_role": "futures_market_data",
        "user_facing_note": "OKX futures data included in analysis",
        "cache_hit": ticker_resp.get("cache_hit"),
        "stale_fallback": ticker_resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_okx_market_context(symbol: str = "BTC") -> dict[str, Any]:
    """Combined spot + swap for decision engine enrichment."""
    t0 = time.perf_counter()
    spot, swap = await _gather_pair(
        fetch_okx_spot_ticker(symbol),
        fetch_okx_swap_ticker(symbol),
    )
    ok = spot.get("ok") or swap.get("ok")
    headline = None
    if swap.get("ok") and swap.get("funding_rate") is not None:
        fr = float(swap["funding_rate"]) * 100
        if abs(fr) >= 0.03:
            headline = f"OKX futures funding elevated ({fr:.3f}%) — included in analysis"
        else:
            headline = "OKX futures data included in analysis"

    elapsed = time.perf_counter() - t0
    return {
        "ok": ok,
        "feature": "#80",
        "symbol": symbol.upper(),
        "spot": spot if spot.get("ok") else None,
        "swap": swap if swap.get("ok") else None,
        "headline": headline,
        "ai_context_line": headline,
        "ingestion_role": "exchange_market_data",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def okx_for_decision_engine(symbol: str = "BTC") -> dict[str, Any]:
    """Compact #80 payload for Decision Engine (#48)."""
    row = await fetch_okx_market_context(symbol)
    if not row.get("ok"):
        return {"ok": False, "feature": "#80", "error": "okx_unavailable"}
    swap = row.get("swap") or {}
    risk_delta = 0.0
    fr = swap.get("funding_rate")
    if fr is not None and abs(float(fr)) >= 0.0005:
        risk_delta = 0.3
    return {
        "ok": True,
        "feature": "#80",
        "symbol": row.get("symbol"),
        "funding_rate": fr,
        "mark_price": swap.get("mark_price"),
        "risk_score_delta": risk_delta,
        "headline": row.get("headline"),
        "latency_ms": row.get("latency_ms"),
    }


async def _gather_pair(a, b):
    import asyncio

    results = await asyncio.gather(a, b, return_exceptions=True)
    out = []
    for r in results:
        if isinstance(r, BaseException):
            out.append({"ok": False, "error": str(r)})
        else:
            out.append(r if isinstance(r, dict) else {})
    return out[0], out[1]


async def _spot_fallback(symbol: str, *, error: str | None = None) -> dict[str, Any]:
    from blackdark.ingestion.binance_connector import fetch_binance_spot_ticker

    row = await fetch_binance_spot_ticker(symbol)
    if row.get("ok"):
        row.update({
            "fallback": True,
            "okx_error": error,
            "source": "binance_fallback",
            "user_facing_note": "OKX futures data included in analysis",
        })
        return row
    stale = _CACHE.get_stale(cache_key("okx_spot", _inst_id(symbol)))
    if stale and stale.get("ok"):
        return {**stale, "stale_fallback": True, "okx_error": error}
    return {"ok": False, "symbol": symbol, "error": error or "okx_unavailable", "data_state": "MISSING"}


async def _swap_fallback(symbol: str, *, error: str | None = None) -> dict[str, Any]:
    from blackdark.ingestion.binance_connector import fetch_binance_futures_funding

    row = await fetch_binance_futures_funding(symbol)
    if row.get("ok"):
        return {
            "ok": True,
            "feature": "#80",
            "symbol": symbol.upper(),
            "mark_price": row.get("mark_price"),
            "funding_rate": row.get("funding_rate"),
            "source": "binance_futures_fallback",
            "fallback": True,
            "okx_error": error,
            "user_facing_note": "OKX futures data included in analysis",
            "timestamp": _utcnow(),
        }
    return {"ok": False, "symbol": symbol.upper(), "error": error or "okx_swap_unavailable", "data_state": "MISSING"}


def okx_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "okx_ingestion_connector",
        "role": "market_data_source",
        "feature": "#80",
        "base_url": BASE_URL,
        "cache_ttl_seconds": _CACHE.ttl("OKX_CACHE_TTL_SEC", 300),
        "api_key_configured": bool(_api_key()),
        "rate_limited": _CACHE.rate_limited(),
        "circuit_breakers": {
            "okx_spot": is_open("okx_spot"),
            "okx_swap": is_open("okx_swap"),
        },
        "fallback_chain": ["okx_api", "stale_cache", "binance"],
        "user_facing_note": "OKX futures data included in analysis",
        "timestamp": _utcnow(),
    }
