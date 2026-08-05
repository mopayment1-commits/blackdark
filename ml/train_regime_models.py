"""
BLACKDARK — Per-regime model training entry (D5).

Trains a real sklearn LogisticRegression per regime when enough labeled
live samples exist. Writes data/models/regime/<regime>/model.joblib.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml.regime_models import REGIMES, _REGIME_MODEL_ROOT, regime_model_registry
from ml.training_utils import FEATURE_COLUMNS, prepare_live_training_rows, temporal_train_test_split

logger = logging.getLogger("BLACKDARK.RegimeTrain")

MIN_SAMPLES_PER_REGIME = 40
STATUS_PATH = Path(__file__).resolve().parents[1] / "data" / "models" / "regime" / "training_status.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_feature_dict(row: dict[str, Any]) -> dict[str, float]:
    feats: dict[str, Any] = {}
    raw = row.get("features_json")
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                feats = parsed
        except Exception:
            feats = {}
    elif isinstance(raw, dict):
        feats = raw
    out: dict[str, float] = {}
    for col in FEATURE_COLUMNS:
        try:
            out[col] = float(feats.get(col) or 0.0)
        except (TypeError, ValueError):
            out[col] = 0.0
    # Fallbacks from prediction row when feature store sparse
    if out["price"] == 0.0 and row.get("price_at_prediction") is not None:
        try:
            out["price"] = float(row["price_at_prediction"])
        except (TypeError, ValueError):
            pass
    return out


def _direction_label(row: dict[str, Any]) -> str | None:
    label = str(row.get("direction_label") or "").strip().lower()
    if label in {"up", "down", "flat", "long", "short", "hold"}:
        return {"long": "up", "short": "down", "hold": "flat"}.get(label, label)
    # Derive from outcome label + verdict when direction missing
    outcome = str(row.get("label") or "").lower()
    verdict = str(row.get("verdict") or "").upper()
    if outcome == "correct" and verdict in {"BUY", "SELL"}:
        return "up" if verdict == "BUY" else "down"
    if outcome in {"incorrect", "partial"} and verdict in {"BUY", "SELL"}:
        return "down" if verdict == "BUY" else "up"
    return None


async def collect_regime_buckets() -> dict[str, list[dict[str, Any]]]:
    """Best-effort bucket labeled predictions by stored market_regime."""
    buckets = {r: [] for r in REGIMES}
    try:
        from database import fetch_labeled_oracle_predictions

        rows = await fetch_labeled_oracle_predictions(limit=2000, include_synthetic=False)
        rows = prepare_live_training_rows(rows or [])
    except Exception:
        return buckets

    for row in rows or []:
        regime = str(row.get("market_regime") or row.get("regime") or "neutral").lower()
        if regime not in buckets:
            regime = "neutral"
        buckets[regime].append(row)
    return buckets


def _fit_regime_model(samples: list[dict[str, Any]], *, regime: str) -> dict[str, Any]:
    import joblib
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    records = []
    for row in samples:
        y = _direction_label(row)
        if not y:
            continue
        feats = _row_to_feature_dict(row)
        records.append({**feats, "direction_label": y, "timestamp": row.get("timestamp") or ""})
    if len(records) < 15:
        return {"trained": False, "reason": "insufficient_labeled_with_direction", "n": len(records)}

    frame = pd.DataFrame(records)
    split = temporal_train_test_split(
        frame,
        feature_columns=FEATURE_COLUMNS,
        label_column="direction_label",
        min_train=10,
        min_test=3,
    )
    if split is None:
        # Fit on all when split too small — still honest about hold-out absence
        x = frame[list(FEATURE_COLUMNS)]
        y = frame["direction_label"]
        pipe = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(max_iter=400, class_weight="balanced", solver="lbfgs"),
                ),
            ]
        )
        pipe.fit(x, y)
        acc = float(accuracy_score(y, pipe.predict(x)))
        holdout = False
    else:
        x_train, x_test, y_train, y_test = split
        pipe = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(max_iter=400, class_weight="balanced", solver="lbfgs"),
                ),
            ]
        )
        pipe.fit(x_train, y_train)
        acc = float(accuracy_score(y_test, pipe.predict(x_test)))
        holdout = True

    target = _REGIME_MODEL_ROOT / regime
    target.mkdir(parents=True, exist_ok=True)
    model_path = target / "model.joblib"
    meta_path = target / "meta.json"
    bundle = {
        "model": pipe,
        "feature_columns": list(FEATURE_COLUMNS),
        "regime": regime,
        "classes": list(getattr(pipe.named_steps["clf"], "classes_", [])),
    }
    joblib.dump(bundle, model_path)
    try:
        rel = str(model_path.relative_to(Path(__file__).resolve().parents[1]))
    except ValueError:
        rel = str(model_path)
    meta = {
        "regime": regime,
        "samples": len(records),
        "status": "artifact_ready",
        "accuracy": round(acc, 4),
        "holdout_eval": holdout,
        "updated_at": _utcnow(),
        "model_path": rel,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {
        "trained": True,
        "artifact_written": True,
        "accuracy": meta["accuracy"],
        "samples": len(records),
        "holdout_eval": holdout,
        "model_path": meta["model_path"],
    }


async def train_regime_models(*, force: bool = False) -> dict[str, Any]:
    buckets = await collect_regime_buckets()
    status: dict[str, Any] = {
        "started_at": _utcnow(),
        "min_samples_per_regime": MIN_SAMPLES_PER_REGIME,
        "regimes": {},
        "artifacts_written": 0,
    }

    _REGIME_MODEL_ROOT.mkdir(parents=True, exist_ok=True)

    for regime in REGIMES:
        samples = buckets.get(regime) or []
        entry: dict[str, Any] = {
            "samples": len(samples),
            "ready": len(samples) >= MIN_SAMPLES_PER_REGIME,
            "artifact_written": False,
        }
        if entry["ready"] or force:
            try:
                fit = _fit_regime_model(samples, regime=regime)
                entry.update(fit)
                if fit.get("artifact_written"):
                    status["artifacts_written"] += 1
            except Exception as exc:
                logger.exception("Regime train failed for %s", regime)
                entry["status"] = "train_error"
                entry["error"] = str(exc)[:200]
        else:
            entry["status"] = "insufficient_labeled_samples"
        status["regimes"][regime] = entry

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    status["finished_at"] = _utcnow()
    status["registry"] = regime_model_registry()
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status


if __name__ == "__main__":
    import asyncio

    out = asyncio.run(train_regime_models())
    print(json.dumps(out, indent=2))
