"""
BLACKDARK — Unified Oracle Scoring (single decision path).

Dashboard Oracle and arbitrage scoring share the same multi-modal pipeline:
base score → regime-weighted dimensions → conflict resolution → optional ML.
"""

from __future__ import annotations

import asyncio

import logging
from typing import Any

from dimension_conflict_guard import apply_dimension_conflict_guard
from oracle_data_hub import hub_score_adjustment
from sentiment_engine import is_extreme_negative_sentiment, sentiment_panic_penalty_for_asset
from sentiment_manipulation_guard import (
    greed_pump_penalty_for_asset as sentiment_greed_penalty_for_asset,
    is_extreme_positive_sentiment,
)
from weight_aggregator import apply_modal_adjustments_with_regime, build_full_market_context

logger = logging.getLogger("BLACKDARK.OracleUnified")

ENGINE_ID = "unified_multimodal_v1"


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
        return to_public_verdict("I_DONT_KNOW")
    if conflict_meta.get("abstain"):
        return to_public_verdict("I_DONT_KNOW")
    if base_verdict:
        return to_public_verdict(base_verdict)
    return _oracle_verdict_from_score(score, asset)


def arbitrage_internal_verdict(
    score: float,
    confidence: float,
    conflict_meta: dict[str, Any] | None = None,
) -> str:
    """Internal execution verdict used by the arbitrage oracle path."""
    from dimension_conflict_guard import arbitrage_verdict_with_conflict

    meta = conflict_meta or {}
    return arbitrage_verdict_with_conflict(score, confidence, meta)


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
        adjusted = round(adjusted * 0.7 + ml_confidence * 0.3)
    return max(20, min(98, adjusted))


async def _optional_ml_nudge(asset: str, price: float, score: float) -> dict[str, Any]:
    try:
        from ml.inference import predict_direction

        ml = await predict_direction(asset, price=price)
    except Exception:
        logger.debug("ML inference skipped | asset=%s", str(asset).replace("\r", " ").replace("\n", " "), exc_info=True)
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


def apply_unified_adjustments(
    base_score: float,
    asset: str,
    institutional_context: dict[str, Any] | None = None,
    *,
    change_24h: float = 0.0,
    quote_volume: float = 0.0,
    apply_hub: bool = True,
) -> tuple[float, dict[str, Any]]:
    """
    Shared multimodal post-processor (sync) used by arb + dashboard.

    Applies sentiment panic/greed, regime-weighted modal adjustments, and hub delta.
    Does NOT multiply by macro again (macro is already inside modal contribution).
    """
    asset = asset.upper()
    ctx = institutional_context or {}
    score = float(base_score)

    compound = float((ctx.get("sentiment_compound_index") or {}).get(asset, 0.0))
    if is_extreme_negative_sentiment(compound):
        score -= sentiment_panic_penalty_for_asset(asset, ctx)
    elif is_extreme_positive_sentiment(compound):
        score -= sentiment_greed_penalty_for_asset(asset, ctx)

    adjusted, breakdown = apply_modal_adjustments_with_regime(
        score,
        asset,
        ctx,
        change_24h=change_24h,
        quote_volume=quote_volume,
    )

    hub_delta = 0.0
    hub_reasons: list[str] = []
    hub_risks: list[str] = []
    if apply_hub:
        hub = ctx.get("oracle_data_hub") or {}
        if hub.get("enabled"):
            hub_delta, hub_reasons, hub_risks = hub_score_adjustment(asset, hub)
            adjusted += hub_delta

    breakdown = dict(breakdown)
    breakdown["hub_adjustment"] = round(hub_delta, 2)
    breakdown["hub_reasons"] = hub_reasons
    breakdown["hub_risks"] = hub_risks
    breakdown["engine"] = ENGINE_ID
    return max(0.0, min(100.0, adjusted)), breakdown


async def _rl_policy_adjustment(change_24h: float, breakdown: dict[str, Any]) -> dict[str, Any]:
    await asyncio.sleep(0)
    rl_meta: dict[str, Any] = {"available": False, "nudge": 0.0}
    try:
        from ml.rl_policy import predict_action

        feats = {
            "ret_24h": float(change_24h or 0.0) / 100.0,
            "volatility": abs(float(change_24h or 0.0)) / 100.0,
            "obi_score": float((breakdown.get("obi") or {}).get("score") or 0.0),
            "sentiment_score": float(
                (breakdown.get("sentiment") or {}).get("compound")
                or (breakdown.get("hub_adjustment") or 0.0)
            ),
        }
        action = predict_action(feats)
    except Exception:
        return rl_meta
    rl_meta = {"available": True, **action}
    act = str(action.get("action") or "hold")
    conf = float(action.get("confidence") or 0.0)
    if act == "long":
        rl_meta["nudge"] = min(3.0, 2.0 * conf)
    elif act == "short":
        rl_meta["nudge"] = -min(3.0, 2.0 * conf)
    else:
        rl_meta["nudge"] = 0.0
    return rl_meta


