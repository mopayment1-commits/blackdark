"""
BLACKDARK — Baseline model inference (Phase 1).

Uses trained oracle_direction model when available; falls back to rules engine.
"""

from __future__ import annotations

import logging
from typing import Any

from ml.feature_store import build_feature_vector
from ml.train_baseline import FEATURE_COLUMNS, load_latest_model

logger = logging.getLogger("BLACKDARK.MLInference")


async def predict_direction(asset: str, *, price: float | None = None) -> dict[str, Any]:
    bundle = load_latest_model()
    features = await build_feature_vector(asset, price_at=price)
    if not bundle:
        return {
            "available": False,
            "reason": "model_not_trained",
            "features": features,
        }

    model = bundle["model"]
    row = {col: float(features.get(col, 0.0)) for col in FEATURE_COLUMNS}
    row["opportunity_score"] = float(features.get("opportunity_score") or 0)
    row["confidence"] = float(features.get("confidence") or 0)

    import pandas as pd

    frame = pd.DataFrame([row])
    pred = str(model.predict(frame[FEATURE_COLUMNS])[0])
    proba_map: dict[str, float] = {}
    if hasattr(model, "predict_proba"):
        classes = list(model.classes_)
        probs = model.predict_proba(frame[FEATURE_COLUMNS])[0]
        proba_map = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}

    return {
        "available": True,
        "model_version": bundle.get("version"),
        "direction": pred,
        "probabilities": proba_map,
        "features": features,
    }
