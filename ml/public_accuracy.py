"""

BLACKDARK — Public Oracle Accuracy + AI model transparency API.



Live-only hit rate is the primary metric; synthetic seeded data is labeled separately.

"""



from __future__ import annotations



from typing import Any



import config

from oracle_integrity import is_synthetic_prediction





async def build_public_accuracy_payload(*, recent_limit: int = 20) -> dict[str, Any]:

    from database import fetch_labeled_oracle_predictions, fetch_oracle_audit_stats

    from ml.experience_log import public_experience_block

    from ml.train_baseline import model_status

    from ml.training_utils import LEAKAGE_GUARD_NOTE



    stats = await fetch_oracle_audit_stats(limit=recent_limit, include_synthetic=False)

    ml_status = await model_status()

    labeled = await fetch_labeled_oracle_predictions(limit=1000, include_synthetic=False)

    experience = public_experience_block()



    recent = stats.get("recent") or []

    public_recent = []

    correct = 0

    resolved_rows = 0

    for row in recent:

        if not row.get("resolved"):

            continue

        if is_synthetic_prediction(row):

            continue

        resolved_rows += 1

        label = str(row.get("label") or row.get("outcome") or "")

        if label == "correct":

            correct += 1

        pred_id = row.get("id")
        public_recent.append(
            {
                "prediction_id": pred_id,
                "timestamp": row.get("timestamp"),
                "asset": row.get("asset"),
                "verdict": row.get("verdict"),
                "price_at_prediction": row.get("price_at_prediction"),
                "price_after_24h": row.get("price_after_24h"),
                "label": label,
                "direction_label": row.get("direction_label"),
                "accuracy_score": row.get("accuracy_score"),
                "opportunity_score": row.get("opportunity_score"),
                "synthetic": False,
                "source": row.get("source") or "oracle",
                "chain_ref": f"oracle_pred:{pred_id}" if pred_id is not None else None,
            }
        )



    hit_rate = round(correct / resolved_rows * 100, 2) if resolved_rows else 0.0



    track_record_block: dict[str, Any] = {}

    try:

        from oracle_track_record import public_track_record



        track_record_block = public_track_record()

    except Exception:

        track_record_block = {"auto_accumulation": False}



    from ml.drift_monitor import load_feature_envelope



    envelope = load_feature_envelope()

    production_engine = "ml_model" if ml_status.get("latest_model_loaded") else "rules_engine"

    synthetic_block = stats.get("synthetic") or {}



    return {

        "product": "BLACKDARK Oracle AI",

        "mission": "Proprietary crypto intelligence — every live prediction tracked publicly",

        "transparency": {

            "production_engine": production_engine,

            "engine_note": (

                "Live verdicts use deterministic rules engine until ML model is trained and OOD-validated."

                if production_engine == "rules_engine"

                else "ML model active with OOD gate and temporal hold-out validation."

            ),

            "confidence_type": "calibrated" if envelope else "heuristic_formula",

            "drift_monitoring": envelope is not None,

            "ood_protection": True,

            "min_training_samples": ml_status.get("min_samples_required"),

            "validation_method": "temporal_holdout",

            "synthetic_data_excluded": True,

            "integrity_note": LEAKAGE_GUARD_NOTE,

        },

        "oracle": {

            "total_predictions": stats.get("live", {}).get("total_predictions", stats.get("total_predictions", 0)),

            "resolved_predictions": stats.get("live", {}).get(

                "resolved_predictions", stats.get("resolved_predictions", 0)

            ),

            "pending_predictions": stats.get("live", {}).get(

                "pending_predictions", stats.get("pending_predictions", 0)

            ),

            "average_accuracy_percent": stats.get("live", {}).get(

                "average_accuracy_percent", stats.get("average_accuracy_percent", 0)

            ),

            "recent_hit_rate_percent": hit_rate,

            "recent_predictions": public_recent[:recent_limit],

            "metrics_scope": "live_only",

        },

        "synthetic_demo_data": {

            "excluded_from_hit_rate": True,

            "total_predictions": synthetic_block.get("total_predictions", 0),

            "resolved_predictions": synthetic_block.get("resolved_predictions", 0),

            "average_accuracy_percent": synthetic_block.get("average_accuracy_percent", 0),

            "note": synthetic_block.get(

                "note",

                "Demo backfill for chain integrity — not counted as live performance.",

            ),

        },

        "model": {

            "production_engine": production_engine,

            "labeled_samples": len(labeled),

            "min_samples_required": ml_status.get("min_samples_required"),

            "latest_model_loaded": ml_status.get("latest_model_loaded"),

            "latest_model_version": ml_status.get("latest_model_version"),

            "auto_train_enabled": ml_status.get("auto_train_enabled"),

            "latest_run": ml_status.get("latest_run"),

            "drift_envelope_ready": envelope is not None,

            "synthetic_excluded": True,

            "validation_method": "temporal_holdout",

        },

        "learning_experience": experience,

        "immutable_track_record": track_record_block,

        "data_moat": {

            "exchanges": len(config.INGESTION_READY_EXCHANGES),

            "assets": len(config.UNIVERSE_ASSETS),

        },

        "proof_chain": _proof_chain_block(),

        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",

    }


def _proof_chain_block() -> dict[str, Any]:
    try:
        from oracle_audit_chain import chain_summary, verify_chain

        return {
            "summary": chain_summary(limit=5),
            "verify": verify_chain(),
            "public_page": "/oracle-accuracy",
        }
    except Exception as exc:
        return {"error": str(exc)}

