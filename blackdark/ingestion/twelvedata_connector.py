"""
Twelve Data API connector (#104) — silent macro enrichment layer.

NOT a standalone product. Enriches Market Radar / Decision Engine (#48) with
crypto-correlated tradfi context (S&P 500, DXY, Gold, Nasdaq, VIX).

Users see natural language like:
"Bitcoin down 3% while DXY up 0.5% — strong negative correlation"
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.TwelveData")

BASE_URL = "https://api.twelvedata.com"
_CACHE = IngestionCache(default_ttl_sec=1200, max_ttl_sec=86400)

# Crypto-correlated tradfi symbols (institutional focus set)
MACRO_SYMBOLS: dict[str, str] = {
    "sp500": "SPX",
    "dxy": "DXY",
    "gold": "XAU/USD",
    "nasdaq": "IXIC",
    "vix": "VIX",
}

_SYMBOL_LABELS: dict[str, str] = {
    "sp500": "S&P 500",
    "dxy": "DXY",
    "gold": "Gold",
    "nasdaq": "Nasdaq",
    "vix": "VIX",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("TWELVEDATA_API_KEY") or "").strip()
    return key or None


def _parse_pct(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_quote_rows(data: Any) -> dict[str, dict[str, Any]]:
    """Twelve Data returns dict for one symbol or list for batch quotes."""
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        if "symbol" in data:
            rows = [data]
        else:
            rows = list(data.values())
    else:
        return {}

    by_symbol: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        sym = str(row.get("symbol") or "").upper()
        if sym:
            by_symbol[sym] = row
    return by_symbol


async def _twelvedata_get(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    cache_key_str: str,
    ttl: int,
) -> dict[str, Any]:
    merged = dict(params or {})
    key = _api_key()
    if key:
        merged["apikey"] = key
    return await _CACHE.http_get_json(
        f"{BASE_URL}{path}",
        params=merged,
        timeout_sec=3.0,
        cache_key=cache_key_str,
        ttl=ttl,
        source_slug="twelvedata",
    )


async def _fetch_btc_change_pct() -> float | None:
    """BTC 24h change for macro correlation narrative."""
    try:
        from blackdark.ingestion.binance_connector import fetch_binance_spot_ticker

        row = await fetch_binance_spot_ticker("BTC")
        if row.get("ok"):
            return _parse_pct(row.get("price_change_pct"))
    except Exception as exc:  # noqa: BLE001 — silent enrichment must not break radar
        logger.debug("btc_change_fallback_failed: %s", exc)
    return None


def _correlation_narrative(
    *,
    btc_change_pct: float | None,
    quotes: dict[str, dict[str, Any]],
) -> str | None:
    """Rule-based macro/crypto correlation line — no ML, honest thresholds."""
    dxy_row = quotes.get("dxy") or {}
    dxy_chg = dxy_row.get("change_pct")
    btc_chg = btc_change_pct

    if btc_chg is None or dxy_chg is None:
        return None

    if btc_chg < -0.5 and dxy_chg > 0.2:
        return (
            f"Bitcoin down {abs(btc_chg):.1f}% while DXY up {dxy_chg:.1f}% "
            "— strong negative correlation"
        )
    if btc_chg > 0.5 and dxy_chg < -0.2:
        return (
            f"Bitcoin up {btc_chg:.1f}% while DXY down {abs(dxy_chg):.1f}% "
            "— risk-on correlation"
        )

    vix_chg = (quotes.get("vix") or {}).get("change_pct")
    if vix_chg is not None and vix_chg > 3.0 and btc_chg < -1.0:
        return (
            f"VIX up {vix_chg:.1f}% with Bitcoin down {abs(btc_chg):.1f}% "
            "— risk-off macro stress"
        )

    sp_chg = (quotes.get("sp500") or {}).get("change_pct")
    if sp_chg is not None and btc_chg is not None:
        same_dir = (sp_chg >= 0 and btc_chg >= 0) or (sp_chg < 0 and btc_chg < 0)
        if same_dir and abs(sp_chg) > 0.5 and abs(btc_chg) > 0.5:
            label = "positive" if sp_chg >= 0 else "negative"
            return (
                f"S&P 500 and Bitcoin moving together ({label}) "
                f"— {abs(btc_chg):.1f}% BTC vs {abs(sp_chg):.1f}% equities"
            )
    return None


async def _fallback_macro_context() -> dict[str, Any]:
    """Fallback chain: Polygon.io SPY → Investing.com RSS."""
    from blackdark.ingestion.polygon_io_connector import fetch_polygon_macro_context

    polygon = await fetch_polygon_macro_context()
    if polygon.get("ok") and polygon.get("change_pct") is not None:
        chg = float(polygon["change_pct"])
        direction = "down" if chg < 0 else "up"
        return {
            "ok": True,
            "source": "polygon_io_fallback",
            "quotes": {
                "sp500": {
                    "label": "S&P 500",
                    "change_pct": round(chg, 3),
                    "proxy": "SPY",
                }
            },
            "headline": polygon.get("headline")
            or f"AI detected S&P 500 {direction} {abs(chg):.1f}% — macro context (fallback)",
            "fallback": True,
        }

    from blackdark.ingestion.investing_com_connector import fetch_investing_news_context

    news = await fetch_investing_news_context(limit=30)
    if news.get("ok"):
        return {
            "ok": True,
            "source": "investing_com_fallback",
            "headline": news.get("ai_context_line"),
            "high_impact_tags": [
                t
                for a in (news.get("articles") or [])
                if a.get("high_impact")
                for t in (a.get("impact_tags") or [])
            ][:8],
            "fallback": True,
        }
    return {"ok": False, "error": "macro_fallback_unavailable"}


async def fetch_twelvedata_macro_context(*, include_btc_correlation: bool = True) -> dict[str, Any]:
    """
    Macro enrichment for Market Radar — tradfi quotes + BTC correlation narrative.

    Cache default 20 minutes (TWELVEDATA_CACHE_TTL_SEC, range 900–1800 recommended).
    """
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("TWELVEDATA_CACHE_TTL_SEC", 1200)
    ck = cache_key("twelvedata_macro", sorted(MACRO_SYMBOLS.values()))
    cached = _CACHE.get(ck, ttl=ttl)
    if cached:
        return {**cached, "cache_hit": True}

    if not _api_key():
        fb = await _fallback_macro_context()
        elapsed = time.perf_counter() - t0
        return {
            "ok": fb.get("ok", False),
            "feature": "#104",
            "ingestion_role": "macro_enrichment",
            "data_state": "DEGRADED",
            "fallback": fb,
            "headline": fb.get("headline"),
            "quotes": fb.get("quotes") or {},
            "latency_ms": round(elapsed * 1000, 1),
            "sla_met": elapsed <= 3.0,
            "timestamp": _utcnow(),
        }

    symbols_csv = ",".join(MACRO_SYMBOLS.values())
    resp = await _twelvedata_get(
        "/quote",
        params={"symbol": symbols_csv},
        cache_key_str=cache_key("twelvedata_quote", symbols_csv),
        ttl=ttl,
    )

    if not resp.get("ok"):
        fb = await _fallback_macro_context()
        stale = _CACHE.get_stale(ck)
        if stale:
            return {**stale, "ok": True, "stale_fallback": True, "fallback": fb}
        elapsed = time.perf_counter() - t0
        return {
            "ok": False,
            "feature": "#104",
            "error": resp.get("error"),
            "fallback": fb if fb.get("ok") else None,
            "data_state": "MISSING",
            "latency_ms": round(elapsed * 1000, 1),
            "timestamp": _utcnow(),
        }

    payload = resp.get("data") or {}
    if isinstance(payload, dict) and payload.get("status") == "error":
        fb = await _fallback_macro_context()
        stale = _CACHE.get_stale(ck)
        if stale:
            return {**stale, "ok": True, "stale_fallback": True, "fallback": fb}
        elapsed = time.perf_counter() - t0
        return {
            "ok": False,
            "feature": "#104",
            "error": payload.get("message") or "twelvedata_error",
            "fallback": fb if fb.get("ok") else None,
            "data_state": "MISSING",
            "latency_ms": round(elapsed * 1000, 1),
            "timestamp": _utcnow(),
        }

    by_symbol = _normalize_quote_rows(payload)
    quotes: dict[str, dict[str, Any]] = {}
    for key, td_symbol in MACRO_SYMBOLS.items():
        row = by_symbol.get(td_symbol.upper()) or by_symbol.get(td_symbol) or {}
        chg = _parse_pct(row.get("percent_change"))
        quotes[key] = {
            "symbol": td_symbol,
            "label": _SYMBOL_LABELS.get(key, key),
            "close": row.get("close"),
            "change_pct": round(chg, 3) if chg is not None else None,
        }

    btc_chg = await _fetch_btc_change_pct() if include_btc_correlation else None
    correlation_line = _correlation_narrative(btc_change_pct=btc_chg, quotes=quotes)

    headline = correlation_line
    if not headline:
        sp = quotes.get("sp500", {}).get("change_pct")
        if sp is not None:
            direction = "down" if sp < 0 else "up"
            headline = (
                f"Macro context: S&P 500 {direction} {abs(sp):.1f}% "
                f"| DXY {quotes.get('dxy', {}).get('change_pct')}% "
                f"| VIX {quotes.get('vix', {}).get('change_pct')}%"
            )

    elapsed = time.perf_counter() - t0
    result = {
        "ok": True,
        "feature": "#104",
        "ingestion_role": "macro_enrichment",
        "quotes": quotes,
        "btc_change_pct": round(btc_chg, 3) if btc_chg is not None else None,
        "correlation_narrative": correlation_line,
        "headline": headline,
        "data_state": "LIVE",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
    _CACHE.set(ck, result)
    return result


def twelvedata_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "twelvedata_ingestion_connector",
        "role": "macro_enrichment_layer",
        "feature": "#104",
        "api_key_configured": bool(_api_key()),
        "symbols": list(MACRO_SYMBOLS.values()),
        "cache_ttl_seconds": _CACHE.ttl("TWELVEDATA_CACHE_TTL_SEC", 1200),
        "circuit_open": is_open("twelvedata"),
        "fallback_chain": ["twelvedata", "stale_cache", "polygon_io", "investing_com_rss"],
        "timestamp": _utcnow(),
    }
