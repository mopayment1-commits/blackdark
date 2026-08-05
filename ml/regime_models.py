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


def regime_model_registry() -> dict[str, Any]:
    """Public-safe registry of D5 regime-conditional model status."""
    regimes: dict[str, Any] = {}
    artifacts_ready = 0
    for regime in REGIMES:
        has = regime_has_artifact(regime)
        if has:
            artifacts_ready += 1
        regimes[regime] = {
            "artifact_present": has,
            "artifact_path": str(_artifact_path(regime).relative_to(Path(__file__).resolve().parents[1]))
            if has
            else None,
            "status": "artifact_ready" if has else "pending_training",
            "confidence_multiplier": float(REGIME_CONF_MULT.get(regime, 1.0)),
        }

    per_regime = artifacts_ready == len(REGIMES)
    if per_regime:
        evidence = "per_regime_artifacts_live"
        status = "per_regime_models_live"
    elif artifacts_ready > 0:
        evidence = "partial_artifacts"
        status = "partial_regime_artifacts"
    else:
        evidence = "weights_live"
        status = "weights_and_confidence_live"

    return {
        "differentiator": "D5",
        "status": status,
        "evidence_status": evidence,
        "per_regime_models": per_regime,
        "artifacts_ready": artifacts_ready,
        "artifacts_expected": len(REGIMES),
        "regimes": regimes,
        "note": (
            "Separate per-regime ML artifacts are live."
            if per_regime
            else "Regime confidence routing is live; dedicated per-regime model files pending training."
        ),
    }
