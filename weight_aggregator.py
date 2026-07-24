"""
BLACKDARK — Hybrid Multi-Modal Weight Aggregator (Point 45).

Merges technical, on-chain, sentiment, macro, and whale dimensions into
a unified weight profile that feeds the Opportunity Score engine.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from macro_correlations import macro_score_weight
from model_weights_guard import load_weights, save_weights
from obi_predictor import get_obi_for_asset, obi_score_adjustment_for_asset
from onchain_tracker import get_onchain_status_for_asset, onchain_score_adjustment_for_asset
from sentiment_engine import get_sentiment_index_for_asset, sentiment_score_adjustment_for_asset
from whale_tracker import whale_score_boost_for_asset

logger = logging.getLogger("BLACKDARK.WeightAggregator")

DEFAULT_DIMENSIONS: dict[str, float] = {
    "technical": 0.35,
    "onchain": 0.20,
    "sentiment": 0.20,
    "macro": 0.15,
    "whale": 0.10,
}

_CORE_WEIGHTS: dict[str, float] = {
    "profit": 0.40,
    "liquidity": 0.35,
    "stability": 0.25,
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, v) for v in weights.values()) or 1.0
    return {k: round(max(0.0, v) / total, 4) for k, v in weights.items()}


def get_dimension_weights() -> dict[str, float]:
    stored = load_weights()
    if stored and stored.get("dimensions"):
        merged = dict(DEFAULT_DIMENSIONS)
        merged.update({k: float(v) for k, v in stored["dimensions"].items()})
        return _normalize(merged)
    return dict(DEFAULT_DIMENSIONS)


def get_core_score_weights() -> dict[str, float]:
    stored = load_weights()
    if stored and stored.get("core"):
        merged = dict(_CORE_WEIGHTS)
        merged.update({k: float(v) for k, v in stored["core"].items()})
        return _normalize(merged)
    return dict(_CORE_WEIGHTS)


def persist_dimension_weights(
    dimensions: dict[str, float],
    *,
    core: dict[str, float] | None = None,
    note: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "dimensions": _normalize(dimensions),
        "core": _normalize(core or get_core_score_weights()),
        "updated_at": _utcnow_iso(),
        "note": note,
    }
    save_weights(payload)
    return payload


def compute_modal_breakdown(
    asset: str,
    institutional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = institutional_context or {}
    dims = get_dimension_weights()

    technical_adj = obi_score_adjustment_for_asset(asset, ctx)
    onchain_adj = onchain_score_adjustment_for_asset(asset, ctx)
    sentiment_adj = sentiment_score_adjustment_for_asset(asset, ctx)
    whale_adj = whale_score_boost_for_asset(asset, ctx)
    macro_mult = macro_score_weight(ctx)

    obi = get_obi_for_asset(asset, ctx)
    onchain = get_onchain_status_for_asset(asset, ctx)
    sentiment = get_sentiment_index_for_asset(asset, ctx)

    weighted_contribution = (
        technical_adj * dims["technical"]
        + onchain_adj * dims["onchain"]
        + sentiment_adj * dims["sentiment"]
        + whale_adj * dims["whale"]
    )
    macro_contribution = (macro_mult - 1.0) * 10.0 * dims["macro"]

    return {
        "asset": asset,
        "dimension_weights": dims,
        "core_weights": get_core_score_weights(),
        "signals": {
            "technical": {"adjustment": round(technical_adj, 3), "obi": obi},
            "onchain": {"adjustment": round(onchain_adj, 3), "status": onchain},
            "sentiment": {"adjustment": round(sentiment_adj, 3), "compound": sentiment},
            "whale": {"adjustment": round(whale_adj, 3)},
            "macro": {"multiplier": round(macro_mult, 4)},
        },
        "total_modal_adjustment": round(weighted_contribution + macro_contribution, 3),
        "timestamp": _utcnow_iso(),
    }


def apply_modal_adjustments(
    base_score: float,
    asset: str,
    institutional_context: dict[str, Any] | None = None,
) -> tuple[float, dict[str, Any]]:
    breakdown = compute_modal_breakdown(asset, institutional_context)
    adjusted = max(0.0, min(100.0, base_score + breakdown["total_modal_adjustment"]))
    return adjusted, breakdown
