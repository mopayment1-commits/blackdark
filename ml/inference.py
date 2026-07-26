"""
BLACKDARK — Baseline model inference (Phase 1).

Uses trained oracle_direction model when available; OOD-gated with rules fallback.
"""

from __future__ import annotations

import logging
from typing import Any

from ml.drift_monitor import calibrate_confidence, ood_score
from ml.feature_store import build_feature_vector
from ml.train_baseline import load_latest_model
from ml.training_utils import FEATURE_COLUMNS

logger = logging.getLogger("BLACKDARK.MLInference")


async def predict_direction(asset: str, *, price: float | None = None) -> dict[str, Any]:
    bundle = load_latest_model()
    features = await build_feature_vector(asset, price_at=price)
    if not bundle:
        return {
            "available": False,
            "engine": "rules",
            "reason": "model_not_trained",
            "features": features,
        }

    ood = ood_score(features)
    if ood.get("is_ood"):
        return {
            "available": False,
            "engine": "rules",
            "reason": "ood_rejected",
            "ood": ood,
            "features": features,
            "fallback": "rules_engine",
        }

    model = bundle["model"]
    feature_cols = list(bundle.get("feature_columns") or FEATURE_COLUMNS)
    row = {col: float(features.get(col, 0.0)) for col in feature_cols}

    import pandas as pd

    frame = pd.DataFrame([row])
    pred = str(model.predict(frame[feature_cols])[0])
    proba_map: dict[str, float] = {}
    max_prob = 0.0
    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        probs = model.predict_proba(frame[feature_cols])[0]
        proba_map = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
        max_prob = max(proba_map.values()) if proba_map else 0.0

    raw_conf = float(max_prob * 100)
    calibration = calibrate_confidence(raw_conf)

    return {
        "available": True,
        "engine": "ml_model",
        "model_version": bundle.get("version"),
        "direction": pred,
        "probabilities": proba_map,
        "confidence_raw_percent": raw_conf,
        "confidence_calibrated": calibration,
        "ood": ood,
        "features": features,
    }
