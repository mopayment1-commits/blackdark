"""
BLACKDARK — Unified Oracle Scoring (single decision path).

Dashboard Oracle and arbitrage scoring share the same multi-modal pipeline:
base technical score → regime-weighted dimensions → conflict resolution → optional ML.
"""

from __future__ import annotations

import logging
from typing import Any

from oracle_data_hub import hub_score_adjustment
from sentiment_engine import is_extreme_negative_sentiment, sentiment_panic_penalty_for_asset
from sentiment_manipulation_guard import (
    greed_pump_penalty_for_asset as sentiment_greed_penalty_for_asset,
    is_extreme_positive_sentiment,
)
from dimension_conflict_guard import apply_dimension_conflict_guard
from weight_aggregator import apply_modal_adjustments_with_regime, build_full_market_context

logger = logging.getLogger("BLACKDARK.OracleUnified")


def compute_base_technical_score(quote_volume: float, change: float) -> int:
    """Volume + 24h momentum baseline (same rules as legacy dashboard oracle)."""
    score = 50
    if quote_volume > 1_000_000_000:
        score += 20
    elif quote_volume > 100_000_000:
        score += 15
    elif quote_volume > 10_000_000:
        score += 10
    if 0 < change < 3:
        score += 20
    elif 3 <= change < 8:
        score += 15
    elif 8 <= change < 15:
        score += 5
    elif change >= 15:
        score -= 15
    elif -3 < change <= 0:
        score -= 5
    elif -8 < change <= -3:
        score -= 15
    elif change <= -8:
        score -= 25
    return max(0, min(100, score))


def _oracle_verdict_from_score(score: int, asset: str) -> str:
    from regulatory_compliance_guard import to_public_verdict

    stablecoins = {
        "USDC", "USDT", "USD1", "DAI", "FDUSD", "USDE", "USDS",
        "TUSD", "BUSD", "EURC", "RLUSD", "USDG",
    }
    if asset.upper() in stablecoins:
        return to_public_verdict("WAIT")
    if score >= 75:
        return to_public_verdict("BUY")
    if score >= 50:
        return to_public_verdict("WAIT")
    if score >= 30:
        return to_public_verdict("CAUTION")
    return to_public_verdict("SELL")


def unified_verdict_with_conflict(
    score: int,
    asset: str,
    conflict_meta: dict[str, Any],
    *,
    base_verdict: str | None = None,
) -> str:
    """Map score + conflict state to compliant dashboard verdict."""
    from regulatory_compliance_guard import to_public_verdict

    if conflict_meta.get("veto"):
        return to_public_verdict("WAIT")
    if conflict_meta.get("abstain") and score >= 50:
        return to_public_verdict("CAUTION")
    if base_verdict:
        return to_public_verdict(base_verdict)
    return _oracle_verdict_from_score(score, asset)


def _confidence_from_score(
    score: int,
    change: float,
    quote_volume: float,
    *,
    conflict_penalty: float = 0.0,
    ml_confidence: float | None = None,
) -> int:
    base = min(100, max(50, int(score * 0.8 + abs(change) * 2 + (quote_volume / 1e9) * 5)))
    adjusted = base - int(conflict_penalty)
    if ml_confidence is not None and ml_confidence > 0:
        adjusted = int(round(adjusted * 0.7 + ml_confidence * 0.3))
    return max(20, min(98, adjusted))


async def _optional_ml_nudge(asset: str, price: float, score: float) -> dict[str, Any]:
    try:
        from ml.inference import predict_direction

        ml = await predict_direction(asset, price=price)
    except Exception:
        logger.debug("ML inference skipped | asset=%s", asset, exc_info=True)
        return {"available": False, "nudge": 0.0}

    if not ml.get("available"):
        return {"available": False, "reason": ml.get("reason"), "nudge": 0.0}

    direction = str(ml.get("direction") or "flat").lower()
    raw_conf = float((ml.get("confidence_calibrated") or {}).get("percent") or 0)
    nudge = 0.0
    if raw_conf >= 55:
        if direction == "up" and score >= 45:
            nudge = min(5.0, raw_conf / 20.0)
        elif direction == "down" and score <= 55:
            nudge = -min(5.0, raw_conf / 20.0)
        elif direction == "up" and score < 45:
            nudge = -2.0
        elif direction == "down" and score > 55:
            nudge = 2.0

    return {
        "available": True,
        "direction": direction,
        "confidence_percent": raw_conf,
        "nudge": round(nudge, 2),
        "engine": ml.get("engine"),
        "model_version": ml.get("model_version"),
    }


async def compute_unified_oracle(
    asset: str,
    price: float,
    quote_volume: float,
    change: float,
    *,
    include_ml: bool = True,
) -> dict[str, Any]:
    """
    Single scoring path for all Oracle consumers.

    Returns opportunity_score, verdict, regime, breakdown, conflicts, and context.
    """
    asset = asset.upper()
    base_score = float(compute_base_technical_score(quote_volume, change))

    ctx = await build_full_market_context(asset)

    compound = float((ctx.get("sentiment_compound_index") or {}).get(asset, 0.0))
    if is_extreme_negative_sentiment(compound):
        base_score -= sentiment_panic_penalty_for_asset(asset, ctx)
    elif is_extreme_positive_sentiment(compound):
        base_score -= sentiment_greed_penalty_for_asset(asset, ctx)

    adjusted, breakdown = apply_modal_adjustments_with_regime(
        base_score,
        asset,
        ctx,
        change_24h=change,
        quote_volume=quote_volume,
    )

    hub = ctx.get("oracle_data_hub") or {}
    hub_delta = 0.0
    hub_reasons: list[str] = []
    hub_risks: list[str] = []
    if hub.get("enabled"):
        hub_delta, hub_reasons, hub_risks = hub_score_adjustment(asset, hub)
        adjusted += hub_delta

    ml_meta: dict[str, Any] = {"available": False, "nudge": 0.0}
    if include_ml:
        ml_meta = await _optional_ml_nudge(asset, price, adjusted)
        adjusted += float(ml_meta.get("nudge") or 0.0)

    adjusted, conflict_meta = apply_dimension_conflict_guard(adjusted, breakdown)
    final_score = int(round(max(0.0, min(100.0, adjusted))))
    base_verdict = _oracle_verdict_from_score(final_score, asset)
    verdict = unified_verdict_with_conflict(
        final_score, asset, conflict_meta, base_verdict=base_verdict
    )
    conflict_penalty = float((breakdown.get("conflicts") or {}).get("confidence_penalty") or 0.0)
    if conflict_meta.get("veto"):
        conflict_penalty += 15.0
    elif conflict_meta.get("abstain"):
        conflict_penalty += 8.0
    ml_conf = float(ml_meta.get("confidence_percent") or 0) if ml_meta.get("available") else None

    return {
        "asset": asset,
        "opportunity_score": final_score,
        "base_score": int(round(base_score)),
        "verdict": verdict,
        "market_regime": breakdown.get("market_regime", "neutral"),
        "dimension_weights": breakdown.get("dimension_weights", {}),
        "modal_breakdown": breakdown,
        "dimension_conflict": conflict_meta,
        "hub_adjustment": round(hub_delta, 2),
        "hub_reasons": hub_reasons,
        "hub_risks": hub_risks,
        "ml": ml_meta,
        "confidence": _confidence_from_score(
            final_score,
            change,
            quote_volume,
            conflict_penalty=conflict_penalty,
            ml_confidence=ml_conf,
        ),
        "institutional_context": ctx,
        "engine": "unified_multimodal_v1",
    }
