"""
BLACKDARK — Regime-conditional inference router (Differentiator D5 launch slice).

Uses live market regime to adjust ML confidence / direction bias until
separate per-regime model artifacts are trained.
"""

from __future__ import annotations

from typing import Any

# Soft multipliers on calibrated confidence by regime
_REGIME_CONF_MULT = {
    "risk_on": 1.05,
    "neutral": 1.0,
    "risk_off": 0.92,
    "panic": 0.78,
}


async def predict_direction_regime_aware(
    asset: str,
    *,
    price: float | None = None,
    change_24h: float = 0.0,
    institutional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ml.inference import predict_direction
    from weight_aggregator import detect_market_regime

    base = await predict_direction(asset, price=price, regime_aware=False)
    ctx = institutional_context
    if ctx is None:
        try:
            from whale_tracker import get_latest_institutional_context

            ctx = await get_latest_institutional_context()
        except Exception:
            ctx = {}

    regime = detect_market_regime(ctx or {}, change_24h=change_24h)
    mult = float(_REGIME_CONF_MULT.get(regime, 1.0))
    out = dict(base)
    out["market_regime"] = regime
    out["regime_router"] = {
        "status": "weights_and_confidence_live",
        "per_regime_models": False,
        "confidence_multiplier": mult,
        "note": "Separate regime model artifacts pending; confidence gated by regime today.",
    }

    cal = out.get("confidence_calibrated")
    if isinstance(cal, dict) and cal.get("confidence_percent") is not None:
        adjusted = max(0.0, min(100.0, float(cal["confidence_percent"]) * mult))
        out["confidence_calibrated"] = {**cal, "confidence_percent": round(adjusted, 2), "regime_adjusted": True}
    elif out.get("confidence_raw_percent") is not None:
        out["confidence_raw_percent"] = round(
            max(0.0, min(100.0, float(out["confidence_raw_percent"]) * mult)), 2
        )

    if regime == "panic" and out.get("available"):
        # Fail-soft: force lower trust presentation
        out["regime_caution"] = True
    return out
