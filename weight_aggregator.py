"""
BLACKDARK — Hybrid Multi-Modal Weight Aggregator (Point 45).

Merges technical, on-chain, sentiment, macro, and whale dimensions into
a unified weight profile that feeds the Opportunity Score engine.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from log_safety import sanitize_asset
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

# Regime-tilted dimension profiles (normalized at use time).
_REGIME_DIMENSIONS: dict[str, dict[str, float]] = {
    "risk_on": {
        "technical": 0.30,
        "onchain": 0.15,
        "sentiment": 0.25,
        "macro": 0.10,
        "whale": 0.20,
    },
    "neutral": dict(DEFAULT_DIMENSIONS),
    "risk_off": {
        "technical": 0.25,
        "onchain": 0.30,
        "sentiment": 0.10,
        "macro": 0.25,
        "whale": 0.10,
    },
    "panic": {
        "technical": 0.20,
        "onchain": 0.35,
        "sentiment": 0.05,
        "macro": 0.30,
        "whale": 0.10,
    },
}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


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


def detect_market_regime(
    institutional_context: dict[str, Any] | None = None,
    *,
    change_24h: float = 0.0,
) -> str:
    """Classify market regime for dimension tilting and retention UX."""
    ctx = institutional_context or {}
    macro = str(ctx.get("macro_regime") or "").strip().lower().replace(" ", "_")
    if macro in {"risk-off", "risk_off"}:
        base = "risk_off"
    elif macro in {"risk-on", "risk_on"}:
        base = "risk_on"
    else:
        base = "neutral"

    if change_24h <= -8.0 or float(ctx.get("macro_volatility_buffer") or 0) >= 12:
        return "panic"
    if change_24h <= -3.0 and base != "risk_on":
        return "risk_off"
    if change_24h >= 5.0 and base != "risk_off":
        return "risk_on"
    return base


def get_regime_dimension_weights(regime: str) -> dict[str, float]:
    key = (regime or "neutral").strip().lower().replace("-", "_")
    profile = _REGIME_DIMENSIONS.get(key) or _REGIME_DIMENSIONS["neutral"]
    return _normalize(dict(profile))


def _detect_dimension_conflicts(
    *,
    technical_adj: float,
    onchain_adj: float,
    sentiment_adj: float,
    whale_adj: float,
    macro_mult: float,
) -> dict[str, Any]:
    """Emit conflict metadata consumed by dimension_conflict_guard."""
    signals = {
        "technical": technical_adj,
        "onchain": onchain_adj,
        "sentiment": sentiment_adj,
        "whale": whale_adj,
        "macro": (macro_mult - 1.0) * 10.0,
    }
    bullish = [name for name, value in signals.items() if value >= 2.5]
    bearish = [name for name, value in signals.items() if value <= -2.5]

    severity = "none"
    confidence_penalty = 0.0
    message = ""
    if bullish and bearish:
        if len(bullish) >= 2 and len(bearish) >= 2:
            severity = "severe"
            confidence_penalty = 18.0
            message = "Severe multi-modal conflict between bullish and bearish dimensions"
        else:
            severity = "mild"
            confidence_penalty = 8.0
            message = "Mild multi-modal conflict across market dimensions"

    return {
        "severity": severity,
        "bullish": bullish,
        "bearish": bearish,
        "confidence_penalty": confidence_penalty,
        "message": message,
        "signals": {k: round(v, 3) for k, v in signals.items()},
    }


def compute_modal_breakdown(
    asset: str,
    institutional_context: dict[str, Any] | None = None,
    *,
    change_24h: float = 0.0,
    quote_volume: float = 0.0,
) -> dict[str, Any]:
    ctx = institutional_context or {}
    regime = detect_market_regime(ctx, change_24h=change_24h)
    dims = get_regime_dimension_weights(regime)

    technical_adj = obi_score_adjustment_for_asset(asset, ctx)
    onchain_adj = onchain_score_adjustment_for_asset(asset, ctx)
    sentiment_adj = sentiment_score_adjustment_for_asset(asset, ctx)
    whale_adj = whale_score_boost_for_asset(asset, ctx)
    macro_mult = macro_score_weight(ctx)

    obi = get_obi_for_asset(asset, ctx)
    onchain = get_onchain_status_for_asset(asset, ctx)
    sentiment = get_sentiment_index_for_asset(asset, ctx)
    conflicts = _detect_dimension_conflicts(
        technical_adj=technical_adj,
        onchain_adj=onchain_adj,
        sentiment_adj=sentiment_adj,
        whale_adj=whale_adj,
        macro_mult=macro_mult,
    )

    weighted_contribution = (
        technical_adj * dims["technical"]
        + onchain_adj * dims["onchain"]
        + sentiment_adj * dims["sentiment"]
        + whale_adj * dims["whale"]
    )
    macro_contribution = (macro_mult - 1.0) * 10.0 * dims["macro"]

    return {
        "asset": asset,
        "market_regime": regime,
        "dimension_weights": dims,
        "core_weights": get_core_score_weights(),
        "change_24h": change_24h,
        "quote_volume": quote_volume,
        "signals": {
            "technical": {"adjustment": round(technical_adj, 3), "obi": obi},
            "onchain": {"adjustment": round(onchain_adj, 3), "status": onchain},
            "sentiment": {"adjustment": round(sentiment_adj, 3), "compound": sentiment},
            "whale": {"adjustment": round(whale_adj, 3)},
            "macro": {"multiplier": round(macro_mult, 4)},
        },
        "conflicts": conflicts,
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


def apply_modal_adjustments_with_regime(
    base_score: float,
    asset: str,
    institutional_context: dict[str, Any] | None = None,
    *,
    change_24h: float = 0.0,
    quote_volume: float = 0.0,
) -> tuple[float, dict[str, Any]]:
    breakdown = compute_modal_breakdown(
        asset,
        institutional_context,
        change_24h=change_24h,
        quote_volume=quote_volume,
    )
    adjusted = max(0.0, min(100.0, base_score + breakdown["total_modal_adjustment"]))
    return adjusted, breakdown


async def build_full_market_context(asset: str) -> dict[str, Any]:
    """Assemble multi-modal context used by the unified Oracle path."""
    asset = asset.upper().replace("USDT", "").replace("/", "")
    ctx: dict[str, Any] = {}

    try:
        from whale_tracker import get_latest_institutional_context

        ctx.update(await get_latest_institutional_context())
    except Exception:
        logger.debug("Institutional context unavailable | asset=%s", sanitize_asset(asset), exc_info=True)

    try:
        from database import fetch_latest_order_books
        from obi_predictor import build_obi_context_safe, merge_market_context

        books = await fetch_latest_order_books()
        obi_context = await build_obi_context_safe(books)
        ctx = merge_market_context(ctx, obi_context)
    except Exception:
        logger.debug("OBI context unavailable | asset=%s", sanitize_asset(asset), exc_info=True)

    try:
        from onchain_tracker import build_onchain_context_safe, merge_onchain_context

        onchain_context = await build_onchain_context_safe()
        ctx = merge_onchain_context(ctx, onchain_context)
    except Exception:
        logger.debug("On-chain context unavailable | asset=%s", sanitize_asset(asset), exc_info=True)

    try:
        from sentiment_engine import (
            load_active_sentiment_indices_for_valuation_safe,
            merge_sentiment_context,
        )

        sentiment_context = await load_active_sentiment_indices_for_valuation_safe()
        ctx = merge_sentiment_context(ctx, sentiment_context)
    except Exception:
        logger.debug("Sentiment context unavailable | asset=%s", sanitize_asset(asset), exc_info=True)

    try:
        from macro_correlations import get_latest_macro_regime, merge_macro_context

        macro_context = await get_latest_macro_regime()
        ctx = merge_macro_context(ctx, macro_context)
    except Exception:
        logger.debug("Macro context unavailable | asset=%s", sanitize_asset(asset), exc_info=True)

    try:
        from oracle_data_hub import build_hub_context_safe, merge_hub_context

        hub_context = await build_hub_context_safe(asset)
        ctx = merge_hub_context(ctx, hub_context)
    except Exception:
        logger.debug("Oracle hub context unavailable | asset=%s", sanitize_asset(asset), exc_info=True)

    return ctx
