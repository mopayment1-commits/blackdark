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


async def _institutional_context(institutional_context: dict[str, Any] | None) -> dict[str, Any]:
    if institutional_context is not None:
        return institutional_context
    try:
        from whale_tracker import get_latest_institutional_context

        return await get_latest_institutional_context()
    except Exception:
        return {}


async def _artifact_prediction(asset: str, regime: str, price: float | None) -> dict[str, Any] | None:
    if not regime_has_artifact(regime):
        return None
    try:
        from ml.feature_store import build_feature_vector

        features = await build_feature_vector(asset, price_at=price)
        return predict_with_regime_artifact(regime, features or {})
    except Exception:
        return None


def _router_payload(
    *,
    registry: dict[str, Any],
    mult: float,
    regime: str,
    inference_path: str,
    note: str | None,
) -> dict[str, Any]:
    return {
        "status": registry.get("status"),
        "evidence_status": registry.get("evidence_status"),
        "per_regime_models": bool(registry.get("per_regime_models")),
        "confidence_multiplier": mult,
        "active_regime": regime,
        "inference_path": inference_path,
        "note": note,
        "registry": {
            "artifacts_ready": registry.get("artifacts_ready"),
            "artifacts_expected": registry.get("artifacts_expected"),
            "regimes": registry.get("regimes"),
        },
    }


def _apply_regime_caution(out: dict[str, Any], regime: str, *, require_available: bool = True) -> None:
    if regime == "panic" and (out.get("available") or not require_available):
        out["regime_caution"] = True


def _adjust_confidence(out: dict[str, Any], mult: float) -> None:
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


async def predict_direction_regime_aware(
    asset: str,
    *,
    price: float | None = None,
    change_24h: float = 0.0,
    institutional_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ml.inference import predict_direction
    from weight_aggregator import detect_market_regime

    ctx = await _institutional_context(institutional_context)

    regime = detect_market_regime(ctx or {}, change_24h=change_24h)
    mult = float(REGIME_CONF_MULT.get(regime, 1.0))
    registry = regime_model_registry()

    artifact_pred = await _artifact_prediction(asset, regime, price)

    if artifact_pred and artifact_pred.get("available"):
        out = dict(artifact_pred)
        out["market_regime"] = regime
        out["regime_router"] = _router_payload(
            registry=registry,
            mult=mult,
            regime=regime,
            inference_path="per_regime_artifact",
            note="Dedicated regime model artifact used for inference.",
        )
        _apply_regime_caution(out, regime, require_available=False)
        return out

    base = await predict_direction(asset, price=price, regime_aware=False)
    out = dict(base)
    out["market_regime"] = regime
    out["regime_router"] = _router_payload(
        registry=registry,
        mult=mult,
        regime=regime,
        inference_path="confidence_multiplier_fallback",
        note=registry.get("note"),
    )
    _adjust_confidence(out, mult)
    _apply_regime_caution(out, regime)
    return out
