"""
Price Aggregation Engine — Features #133 + #127 (Sprint 0 invisible infrastructure).

#133 — Price collection: canonical schema, outlier detection, volume-weighted average,
        source metadata.
#127 — Live price refresh: invisible auto-update via WS/Redis + connector fallback.
        NOT a user-facing "feature" — prices just work.

Integrated with #194 Unified Connector Layer and #118 ETL storage.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.unified_connector_layer import (
    CanonicalPriceQuote,
    ConnectorFetchResult,
    fetch_all_connector_quotes,
)

logger = logging.getLogger("BLACKDARK.PriceAggregation")

_SNAPSHOT_PATH = Path("data/price_aggregation_snapshots.jsonl")
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEC = 2.0
_OUTLIER_THRESHOLD_PCT = 2.5  # >2.5% from median = outlier (likely API error)
_MIN_SOURCES = 1
_FEATURE_IDS = (133, 127, 194, 147)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def detect_outliers(quotes: list[CanonicalPriceQuote]) -> tuple[list[CanonicalPriceQuote], list[dict[str, Any]]]:
    """
    Outlier detection — isolated extreme price likely API error.
    Returns (clean_quotes, outlier_records).
    """
    if len(quotes) < 2:
        return quotes, []

    prices = [q.price_usd for q in quotes if q.price_usd > 0]
    if not prices:
        return quotes, []

    median = statistics.median(prices)
    if median <= 0:
        return quotes, []

    clean: list[CanonicalPriceQuote] = []
    outliers: list[dict[str, Any]] = []

    for q in quotes:
        deviation_pct = abs(q.price_usd - median) / median * 100
        if deviation_pct > _OUTLIER_THRESHOLD_PCT and len(prices) >= 3:
            outliers.append(
                {
                    "connector_id": q.connector_id,
                    "exchange": q.exchange,
                    "price_usd": q.price_usd,
                    "median_usd": round(median, 6),
                    "deviation_pct": round(deviation_pct, 3),
                    "reason": "isolated_extreme_price_likely_api_error",
                    "source": q.source,
                }
            )
        else:
            clean.append(q)

    # Never drop all quotes — keep median-closest if everything flagged
    if not clean and quotes:
        best = min(quotes, key=lambda q: abs(q.price_usd - median))
        clean = [best]
        outliers = [o for o in outliers if o["connector_id"] != best.connector_id]

    return clean, outliers


def volume_weighted_average(quotes: list[CanonicalPriceQuote]) -> dict[str, Any]:
    """Volume-weighted average price across clean sources."""
    if not quotes:
        return {"vwap_usd": 0.0, "weighting": "none", "sources_used": 0}

    total_vol = sum(max(q.volume_24h_usd, 1.0) for q in quotes)
    if total_vol <= len(quotes):  # all zero volume — equal weight
        vwap = sum(q.price_usd for q in quotes) / len(quotes)
        return {
            "vwap_usd": round(vwap, 8),
            "weighting": "equal",
            "sources_used": len(quotes),
            "total_volume_usd": 0.0,
        }

    vwap = sum(q.price_usd * max(q.volume_24h_usd, 1.0) for q in quotes) / total_vol
    return {
        "vwap_usd": round(vwap, 8),
        "weighting": "volume",
        "sources_used": len(quotes),
        "total_volume_usd": round(total_vol, 2),
    }


def _build_source_metadata(
    results: list[ConnectorFetchResult],
    *,
    outliers: list[dict[str, Any]],
    used: list[CanonicalPriceQuote],
) -> dict[str, Any]:
    return {
        "connectors_polled": len(results),
        "connectors_ok": sum(1 for r in results if r.ok),
        "sources_used": [
            {
                "connector_id": q.connector_id,
                "exchange": q.exchange,
                "price_usd": q.price_usd,
                "volume_24h_usd": q.volume_24h_usd,
                "source": q.source,
                "latency_ms": q.latency_ms,
                "is_live": q.connector_id.startswith("ws_"),
            }
            for q in used
        ],
        "outliers_removed": outliers,
        "failed_connectors": [
            {"connector_id": r.connector_id, "error": r.error}
            for r in results
            if not r.ok
        ],
    }


def _append_snapshot(row: dict[str, Any]) -> None:
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SNAPSHOT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


async def _cache_set(asset: str, payload: dict[str, Any]) -> None:
    _CACHE[asset] = (time.time(), payload)
    try:
        from redis_price_cache import _redis

        client = await _redis()
        if client:
            await client.setex(
                f"price_agg:{asset}",
                5,
                json.dumps({"price_usd": payload.get("price_usd"), "vwap_usd": payload.get("vwap_usd")}),
            )
    except Exception:
        pass


async def aggregate_prices(asset: str = "BTC", *, use_cache: bool = True) -> dict[str, Any]:
    """
    #133 — collect, outlier-filter, volume-weight, attach source metadata.
    """
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")

    if use_cache:
        cached = _CACHE.get(sym)
        if cached and time.time() - cached[0] < _CACHE_TTL_SEC:
            out = dict(cached[1])
            out["cache_hit"] = True
            out["sla_met"] = (time.perf_counter() - t0) <= 2.0
            return out

    results = await fetch_all_connector_quotes(sym)
    quotes = [r.quote for r in results if r.ok and r.quote and r.quote.price_usd > 0]

    if len(quotes) < _MIN_SOURCES:
        elapsed = time.perf_counter() - t0
        return {
            "ok": False,
            "feature_ids": list(_FEATURE_IDS),
            "error": "insufficient_sources",
            "asset": sym,
            "sources_found": len(quotes),
            "sla_met": elapsed <= 2.0,
            "timestamp": _utcnow(),
        }

    clean, outliers = detect_outliers(quotes)

    from bd_platform.data_validation_layer import validate_quotes

    validation = validate_quotes(clean if clean else quotes, asset=sym, context="price_aggregation")
    validated_quotes = validation.get("validated_quotes") or clean
    if validation.get("flagged_count", 0) > 0:
        outliers = outliers + validation.get("flagged_events", [])

    vwap_block = volume_weighted_average(validated_quotes)
    metadata = _build_source_metadata(results, outliers=outliers, used=validated_quotes)

    # Best live price: prefer WS, else VWAP
    live_quotes = [q for q in validated_quotes if q.connector_id.startswith("ws_")]
    if live_quotes:
        price_usd = live_quotes[0].price_usd
        price_source = live_quotes[0].source
        refresh_mode = "live_ws_redis"
    else:
        price_usd = vwap_block["vwap_usd"]
        price_source = "volume_weighted_average"
        refresh_mode = "aggregated_rest"

    accuracy = 1.0 - (len(outliers) / max(len(quotes), 1)) * 0.5
    elapsed = time.perf_counter() - t0

    payload: dict[str, Any] = {
        "ok": True,
        "feature_ids": [133, 147, 194],
        "mode": "infrastructure",
        "user_facing": False,
        "asset": sym,
        "price_usd": round(price_usd, 8),
        "vwap_usd": vwap_block["vwap_usd"],
        "weighting": vwap_block["weighting"],
        "price_source": price_source,
        "source_metadata": metadata,
        "validation": {
            "feature_id": 147,
            "price_verified": validation.get("price_verified"),
            "user_badge": validation.get("user_badge"),
            "user_badge_ar": validation.get("user_badge_ar"),
            "flagged_count": validation.get("flagged_count", 0),
            "fallback_used": validation.get("fallback_used", False),
        },
        "user_badge": validation.get("user_badge"),
        "outlier_count": len(outliers),
        "accuracy_estimate": round(min(0.9999, accuracy), 4),
        "quotes_raw": len(quotes),
        "quotes_clean": len(validated_quotes),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "cache_hit": False,
        "timestamp": _utcnow(),
    }

    _append_snapshot({**payload, "stage": "aggregate"})
    await _cache_set(sym, payload)
    return payload


async def refresh_live_price(asset: str = "BTC") -> dict[str, Any]:
    """
    #127 — invisible live refresh (WS → Redis → REST fallback).
    Users never see this — prices auto-update across the platform.
    """
    t0 = time.perf_counter()
    agg = await aggregate_prices(asset, use_cache=False)
    if not agg.get("ok"):
        return agg

    sym = asset.upper().replace("/USDT", "")
    elapsed = time.perf_counter() - t0

    live_block = {
        "ok": True,
        "feature_ids": [127, 133, 194],
        "mode": "invisible_infrastructure",
        "user_facing": False,
        "asset": sym,
        "price_usd": agg["price_usd"],
        "vwap_usd": agg["vwap_usd"],
        "refresh_mode": "live_ws_redis" if any(
            s.get("is_live") for s in agg.get("source_metadata", {}).get("sources_used", [])
        ) else "aggregated_rest",
        "source_quality": {
            "connectors_ok": agg["source_metadata"]["connectors_ok"],
            "connectors_polled": agg["source_metadata"]["connectors_polled"],
            "outliers_removed": agg["outlier_count"],
        },
        "source_metadata": agg["source_metadata"],
        "sub_second_capable": agg.get("latency_ms", 999) < 1000,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }

    _append_snapshot({**live_block, "stage": "live_refresh"})
    await _cache_set(sym, {**agg, **live_block})
    return live_block


def price_aggregation_status() -> dict[str, Any]:
    from bd_platform.unified_connector_layer import connector_layer_status

    snapshot_rows = 0
    if _SNAPSHOT_PATH.exists():
        snapshot_rows = sum(1 for ln in _SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines() if ln.strip())

    return {
        "ok": True,
        "features": {
            "133": "price_collection",
            "127": "live_refresh_invisible",
            "147": "data_validation_layer",
            "194": "unified_connector_layer",
        },
        "user_facing": False,
        "outlier_threshold_pct": _OUTLIER_THRESHOLD_PCT,
        "validation_threshold_pct": 5.0,
        "cache_ttl_sec": _CACHE_TTL_SEC,
        "snapshot_rows": snapshot_rows,
        "connector_layer": connector_layer_status(),
        "pipeline": ["collect", "outlier_filter", "data_validation", "volume_weight", "source_metadata", "live_refresh"],
        "sla_target_ms": 2000,
        "timestamp": _utcnow(),
    }
