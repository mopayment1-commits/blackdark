"""
BLACKDARK — Per-regime model registry (Differentiator D5).

Honest status: confidence/weight routing is live; separate trained
artifacts per regime are registered here when available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

REGIMES = ("risk_on", "neutral", "risk_off", "panic")

# Soft multipliers shared with regime_router (single source of truth)
REGIME_CONF_MULT = {
    "risk_on": 1.05,
    "neutral": 1.0,
    "risk_off": 0.92,
    "panic": 0.78,
}

# Optional on-disk artifact layout: data/models/regime/<regime>/model.joblib
_REGIME_MODEL_ROOT = Path(__file__).resolve().parents[1] / "data" / "models" / "regime"


def _artifact_path(regime: str) -> Path:
    return _REGIME_MODEL_ROOT / regime / "model.joblib"


def regime_has_artifact(regime: str) -> bool:
    try:
        return _artifact_path(regime).is_file()
    except Exception:
        return False


def load_regime_predictor(regime: str) -> dict[str, Any] | None:
    """Load per-regime joblib bundle when present (D5 inference deepen)."""
    path = _artifact_path(regime)
    if not path.is_file():
        return None
    try:
        import joblib

        bundle = joblib.load(path)
        if not isinstance(bundle, dict) or "model" not in bundle:
            return None
        return bundle
    except Exception:
        return None


def predict_with_regime_artifact(
    regime: str,
    features: dict[str, Any],
) -> dict[str, Any] | None:
    """Run dedicated regime model if artifact exists; else None (caller falls back)."""
    bundle = load_regime_predictor(regime)
    if not bundle:
        return None
    try:
        import pandas as pd

        model = bundle["model"]
        cols = list(bundle.get("feature_columns") or [])
        if not cols:
            return None
        row = {c: float(features.get(c, 0.0) or 0.0) for c in cols}
        frame = pd.DataFrame([row])
        pred = str(model.predict(frame[cols])[0])
        confidence = None
        if hasattr(model, "predict_proba"):
            try:
                probs = model.predict_proba(frame[cols])[0]
                classes = list(getattr(model, "classes_", []) or bundle.get("classes") or [])
                if classes:
                    idx = list(classes).index(pred) if pred in list(classes) else int(probs.argmax())
                    confidence = round(float(probs[idx]) * 100.0, 2)
            except Exception:
                confidence = None
        return {
            "available": True,
            "direction": pred,
            "confidence_raw_percent": confidence,
            "regime_model_used": True,
            "regime": regime,
            "source": "per_regime_artifact",
        }
    except Exception:
        return None


def _artifact_relative_path(path: Path, has_artifact: bool) -> str | None:
    if not has_artifact:
        return None
    try:
        return str(path.relative_to(Path(__file__).resolve().parents[1]))
    except ValueError:
        return str(path)


def _load_regime_meta(regime: str) -> dict[str, Any]:
    import json

    meta_path = _REGIME_MODEL_ROOT / regime / "meta.json"
    if not meta_path.is_file():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _regime_registry_row(regime: str) -> tuple[dict[str, Any], bool, bool]:
    has_artifact = regime_has_artifact(regime)
    meta = _load_regime_meta(regime)
    bootstrap = bool(meta.get("bootstrap_samples") or meta.get("synthetic_class_balance"))
    return {
        "artifact_present": has_artifact,
        "artifact_path": _artifact_relative_path(_artifact_path(regime), has_artifact),
        "status": "artifact_ready" if has_artifact else "pending_training",
        "confidence_multiplier": float(REGIME_CONF_MULT.get(regime, 1.0)),
        "bootstrap_samples": bool(meta.get("bootstrap_samples")),
        "synthetic_class_balance": bool(meta.get("synthetic_class_balance")),
        "samples": meta.get("samples"),
    }, has_artifact, bootstrap


def _registry_status(artifacts_ready: int, bootstrap_any: bool) -> tuple[str, str, str]:
    per_regime = artifacts_ready == len(REGIMES)
    if per_regime and not bootstrap_any:
        return "per_regime_artifacts_live", "per_regime_models_live", "Separate per-regime ML artifacts are live (labeled history)."
    if per_regime and bootstrap_any:
        return (
            "per_regime_artifacts_bootstrapped",
            "per_regime_models_live_bootstrapped",
            "All four regime artifacts present; one or more used bootstrap/synthetic "
            "class balance — replace with live labeled history as the flywheel grows.",
        )
    if artifacts_ready > 0:
        return (
            "partial_artifacts",
            "partial_regime_artifacts",
            "Regime confidence routing is live; dedicated per-regime model files pending training.",
        )
    return (
        "weights_live",
        "weights_and_confidence_live",
        "Regime confidence routing is live; dedicated per-regime model files pending training.",
    )


def regime_model_registry() -> dict[str, Any]:
    """Public-safe registry of D5 regime-conditional model status."""
    regimes: dict[str, Any] = {}
    artifacts_ready = 0
    bootstrap_any = False
    for regime in REGIMES:
        row, has_artifact, bootstrap = _regime_registry_row(regime)
        if has_artifact:
            artifacts_ready += 1
        if bootstrap:
            bootstrap_any = True
        regimes[regime] = row

    per_regime = artifacts_ready == len(REGIMES)
    evidence, status, note = _registry_status(artifacts_ready, bootstrap_any)

    return {
        "differentiator": "D5",
        "status": status,
        "evidence_status": evidence,
        "per_regime_models": per_regime,
        "artifacts_ready": artifacts_ready,
        "artifacts_expected": len(REGIMES),
        "bootstrap_used": bootstrap_any,
        "regimes": regimes,
        "note": note,
    }
