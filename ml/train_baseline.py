"""

BLACKDARK — Baseline ML model training (Phase 1 entry point).



Trains a direction classifier from labeled live oracle predictions + feature vectors.

Uses chronological hold-out (no random shuffle) to prevent temporal leakage.

"""



from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import config
from ml.training_utils import (
    FEATURE_COLUMNS,
    LEAKAGE_GUARD_NOTE,
    temporal_train_test_split,
)

logger = logging.getLogger("BLACKDARK.MLTrain")





def _utcnow_iso() -> str:

    return datetime.now(UTC).isoformat()





def _parse_features(raw: Any) -> dict[str, float]:

    if not raw:

        return {}

    if isinstance(raw, dict):

        payload = raw

    else:

        try:

            payload = json.loads(str(raw))

        except json.JSONDecodeError:

            return {}

    return {k: float(v) for k, v in payload.items() if isinstance(v, (int, float))}





def _build_training_frame(rows: list[dict[str, Any]]):

    import pandas as pd



    records: list[dict[str, Any]] = []

    for row in rows:

        direction = str(row.get("direction_label") or "").lower()

        # Prefer directional labels; keep flat only when class balance needs it.
        if direction not in {"up", "down", "flat"}:

            continue

        feats = _parse_features(row.get("features_json"))

        record: dict[str, Any] = {

            "direction_label": direction,

            "timestamp": str(row.get("timestamp") or ""),

        }

        for col in FEATURE_COLUMNS:

            record[col] = float(feats.get(col, 0.0))

        records.append(record)



    if not records:

        return None

    return pd.DataFrame(records)





async def train_oracle_direction_model(*, min_samples: int | None = None) -> dict[str, Any]:

    from database import fetch_labeled_oracle_predictions, fetch_latest_ml_model_run, insert_ml_model_run
    from ml.experience_log import append_experience



    threshold = min_samples or config.ML_MIN_TRAIN_SAMPLES

    rows = await fetch_labeled_oracle_predictions(

        limit=max(threshold * 4, 500),

        include_synthetic=False,

    )

    frame = _build_training_frame(rows)

    if frame is None or len(frame) < threshold:

        return {

            "trained": False,

            "reason": "insufficient_labeled_samples",

            "samples": 0 if frame is None else len(frame),

            "minimum_required": threshold,

            "integrity_note": LEAKAGE_GUARD_NOTE,

        }



    try:

        import joblib
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.metrics import accuracy_score

    except ImportError:

        return {

            "trained": False,

            "reason": "scikit_learn_missing",

            "hint": "pip install scikit-learn",

        }



    split = temporal_train_test_split(frame)

    if split is None:

        return {

            "trained": False,

            "reason": "insufficient_samples_for_temporal_split",

            "samples": len(frame),

            "minimum_required": threshold,

        }



    x_train, x_test, y_train, y_test = split

    if y_train.nunique() < 2 or y_test.nunique() < 1:

        return {"trained": False, "reason": "single_class_labels", "samples": len(frame)}



    model = GradientBoostingClassifier(random_state=42, learning_rate=0.1)

    model.fit(x_train, y_train)

    preds = model.predict(x_test)

    accuracy = float(accuracy_score(y_test, preds))



    incumbent_metrics: dict[str, Any] | None = None

    latest_run = await fetch_latest_ml_model_run("oracle_direction")

    if latest_run and latest_run.get("metrics_json"):

        try:

            incumbent_metrics = json.loads(str(latest_run["metrics_json"]))

        except json.JSONDecodeError:

            incumbent_metrics = None



    from ml.drift_monitor import (
        build_confidence_calibration,
        build_feature_envelope,
        save_feature_envelope,
        validate_model_deployment,
    )



    validation = validate_model_deployment(

        {"accuracy": accuracy},

        incumbent_metrics=incumbent_metrics,

    )

    if not validation.get("approved"):

        append_experience(

            "training_rejected",

            {"metrics": {"accuracy": accuracy}, "validation": validation},

            notes="model_validation_gate",

        )

        return {

            "trained": True,

            "deployed": False,

            "reason": validation.get("reason"),

            "metrics": {"accuracy": accuracy},

            "validation": validation,

            "validation_method": "temporal_holdout",

        }



    envelope = build_feature_envelope(rows)

    save_feature_envelope(envelope)

    build_confidence_calibration(rows)



    config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    version = datetime.now(UTC).strftime("v%Y%m%d_%H%M")

    model_path = config.ML_MODELS_DIR / f"oracle_direction_{version}.joblib"

    joblib.dump(

        {

            "model": model,

            "feature_columns": list(FEATURE_COLUMNS),

            "version": version,

            "trained_at": _utcnow_iso(),

            "validation_method": "temporal_holdout",

        },

        model_path,

    )



    latest_path = config.ML_MODELS_DIR / "oracle_direction_latest.joblib"

    joblib.dump(

        {

            "model": model,

            "feature_columns": list(FEATURE_COLUMNS),

            "version": version,

            "trained_at": _utcnow_iso(),

            "validation_method": "temporal_holdout",

        },

        latest_path,

    )



    metrics = {

        "accuracy": round(accuracy, 4),

        "samples_total": len(frame),

        "samples_train": len(x_train),

        "samples_test": len(x_test),

        "classes": sorted(set(y_train.unique().tolist()) | set(y_test.unique().tolist())),

        "validation_method": "temporal_holdout",

        "synthetic_excluded": True,

        "leakage_guards": [

            "no_opportunity_score",

            "no_confidence",

            "no_historical_seed",

            "chronological_split",

        ],

    }

    await insert_ml_model_run(

        model_name="oracle_direction",

        model_version=version,

        samples_used=len(frame),

        metrics_json=json.dumps(metrics),

        model_path=str(model_path),

        status="completed",

    )

    result = {

        "trained": True,

        "deployed": True,

        "model_name": "oracle_direction",

        "model_version": version,

        "model_path": str(model_path),

        "metrics": metrics,

        "validation": validation,

        "feature_envelope_samples": envelope.get("sample_count"),

        "integrity_note": LEAKAGE_GUARD_NOTE,

    }

    append_experience("training_run", result, notes="baseline_direction_model")

    logger.info(

        "Baseline model trained | version=%s accuracy=%.3f samples=%d temporal_holdout",

        version,

        accuracy,

        len(frame),

    )

    return result





def load_latest_model() -> dict[str, Any] | None:

    path = config.ML_MODELS_DIR / "oracle_direction_latest.joblib"

    if not path.exists():

        return None

    try:

        import joblib



        return joblib.load(path)

    except Exception:

        logger.exception("Unable to load latest ML model")

        return None





async def model_status() -> dict[str, Any]:

    from database import fetch_labeled_oracle_predictions, fetch_latest_ml_model_run



    labeled = await fetch_labeled_oracle_predictions(limit=10000, include_synthetic=False)

    latest_run = await fetch_latest_ml_model_run("oracle_direction")

    artifact = load_latest_model()

    return {

        "labeled_samples": len(labeled),

        "min_samples_required": config.ML_MIN_TRAIN_SAMPLES,

        "latest_model_loaded": artifact is not None,

        "latest_model_version": (artifact or {}).get("version"),

        "latest_run": latest_run,

        "auto_train_enabled": config.ML_AUTO_TRAIN,

        "synthetic_excluded": True,

        "validation_method": "temporal_holdout",

        "timestamp": _utcnow_iso(),

    }