async def _timeframe_confluence_adjustment(
    asset: str,
    adjusted: float,
    conflict_meta: dict[str, Any],
) -> tuple[float, dict[str, Any], dict[str, Any]]:
    confluence: dict[str, Any] = {"aligned": None, "score_penalty": 0.0}
    try:
        from technical_analysis import compute_timeframe_confluence

        confluence = await compute_timeframe_confluence(asset)
        adjusted -= float(confluence.get("score_penalty") or 0.0)
        conflict_meta = _merge_timeframe_conflict(conflict_meta, confluence)
    except Exception:
        pass
    return adjusted, conflict_meta, confluence


def _merge_timeframe_conflict(
    conflict_meta: dict[str, Any],
    confluence: dict[str, Any],
) -> dict[str, Any]:
    penalty = float(confluence.get("score_penalty") or 0)
    if confluence.get("aligned") is False and penalty >= 8:
        return {
            **conflict_meta,
            "timeframe_disagreement": True,
            "abstain": True if not conflict_meta.get("veto") else conflict_meta.get("abstain"),
        }
    return conflict_meta


def _conflict_penalty(
    breakdown: dict[str, Any],
    conflict_meta: dict[str, Any],
    confluence: dict[str, Any],
) -> float:
    penalty = float((breakdown.get("conflicts") or {}).get("confidence_penalty") or 0.0)
    if conflict_meta.get("veto"):
        penalty += 15.0
    elif conflict_meta.get("abstain"):
        penalty += 8.0
    if confluence.get("aligned") is False:
        penalty += 5.0
    return penalty


async def finalize_unified_score(
    adjusted_score: float,
    asset: str,
    breakdown: dict[str, Any],
    *,
    price: float = 0.0,
    change_24h: float = 0.0,
    quote_volume: float = 0.0,
    include_ml: bool = True,
) -> dict[str, Any]:
    """Apply optional ML nudge + dimension conflict guard and emit verdicts."""
    asset = asset.upper()
    adjusted = float(adjusted_score)
    ml_meta: dict[str, Any] = {"available": False, "nudge": 0.0}
    if include_ml:
        ml_meta = await _optional_ml_nudge(asset, price, adjusted)
        adjusted += float(ml_meta.get("nudge") or 0.0)

    # Soft RL policy fusion (size/bias hint) — never overrides veto/conflict.
    rl_meta = await _rl_policy_adjustment(change_24h, breakdown)
    adjusted += float(rl_meta.get("nudge") or 0.0)

    adjusted, conflict_meta = apply_dimension_conflict_guard(adjusted, breakdown)

    # Core Canon §1.1 — multi-timeframe confluence before trusting score.
    adjusted, conflict_meta, confluence = await _timeframe_confluence_adjustment(
        asset,
        adjusted,
        conflict_meta,
    )

    final_score = round(max(0.0, min(100.0, adjusted)))
    public_verdict = unified_verdict_with_conflict(
        final_score,
        asset,
        conflict_meta,
        base_verdict=_oracle_verdict_from_score(final_score, asset),
    )
    ml_conf = float(ml_meta.get("confidence_percent") or 0) if ml_meta.get("available") else None
    confidence = _confidence_from_score(
        final_score,
        change_24h,
        quote_volume,
        conflict_penalty=_conflict_penalty(breakdown, conflict_meta, confluence),
        ml_confidence=ml_conf,
    )
    internal_verdict = arbitrage_internal_verdict(
        float(final_score),
        float(confidence),
        conflict_meta,
    )

    return {
        "asset": asset,
        "opportunity_score": final_score,
        "verdict": public_verdict,
        "internal_verdict": internal_verdict,
        "market_regime": breakdown.get("market_regime", "neutral"),
        "dimension_weights": breakdown.get("dimension_weights", {}),
        "modal_breakdown": breakdown,
        "dimension_conflict": conflict_meta,
        "timeframe_confluence": confluence,
        "hub_adjustment": breakdown.get("hub_adjustment", 0.0),
        "hub_reasons": breakdown.get("hub_reasons") or [],
        "hub_risks": breakdown.get("hub_risks") or [],
        "ml": ml_meta,
        "rl_policy": rl_meta,
        "confidence": confidence,
        "engine": ENGINE_ID,
    }


async def compute_unified_oracle(
    asset: str,
    price: float,
    quote_volume: float,
    change: float,
    *,
    include_ml: bool = True,
    institutional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Single scoring path for all Oracle consumers.

    Returns opportunity_score, verdict, regime, breakdown, conflicts, and context.
    """
    asset = asset.upper()
    base_score = float(compute_base_technical_score(quote_volume, change))
    ctx = institutional_context if institutional_context is not None else await build_full_market_context(asset)

    adjusted, breakdown = apply_unified_adjustments(
        base_score,
        asset,
        ctx,
        change_24h=change,
        quote_volume=quote_volume,
        apply_hub=True,
    )
    finalized = await finalize_unified_score(
        adjusted,
        asset,
        breakdown,
        price=price,
        change_24h=change,
        quote_volume=quote_volume,
        include_ml=include_ml,
    )
    finalized["base_score"] = round(base_score)
    finalized["institutional_context"] = ctx
    return finalized
