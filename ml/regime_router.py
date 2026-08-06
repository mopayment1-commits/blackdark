"""
BLACKDARK — Regime-conditional inference router (Differentiator D5).

Prefers per-regime model.joblib when present; else soft confidence multipliers.
"""

from __future__ import annotations

from typing import Any

from ml.regime_models import (
    REGIME_CONF_MULT,
    predict_with_regime_artifact,
    regime_has_artifact,
    regime_model_registry,
)


async def predict_direction_regime_aware(
    asset: str,
    *,
    price: float | None = None,
    change_24h: float = 0.0,
    institutional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ml.feature_store import build_feature_vector
    from ml.inference import predict_direction
    from weight_aggregator import detect_market_regime

    ctx = institutional_context
    if ctx is None:
        try:
            from whale_tracker import get_latest_institutional_context

            ctx = await get_latest_institutional_context()
        except Exception:
            ctx = {}

    regime = detect_market_regime(ctx or {}, change_24h=change_24h)
    mult = float(REGIME_CONF_MULT.get(regime, 1.0))
    registry = regime_model_registry()

    artifact_pred: dict[str, Any] | None = None
    if regime_has_artifact(regime):
        try:
            features = await build_feature_vector(asset, price_at=price)
            artifact_pred = predict_with_regime_artifact(regime, features or {})
        except Exception:
            artifact_pred = None

    if artifact_pred and artifact_pred.get("available"):
        out = dict(artifact_pred)
        out["market_regime"] = regime
        out["regime_router"] = {
            "status": registry.get("status"),
            "evidence_status": registry.get("evidence_status"),
            "per_regime_models": bool(registry.get("per_regime_models")),
            "confidence_multiplier": mult,
            "active_regime": regime,
            "inference_path": "per_regime_artifact",
            "note": "Dedicated regime model artifact used for inference.",
            "registry": {
                "artifacts_ready": registry.get("artifacts_ready"),
                "artifacts_expected": registry.get("artifacts_expected"),
                "regimes": registry.get("regimes"),
            },
        }
        if regime == "panic":
            out["regime_caution"] = True
        return out

    base = await predict_direction(asset, price=price, regime_aware=False)
    out = dict(base)
    out["market_regime"] = regime
    out["regime_router"] = {
        "status": registry.get("status"),
        "evidence_status": registry.get("evidence_status"),
        "per_regime_models": bool(registry.get("per_regime_models")),
        "confidence_multiplier": mult,
        "active_regime": regime,
        "inference_path": "confidence_multiplier_fallback",
        "note": registry.get("note"),
        "registry": {
            "artifacts_ready": registry.get("artifacts_ready"),
            "artifacts_expected": registry.get("artifacts_expected"),
            "regimes": registry.get("regimes"),
        },
    }

    cal = out.get("confidence_calibrated")
    if isinstance(cal, dict) and cal.get("confidence_percent") is not None:
        adjusted = max(0.0, min(100.0, float(cal["confidence_percent"]) * mult))
        out["confidence_calibrated"] = {
            **cal,
            "confidence_percent": round(adjusted, 2),
            "regime_adjusted": True,
        }
    elif out.get("confidence_raw_percent") is not None:
        out["confidence_raw_percent"] = round(
            max(0.0, min(100.0, float(out["confidence_raw_percent"]) * mult)), 2
        )

    if regime == "panic" and out.get("available"):
        out["regime_caution"] = True
    return out
