"""
BLACKDARK — Public Oracle Accuracy + AI model transparency API.
"""

from __future__ import annotations

from typing import Any

import config


async def build_public_accuracy_payload(*, recent_limit: int = 20) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions, fetch_oracle_audit_stats
    from ml.experience_log import public_experience_block
    from ml.train_baseline import model_status

    stats = await fetch_oracle_audit_stats(limit=recent_limit)
    ml_status = await model_status()
    labeled = await fetch_labeled_oracle_predictions(limit=1000)
    experience = public_experience_block()

    recent = stats.get("recent") or []
    public_recent = []
    correct = 0
    resolved_rows = 0
    for row in recent:
        if not row.get("resolved"):
            continue
        resolved_rows += 1
        label = str(row.get("label") or row.get("outcome") or "")
        if label == "correct":
            correct += 1
        public_recent.append(
            {
                "timestamp": row.get("timestamp"),
                "asset": row.get("asset"),
                "verdict": row.get("verdict"),
                "price_at_prediction": row.get("price_at_prediction"),
                "price_after_24h": row.get("price_after_24h"),
                "label": label,
                "direction_label": row.get("direction_label"),
                "accuracy_score": row.get("accuracy_score"),
                "opportunity_score": row.get("opportunity_score"),
            }
        )

    hit_rate = round(correct / resolved_rows * 100, 2) if resolved_rows else 0.0

    return {
        "product": "BLACKDARK Oracle AI",
        "mission": "Proprietary crypto intelligence model — every prediction tracked publicly",
        "oracle": {
            "total_predictions": stats.get("total_predictions", 0),
            "resolved_predictions": stats.get("resolved_predictions", 0),
            "pending_predictions": stats.get("pending_predictions", 0),
            "average_accuracy_percent": stats.get("average_accuracy_percent", 0),
            "recent_hit_rate_percent": hit_rate,
            "recent_predictions": public_recent[:recent_limit],
        },
        "model": {
            "labeled_samples": len(labeled),
            "min_samples_required": ml_status.get("min_samples_required"),
            "latest_model_loaded": ml_status.get("latest_model_loaded"),
            "latest_model_version": ml_status.get("latest_model_version"),
            "auto_train_enabled": ml_status.get("auto_train_enabled"),
            "latest_run": ml_status.get("latest_run"),
        },
        "learning_experience": experience,
        "data_moat": {
            "exchanges": len(config.INGESTION_READY_EXCHANGES),
            "assets": len(config.UNIVERSE_ASSETS),
        },
    }
