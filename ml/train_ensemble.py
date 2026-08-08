"""
BLACKDARK — Ensemble trainer (Phase 1+).

Trains multiple classifiers with chronological hold-out validation.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import config
from ml.train_baseline import _build_training_frame, _utcnow_iso
from ml.training_utils import FEATURE_COLUMNS, LEAKAGE_GUARD_NOTE, temporal_train_test_split

logger = logging.getLogger("BLACKDARK.MLEnsemble")


async def train_direction_ensemble(*, min_samples: int | None = None) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions, insert_ml_model_run
    from ml.experience_log import append_experience

    threshold = min_samples or config.ML_MIN_TRAIN_SAMPLES
    rows = await fetch_labeled_oracle_predictions(
        limit=max(threshold * 4, 500),
        include_synthetic=False,
    )
    frame = _build_training_frame(rows)
    if frame is None or len(frame) < threshold:
        result = {
            "trained": False,
            "reason": "insufficient_labeled_samples",
            "samples": 0 if frame is None else len(frame),
            "minimum_required": threshold,
            "integrity_note": LEAKAGE_GUARD_NOTE,
        }
        append_experience("ensemble_trained", result, notes="ensemble_skipped")
        return result

    try:
        import joblib
        from sklearn.ensemble import (
            GradientBoostingClassifier,
            RandomForestClassifier,
            VotingClassifier,
        )
        from sklearn.metrics import accuracy_score
    except ImportError:
        return {"trained": False, "reason": "scikit_learn_missing"}

    split = temporal_train_test_split(frame)
    if split is None:
        return {
            "trained": False,
            "reason": "insufficient_samples_for_temporal_split",
            "samples": len(frame),
        }

    x_train, x_test, y_train, y_test = split
    if y_train.nunique() < 2:
        return {"trained": False, "reason": "single_class_labels", "samples": len(frame)}

    candidates = {
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=120, random_state=42, max_depth=8
        ),
    }
    solo_metrics: dict[str, float] = {}
    estimators: list[tuple[str, Any]] = []
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        preds = model.predict(x_test)
        solo_metrics[name] = float(accuracy_score(y_test, preds))
        estimators.append((name, model))

    ensemble = VotingClassifier(estimators=estimators, voting="soft")
    ensemble.fit(x_train, y_train)
    ensemble_preds = ensemble.predict(x_test)
    ensemble_accuracy = float(accuracy_score(y_test, ensemble_preds))

    best_solo = max(solo_metrics.values()) if solo_metrics else 0.0
    use_ensemble = ensemble_accuracy >= best_solo
    final_model = ensemble if use_ensemble else candidates[
        max(solo_metrics, key=solo_metrics.get)  # type: ignore[arg-type]
    ]
    final_accuracy = ensemble_accuracy if use_ensemble else best_solo
    final_kind = "ensemble" if use_ensemble else max(solo_metrics, key=solo_metrics.get)

    metrics = {
        "accuracy": round(final_accuracy, 4),
        "ensemble_accuracy": round(ensemble_accuracy, 4),
        "solo_metrics": {k: round(v, 4) for k, v in solo_metrics.items()},
        "selected": final_kind,
        "samples_total": len(frame),
        "samples_train": len(x_train),
        "samples_test": len(x_test),
        "classes": sorted(set(y_train.unique().tolist()) | set(y_test.unique().tolist())),
        "validation_method": "temporal_holdout",
        "synthetic_excluded": True,
    }

    from ml.drift_monitor import validate_model_deployment
    from ml.train_baseline import load_latest_model

    incumbent = load_latest_model() or {}
    incumbent_metrics = None
    if incumbent:
        incumbent_metrics = {"accuracy": float((incumbent.get("metrics") or {}).get("accuracy") or 0)}
        # Bundles may store accuracy at top-level metrics from prior runs.
        if not incumbent_metrics["accuracy"]:
            try:
                incumbent_metrics = {"accuracy": float(incumbent.get("ensemble_accuracy") or 0)}
            except (TypeError, ValueError):
                incumbent_metrics = None
    validation = validate_model_deployment(metrics, incumbent_metrics=incumbent_metrics)
    if not validation.get("approved"):
        result = {
            "trained": False,
            "reason": validation.get("reason"),
            "validation": validation,
            "metrics": metrics,
            "integrity_note": LEAKAGE_GUARD_NOTE,
        }
        append_experience("ensemble_rejected", result, notes="deployment_gate")
        logger.warning("Ensemble rejected by deployment gate | %s", validation)
        return result

    config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    version = datetime.now(UTC).strftime("ens%Y%m%d_%H%M")
    bundle = {
        "model": final_model,
        "feature_columns": list(FEATURE_COLUMNS),
        "version": version,
        "model_kind": final_kind,
        "trained_at": _utcnow_iso(),
        "solo_metrics": solo_metrics,
        "ensemble_accuracy": ensemble_accuracy,
        "metrics": metrics,
        "validation_method": "temporal_holdout",
    }
    model_path = config.ML_MODELS_DIR / f"oracle_direction_{version}.joblib"
    latest_path = config.ML_MODELS_DIR / "oracle_direction_latest.joblib"
    joblib.dump(bundle, model_path)
    joblib.dump(bundle, latest_path)

    await insert_ml_model_run(
        model_name="oracle_direction_ensemble",
        model_version=version,
        samples_used=len(frame),
        metrics_json=json.dumps(metrics),
        model_path=str(model_path),
        status="completed",
    )
    result = {
        "trained": True,
        "model_name": "oracle_direction_ensemble",
        "model_version": version,
        "model_path": str(model_path),
        "metrics": metrics,
        "validation": validation,
        "integrity_note": LEAKAGE_GUARD_NOTE,
    }
    append_experience("ensemble_trained", result, notes=f"selected={final_kind}")
    logger.info(
        "Ensemble trained | version=%s selected=%s accuracy=%.3f temporal_holdout",
        version,
        final_kind,
        final_accuracy,
    )
    return result
