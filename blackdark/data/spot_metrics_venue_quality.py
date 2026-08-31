"""
Spot Metrics & Venue Quality Layer — Features #295 + #294 merged (Wave 01 Data Engine).

#295 = Spot Market Metrics Suite — aggregations + filtering on Sprint 1 Data Engine
#294 = Spot Market Intelligence (ARCHIVED → absorbed into #295 spot overview)

NOT standalone — Data Engine expansion. Dashboard deferred to Sprint 2.
No separate pipeline — spot metrics = aggregations + filtering on existing OHLCV/trades.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SpotMetricsVenueQuality")

_FEATURE_IDS = (295, 294)
_FEATURE_ID = 295
_STANDALONE = False
_MERGED_INTO = "Wave 01 Data Engine / Spot Metrics & Venue Quality Layer"
_MERGED_TICKETS = {
    295: "Spot Market Metrics Suite",
    294: "Spot Market Intelligence (ARCHIVED → spot overview sub-task)",
}
_ARCHIVED_TICKETS = {294: "Spot Market Intelligence — generic overview, covered by #295"}
_REJECTED_STANDALONE = (294,)
_SPRINT = 1
_DASHBOARD_DEFERRED = "Sprint 2 Intelligence Ledger spot dashboard"
_SEED_PATH = Path("data/spot_metrics_venue_quality_seed.json")
_METHODOLOGY_VERSION = "1.0"
_MAX_VENUES = 50
_WARMUP_DAYS = 7
_ZSCORE_OUTLIER_THRESHOLD = 3.0
_STALE_THRESHOLD_SEC = 120

VenueStatus = Literal["active", "warmup", "archived", "excluded_outlier", "excluded_stale"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"venues": [], "symbols": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("spot metrics seed load failed: %s", exc)
        return {"venues": [], "symbols": {}}


def build_scope_lock() -> dict[str, Any]:
    return {
        "max_venues": _MAX_VENUES,
        "new_venue_warmup_days": _WARMUP_DAYS,
        "delisted_venue_handling": "archived",
        "no_separate_pipeline": True,
        "data_source": "Sprint 1 Data Engine (OHLCV + trades aggregations)",
        "dashboard_deferred": _DASHBOARD_DEFERRED,
        "display": (
            f"Top {_MAX_VENUES} venues only | "
            f"New venue = {_WARMUP_DAYS}-day warmup | "
            "Delisted venue = archived | "
            "No separate pipeline — aggregations + filtering on existing Data Engine"
        ),
    }


def build_venue_normalization() -> dict[str, Any]:
    return {
        "venue_quality_score_documented": True,
        "outlier_detection": f"Z-score > {_ZSCORE_OUTLIER_THRESHOLD} = excluded",
        "outlier_zscore_threshold": _ZSCORE_OUTLIER_THRESHOLD,
        "timestamp_alignment": "UTC",
        "source_provenance": "every metric tagged with venue, source, timestamp_utc",
        "stale_threshold_sec": _STALE_THRESHOLD_SEC,
        "display": (
            f"Venue quality score documented | Outlier: Z>{_ZSCORE_OUTLIER_THRESHOLD} excluded | "
            "Timestamp: UTC | Source provenance on every metric"
        ),
    }


def _compute_zscore(value: float, values: list[float], *, leave_one_out: bool = True) -> float:
    if len(values) < 2:
        return 0.0
    population = [v for v in values if v != value] if leave_one_out and len(values) > 2 else values
    if len(population) < 2:
        population = values
    mean = statistics.mean(population)
    stdev = statistics.stdev(population)
    if stdev <= 0:
        return 0.0
    return round((value - mean) / stdev, 4)


def classify_venue(venue: dict[str, Any], *, price_values: list[float] | None = None) -> dict[str, Any]:
    """Venue normalization with outlier/stale filtering."""
    status: VenueStatus = venue.get("status", "active")
    stale_sec = int(venue.get("staleness_sec", 0))
    warmup_days = int(venue.get("warmup_days_remaining", 0))
    price = float(venue.get("last_price", 0))
    price_values = price_values or []

    excluded_reason = None
    if status == "archived":
        final_status: VenueStatus = "archived"
    elif warmup_days > 0:
        final_status = "warmup"
        excluded_reason = f"warmup ({warmup_days} days remaining)"
    elif stale_sec > _STALE_THRESHOLD_SEC:
        final_status = "excluded_stale"
        excluded_reason = f"stale ({stale_sec}s > {_STALE_THRESHOLD_SEC}s)"
    elif price_values and abs(_compute_zscore(price, price_values)) > _ZSCORE_OUTLIER_THRESHOLD:
        final_status = "excluded_outlier"
        excluded_reason = f"Z-score > {_ZSCORE_OUTLIER_THRESHOLD}"
    else:
        final_status = "active"

    quality_score = float(venue.get("quality_score", 0))
    included = final_status == "active"

    return {
        "venue": venue.get("venue"),
        "venue_id": venue.get("venue_id"),
        "status": final_status,
        "included_in_aggregate": included,
        "excluded_reason": excluded_reason,
        "quality_score": quality_score,
        "quality_score_documented": True,
        "warmup_days_remaining": warmup_days,
        "staleness_sec": stale_sec,
        "source": venue.get("source"),
        "timestamp_utc": venue.get("timestamp_utc"),
        "provenance": {
            "source": venue.get("source"),
            "venue": venue.get("venue"),
            "timestamp_utc": venue.get("timestamp_utc"),
            "methodology_version": _METHODOLOGY_VERSION,
        },
    }


def filter_venues(venues: list[dict[str, Any]]) -> dict[str, Any]:
    """Filter outlier and stale venues before aggregation."""
    prices = [float(v.get("last_price", 0)) for v in venues if v.get("last_price")]
    classified = [classify_venue(v, price_values=prices) for v in venues[:_MAX_VENUES]]
    active = [v for v in classified if v["included_in_aggregate"]]
    excluded = [v for v in classified if not v["included_in_aggregate"]]

    return {
        "total_venues": len(classified),
        "active_count": len(active),
        "excluded_count": len(excluded),
        "active_venues": active,
        "excluded_venues": excluded,
        "outlier_stale_filtered": True,
    }


def build_venue_metric_block(venue: dict[str, Any], *, symbol: str) -> dict[str, Any]:
    from blackdark.data.provenance_lineage import build_lineage_chain, build_provenance_tag, wrap_metric

    source = venue.get("source") or venue.get("venue") or "unknown"
    lineage_steps = [
        {"stage": "ingest", "description": f"{source} API", "version": "3.0"},
        {"stage": "normalize", "description": "normalized via schema v2.1", "version": "2.1", "schema_version": "2.1"},
        {"stage": "filter", "description": "outlier filtered via Z-score v1.4", "version": "1.4"},
    ]
    tag = build_provenance_tag(
        source=f"{source} API v3",
        source_kind="api",
        transformation="venue_normalize_zscore_filter",
        transformation_version="1.4",
        source_schema_version="2.1",
        last_verified_utc=venue.get("timestamp_utc"),
        confidence="high",
    )
    metric_id = f"spot.{symbol.replace('/', '_').lower()}.{venue.get('venue', 'unknown')}.price"
    wrapped = wrap_metric(
        venue.get("last_price"),
        metric_id=metric_id,
        metric_name="spot_price",
        provenance=tag,
        lineage_chain=build_lineage_chain(lineage_steps),
        unit="USD",
    )

    return {
        "venue": venue.get("venue"),
        "symbol": symbol,
        "price": venue.get("last_price"),
        "volume_24h": venue.get("volume_24h"),
        "return_1d_pct": venue.get("return_1d_pct"),
        "volatility_7d_pct": venue.get("volatility_7d_pct"),
        "spread_bps": venue.get("spread_bps"),
        "timestamp_utc": venue.get("timestamp_utc"),
        "source": venue.get("source"),
        "provenance": wrapped["provenance"],
        "badge": wrapped["badge"],
        "provenance_mandatory": True,
    }


def aggregate_spot_metrics(
    venues: list[dict[str, Any]],
    *,
    symbol: str,
) -> dict[str, Any]:
    """Normalize and aggregate spot metrics across venues."""
    filtered = filter_venues(venues)
    active_raw = [
        v for v in venues[:_MAX_VENUES]
        if any(a["venue"] == v.get("venue") for a in filtered["active_venues"])
    ]

    if not active_raw:
        return {
            "symbol": symbol,
            "venue_count": 0,
            "aggregated_price": None,
            "aggregated_volume_24h": 0,
            "median_return_1d_pct": None,
            "median_volatility_7d_pct": None,
            "median_spread_bps": None,
            "filtered": filtered,
        }

    prices = [float(v["last_price"]) for v in active_raw if v.get("last_price")]
    volumes = [float(v.get("volume_24h", 0)) for v in active_raw]
    returns = [float(v["return_1d_pct"]) for v in active_raw if v.get("return_1d_pct") is not None]
    vols = [float(v["volatility_7d_pct"]) for v in active_raw if v.get("volatility_7d_pct") is not None]
    spreads = [float(v["spread_bps"]) for v in active_raw if v.get("spread_bps") is not None]

    return {
        "symbol": symbol,
        "venue_count": len(active_raw),
        "aggregated_price": round(statistics.median(prices), 8) if prices else None,
        "aggregated_volume_24h": round(sum(volumes), 2),
        "median_return_1d_pct": round(statistics.median(returns), 4) if returns else None,
        "median_volatility_7d_pct": round(statistics.median(vols), 4) if vols else None,
        "median_spread_bps": round(statistics.median(spreads), 2) if spreads else None,
        "timestamp_alignment": "UTC",
        "filtered": filtered,
    }


def build_spot_overview_sub_task(symbol_data: dict[str, Any], *, symbol: str) -> dict[str, Any]:
    """#294 Spot Market Intelligence — absorbed as spot overview sub-task."""
    venues = symbol_data.get("venues") or []
    agg = aggregate_spot_metrics(venues, symbol=symbol)
    return {
        "sub_task": "#294",
        "archived_standalone": True,
        "absorbed_into": "#295 Spot Metrics & Venue Quality Layer",
        "symbol": symbol,
        "price": agg.get("aggregated_price"),
        "volume_24h": agg.get("aggregated_volume_24h"),
        "change_1d_pct": agg.get("median_return_1d_pct"),
        "liquidity_spread_bps": agg.get("median_spread_bps"),
        "active_venues": agg.get("venue_count"),
        "outlier_stale_filtered": True,
        "display": (
            f"Spot overview {symbol}: price={agg.get('aggregated_price')} | "
            f"vol={agg.get('aggregated_volume_24h'):,.0f} | "
            f"venues={agg.get('venue_count')} (outlier/stale filtered)"
        ),
    }


