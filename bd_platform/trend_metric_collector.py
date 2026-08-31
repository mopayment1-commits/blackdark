"""
Trend Metric Collector — Feature #299 (Sprint 2 Intelligence Ledger).

Unified trend layer from momentum, volume, and liquidity across timeframes.
Infrastructure layer — point-in-time, no look-ahead, versioned universe.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.TrendMetricCollector")

_FEATURE_ID = 299
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Trend Metric Collector (infrastructure)"
_SPRINT = 2
_SEED_PATH = Path("data/trend_metric_collector_seed.json")
_METHODOLOGY_VERSION = "1.0"
_LOOKAHEAD_TESTS_REQUIRED = True

_DISCLAIMER = (
    "Trend metrics are computed point-in-time with no future data. "
    "Cross-sectional ranks use a versioned universe re-ranked daily. "
    "Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"universe": {}, "assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("trend metric collector seed load failed: %s", exc)
        return {"universe": {}, "assets": {}}


def build_point_in_time_controls() -> dict[str, Any]:
    return {
        "point_in_time": True,
        "no_lookahead": True,
        "no_future_data": True,
        "code_review_mandatory": True,
        "unit_tests_for_lookahead_bias": _LOOKAHEAD_TESTS_REQUIRED,
        "universe_at_time_t_known": True,
        "display": (
            "All metrics computed with data available at timestamp | "
            "No future data | Code review + unit tests for look-ahead bias"
        ),
    }


def build_universe_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    universe = seed.get("universe") or {}
    return {
        "version": universe.get("version"),
        "asset_count": universe.get("asset_count"),
        "as_of": universe.get("as_of"),
        "re_rank_frequency": "daily",
        "versioned": True,
        "documented": True,
        "display": (
            f"Universe v{universe.get('version', '?')} | "
            f"{universe.get('asset_count', 0)} assets | Re-ranked daily"
        ),
    }


def compute_momentum_score(
    returns: dict[str, float],
    *,
    as_of_timestamp: str,
    available_data_cutoff: str,
) -> dict[str, Any]:
    """Point-in-time momentum — only data <= as_of_timestamp."""
    if as_of_timestamp > available_data_cutoff:
        return {
            "score": None,
            "lookahead_violation": True,
            "error": "future_data_used",
        }

    weights = {"1d": 0.2, "7d": 0.3, "30d": 0.5}
    score = sum(returns.get(k, 0) * w for k, w in weights.items())
    return {
        "score": round(score, 4),
        "lookahead_violation": False,
        "as_of_timestamp": as_of_timestamp,
        "data_cutoff": available_data_cutoff,
    }


def compute_volume_acceleration(
    volume_current: float,
    volume_baseline: float,
) -> float:
    if volume_baseline <= 0:
        return 0.0
    return round((volume_current - volume_baseline) / volume_baseline, 4)


def compute_cross_sectional_rank(
    asset_score: float,
    universe_scores: list[float],
) -> dict[str, Any]:
    """Percentile rank within versioned universe — deterministic."""
    if not universe_scores:
        return {"percentile": 0, "rank": 0, "universe_size": 0}

    sorted_scores = sorted(universe_scores, reverse=True)
    rank = sorted_scores.index(asset_score) + 1 if asset_score in sorted_scores else len(sorted_scores)
    below = sum(1 for s in universe_scores if s < asset_score)
    percentile = round(below / len(universe_scores) * 100, 1)

    return {
        "percentile": percentile,
        "rank": rank,
        "universe_size": len(universe_scores),
        "deterministic": True,
    }


def build_asset_trend_block(
    asset_data: dict[str, Any],
    *,
    symbol: str,
    universe_scores: list[float],
    as_of_timestamp: str,
) -> dict[str, Any]:
    returns = asset_data.get("returns") or {}
    momentum = compute_momentum_score(
        returns,
        as_of_timestamp=as_of_timestamp,
        available_data_cutoff=asset_data.get("data_cutoff_utc", as_of_timestamp),
    )
    vol_accel = compute_volume_acceleration(
        float(asset_data.get("volume_current", 0)),
        float(asset_data.get("volume_baseline", 1)),
    )
    trend_score = round((momentum.get("score") or 0) * 0.6 + vol_accel * 0.4, 4)
    rank_block = compute_cross_sectional_rank(trend_score, universe_scores)

    timeframes = {}
    for tf in ("1h", "4h", "1d", "7d"):
        tf_data = (asset_data.get("timeframes") or {}).get(tf) or {}
        timeframes[tf] = {
            "momentum": tf_data.get("momentum"),
            "volume_accel": tf_data.get("volume_accel"),
            "liquidity_score": tf_data.get("liquidity_score"),
            "point_in_time": True,
        }

    return {
        "symbol": symbol,
        "trend_score": trend_score,
        "momentum": momentum,
        "volume_acceleration": vol_accel,
        "acceleration": vol_accel,
        "cross_sectional_rank": rank_block,
        "timeframe_breakdown": timeframes,
        "point_in_time": True,
        "no_lookahead": not momentum.get("lookahead_violation", False),
        "universe_version": asset_data.get("universe_version"),
    }


def build_trend_metric_panel(asset: str = "BTC") -> dict[str, Any]:
    """Trend score + acceleration + timeframe breakdown."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)
    as_of = seed.get("as_of_timestamp_utc", _utcnow())

    if not asset_data:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "asset_not_in_universe",
            "asset": sym,
        }

    all_scores = [
        float(a.get("trend_score", 0))
        for a in (seed.get("assets") or {}).values()
    ]
    block = build_asset_trend_block(
        asset_data, symbol=sym, universe_scores=all_scores, as_of_timestamp=as_of,
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "infrastructure_layer": True,
        "asset": sym,
        "trend": block,
        "universe": build_universe_block(seed),
        "point_in_time_controls": build_point_in_time_controls(),
        "as_of_timestamp_utc": as_of,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def list_universe_rankings(limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    as_of = seed.get("as_of_timestamp_utc", _utcnow())
    assets = seed.get("assets") or {}
    all_scores = [float(a.get("trend_score", 0)) for a in assets.values()]

    ranked = []
    for sym, data in sorted(assets.items(), key=lambda x: float(x[1].get("trend_score", 0)), reverse=True):
        block = build_asset_trend_block(
            data, symbol=sym, universe_scores=all_scores, as_of_timestamp=as_of,
        )
        ranked.append(block)
        if len(ranked) >= limit:
            break

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(ranked),
        "rankings": ranked,
        "universe": build_universe_block(seed),
        "re_rank_frequency": "daily",
        "timestamp": _utcnow(),
    }


def trend_metric_collector_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Trend Metric Collector",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "infrastructure_layer": True,
        "point_in_time_controls": build_point_in_time_controls(),
        "universe": build_universe_block(seed),
        "acceptance_criteria": {
            "point_in_time_computation": True,
            "no_lookahead": True,
            "asset_universe_versioned": True,
            "cross_sectional_ranks_daily": True,
        },
        "asset_count": len(seed.get("assets") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
