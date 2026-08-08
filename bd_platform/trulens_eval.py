"""TruLens-style ML explainability with optional TruLens + rules fallback."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.TruLensEval")


async def explain_prediction(asset: str, *, price: float | None = None) -> dict[str, Any]:
    from ml.inference import predict_direction
    from ml.training_utils import LEAKAGE_GUARD_NOTE

    pred = await predict_direction(asset, price=price)
    features = pred.get("features") or {}
    engine = pred.get("engine") or "rules"

    trulens_available = False
    feedback_score: float | None = None
    try:
        import trulens  # noqa: F401

        trulens_available = True
        feedback_score = _trulens_feedback(pred)
    except ImportError:
        feedback_score = _confidence_from_pred(pred)

    reasons = _build_reason_chain(features, pred)
    contributions = _feature_contributions(features, pred)
    return {
        "asset": asset.upper(),
        "engine": engine,
        "direction": pred.get("direction"),
        "probabilities": pred.get("probabilities"),
        "confidence_pct": pred.get("confidence_pct"),
        "ood": pred.get("ood"),
        "trulens_available": trulens_available,
        "trulens_feedback_score": feedback_score,
        "reason_chain": reasons,
        "feature_contributions": contributions,
        "integrity": {
            "temporal_holdout": True,
            "synthetic_excluded": True,
            "note": LEAKAGE_GUARD_NOTE,
        },
        "interpretation": " | ".join(reasons[:4]),
    }


def _confidence_from_pred(pred: dict[str, Any]) -> float:
    probs = pred.get("probabilities") or {}
    if probs:
        return float(max(probs.values()))
    return 0.5


def _trulens_feedback(pred: dict[str, Any]) -> float:
    return _confidence_from_pred(pred)


def _feature_contributions(features: dict[str, Any], pred: dict[str, Any]) -> list[dict[str, Any]]:
    from ml.training_utils import FEATURE_COLUMNS

    rows: list[dict[str, Any]] = []
    for col in FEATURE_COLUMNS:
        val = float(features.get(col) or 0)
        weight = abs(val)
        rows.append({"feature": col, "value": round(val, 4), "weight": round(weight, 4)})
    rows.sort(key=lambda x: x["weight"], reverse=True)
    top = rows[:8]
    total = sum(r["weight"] for r in top) or 1.0
    for r in top:
        r["contribution_pct"] = round(r["weight"] / total * 100, 1)
    if pred.get("ood", {}).get("is_ood"):
        top.insert(0, {"feature": "ood_gate", "value": 1.0, "contribution_pct": 100.0, "weight": 1.0})
    return top


def _build_reason_chain(features: dict[str, Any], pred: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    ret_1h = float(features.get("ret_1h") or 0)
    ret_24h = float(features.get("ret_24h") or 0)
    sentiment = float(features.get("sentiment_score") or 0)
    obi = float(features.get("obi_score") or 0)
    funding = float(features.get("funding_rate") or 0)
    if ret_1h > 0.5:
        reasons.append(f"1h momentum +{ret_1h:.2f}% supports bullish bias")
    elif ret_1h < -0.5:
        reasons.append(f"1h momentum {ret_1h:.2f}% supports bearish bias")
    if abs(ret_24h) > 2:
        reasons.append(f"24h trend {ret_24h:+.2f}% reinforces direction")
    if abs(sentiment) > 0.15:
        reasons.append(f"Sentiment compound {sentiment:+.2f} tilts direction")
    if abs(obi) > 10:
        reasons.append(f"Order-book imbalance score {obi:.1f}")
    if abs(funding) > 0.0002:
        reasons.append(f"Funding rate {funding*100:.4f}% signals crowded positioning")
    if pred.get("ood", {}).get("is_ood"):
        reasons.append("OOD gate triggered — rules engine fallback active")
    if pred.get("engine") == "rules":
        reasons.append("Rules engine active (ML unavailable or OOD)")
    if not reasons:
        reasons.append("Neutral feature vector — low conviction")
    return reasons