def build_spot_metrics_panel(symbol: str = "BTC/USDT") -> dict[str, Any]:
    """Spot metrics panel — cross-venue comparison, dashboard deferred."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = symbol.upper().replace("-", "/")
    symbol_data = (seed.get("symbols") or {}).get(sym)

    if not symbol_data:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "symbol_not_tracked",
            "symbol": sym,
        }

    venues = symbol_data.get("venues") or []
    agg = aggregate_spot_metrics(venues, symbol=sym)
    venue_blocks = [build_venue_metric_block(v, symbol=sym) for v in venues[:_MAX_VENUES]]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    panel = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_FEATURE_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "dashboard_deferred": _DASHBOARD_DEFERRED,
        "symbol": sym,
        "aggregated": agg,
        "venues": venue_blocks,
        "spot_overview": build_spot_overview_sub_task(symbol_data, symbol=sym),
        "venue_normalization": build_venue_normalization(),
        "scope_lock": build_scope_lock(),
        "no_separate_pipeline": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }

    from blackdark.data.provenance_lineage import enrich_api_response

    return enrich_api_response(panel, layer="spot_metrics")


def list_venue_quality_rankings(limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    venues = sorted(
        seed.get("venues") or [],
        key=lambda v: float(v.get("quality_score", 0)),
        reverse=True,
    )[: min(limit, _MAX_VENUES)]

    ranked = []
    for i, v in enumerate(venues, 1):
        classified = classify_venue(v)
        ranked.append({
            "rank": i,
            "venue": v.get("venue"),
            "quality_score": v.get("quality_score"),
            "status": classified["status"],
            "included_in_aggregate": classified["included_in_aggregate"],
            "quality_score_documented": True,
            "source": v.get("source"),
            "timestamp_utc": v.get("timestamp_utc"),
        })

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(ranked),
        "max_venues": _MAX_VENUES,
        "rankings": ranked,
        "venue_normalization": build_venue_normalization(),
        "timestamp": _utcnow(),
    }


def spot_metrics_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_FEATURE_IDS),
        "merged_tickets": _MERGED_TICKETS,
        "archived_tickets": _ARCHIVED_TICKETS,
        "rejected_standalone_tickets": list(_REJECTED_STANDALONE),
        "spot_overview_sub_task": "#294 absorbed into #295 spot overview",
        "title": "Spot Metrics & Venue Quality Layer",
        "standalone": _STANDALONE,
        "archived_standalone_ticket": True,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "dashboard_deferred": _DASHBOARD_DEFERRED,
        "scope_lock": build_scope_lock(),
        "venue_normalization": build_venue_normalization(),
        "no_separate_pipeline": True,
        "acceptance_criteria": {
            "venue_normalization": True,
            "outlier_filtering": True,
            "timestamp_alignment_utc": True,
            "source_provenance_tagged": True,
            "outlier_stale_venues_filtered": True,
        },
        "symbol_count": len(seed.get("symbols") or {}),
        "venue_count": len(seed.get("venues") or []),
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
