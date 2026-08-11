"""
BLACKDARK — Data moat guard (acquisition defensibility).

Enforces live-only oracle labeling, blocks synthetic backfill in production,
and exposes honest flywheel / dataset readiness metrics for due diligence.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.DataMoat")

SYNTHETIC_SOURCES = frozenset({"historical_seed", "synthetic", "demo_seed"})


def _enabled() -> bool:
    return getattr(config, "DATA_MOAT_GUARD_ENABLED", True)


def _live_only() -> bool:
    return getattr(config, "DATA_MOAT_LIVE_ONLY", True)


def _block_synthetic_seed() -> bool:
    return getattr(config, "DATA_MOAT_BLOCK_SYNTHETIC_SEED", True)


def _require_features() -> bool:
    return getattr(config, "DATA_MOAT_REQUIRE_FEATURES_JSON", True)


def _is_production() -> bool:
    env = os.getenv("ENV", os.getenv("RAILWAY_ENVIRONMENT", "")).strip().lower()
    local = os.getenv("LOCAL_DEV", "false").lower() in {"1", "true", "yes"}
    return env in {"production", "prod"} and not local


def validate_prediction_insert(
    *,
    source: str,
    features_json: str | None,
) -> tuple[bool, str]:
    """Gate oracle prediction inserts — live labels only in production."""
    if not _enabled():
        return True, "ok"

    src = (source or "oracle").strip().lower()
    if _block_synthetic_seed() and src in SYNTHETIC_SOURCES and (_is_production() or _live_only()):
        return False, f"synthetic_source_blocked:{src}"

    if _require_features() and src == "oracle" and not (features_json or "").strip() and _is_production():
        return False, "features_json_required_for_live_oracle"

    return True, "ok"


def assert_synthetic_seed_allowed() -> None:
    """Raise if historical seed scripts must not run (production / live-only mode)."""
    if not _enabled():
        return
    if _block_synthetic_seed() and (_is_production() or _live_only()):
        raise RuntimeError(
            "Synthetic oracle seeding is disabled (DATA_MOAT_LIVE_ONLY / production). "
            "Use live traffic only to build the acquisition dataset."
        )


def _model_artifact_present() -> bool:
    model_dir = getattr(config, "ML_MODELS_DIR", Path("data/models"))
    if not model_dir.exists():
        return False
    return any(any(model_dir.glob(pattern)) for pattern in ("*.joblib", "*.pkl", "*.onnx"))


async def fetch_dataset_stats() -> dict[str, Any]:
    from oracle_integrity import live_source_sql

    stats: dict[str, Any] = {
        "live_predictions": 0,
        "synthetic_predictions": 0,
        "live_with_features": 0,
        "live_labeled": 0,
        "live_resolved": 0,
        "features_coverage_pct": 0.0,
    }
    try:
        from database import get_connection

        live_clause = live_source_sql()
        async with get_connection() as db:
            live_row = await (await db.execute(f"SELECT COUNT(*) FROM oracle_predictions WHERE {live_clause}")).fetchone()
            syn_row = await (
                await db.execute("SELECT COUNT(*) FROM oracle_predictions WHERE source = 'historical_seed'")
            ).fetchone()
            feat_row = await (
                await db.execute(
                    f"""
                    SELECT COUNT(*) FROM oracle_predictions
                    WHERE {live_clause}
                      AND features_json IS NOT NULL AND TRIM(features_json) != ''
                    """
                )
            ).fetchone()
            labeled_row = await (
                await db.execute(
                    f"""
                    SELECT COUNT(*) FROM oracle_predictions
                    WHERE {live_clause} AND resolved = 1 AND label IS NOT NULL
                    """
                )
            ).fetchone()
            resolved_row = await (
                await db.execute(f"SELECT COUNT(*) FROM oracle_predictions WHERE {live_clause} AND resolved = 1")
            ).fetchone()

        live = int(live_row[0]) if live_row else 0
        stats["live_predictions"] = live
        stats["synthetic_predictions"] = int(syn_row[0]) if syn_row else 0
        stats["live_with_features"] = int(feat_row[0]) if feat_row else 0
        stats["live_labeled"] = int(labeled_row[0]) if labeled_row else 0
        stats["live_resolved"] = int(resolved_row[0]) if resolved_row else 0
        stats["features_coverage_pct"] = round(
            (stats["live_with_features"] / live * 100) if live else 0.0,
            1,
        )
    except Exception:
        logger.exception("Dataset stats query failed")
    return stats


def _copyability_risk(labeled: int, model_present: bool) -> str:
    if model_present and labeled >= int(getattr(config, "ML_MIN_TRAIN_SAMPLES", 50)):
        return "moderate"
    if labeled >= 500:
        return "moderate"
    return "high"


async def build_moat_build_status() -> dict[str, Any]:
    """Honest acquisition readiness — no inflated marketing metrics."""
    dataset = await fetch_dataset_stats()
    min_train = int(getattr(config, "ML_MIN_TRAIN_SAMPLES", 50))
    labeled = int(dataset.get("live_labeled") or 0)
    model_present = _model_artifact_present()
    samples_until_train = max(0, min_train - labeled)

    readiness_score = min(
        100,
        int(
            min(labeled / max(min_train, 1), 1.0) * 40
            + (dataset.get("features_coverage_pct") or 0) * 0.35
            + (20 if model_present else 0)
            + (5 if _enabled() and _live_only() else 0)
        ),
    )

    recommendations: list[str] = []
    if int(dataset.get("synthetic_predictions") or 0) > 0:
        recommendations.append(
            "Archive or exclude synthetic historical_seed rows from investor-facing metrics."
        )
    if (dataset.get("features_coverage_pct") or 0) < 95:
        recommendations.append(
            "Route every live Oracle call through log_oracle_signal() so features_json is always stored."
        )
    if labeled < min_train:
        recommendations.append(
            f"Collect {samples_until_train} more live labeled predictions before claiming proprietary AI."
        )
    if not model_present:
        recommendations.append(
            "Train and deploy the first .joblib model once labeled samples >= ML_MIN_TRAIN_SAMPLES."
        )
    if not getattr(config, "ML_FLYWHEEL_ENABLED", True):
        recommendations.append("Enable ML_FLYWHEEL_ENABLED so resolutions and exports run hourly.")

    if readiness_score >= 70:
        readiness_label = "Investable dataset"
    elif readiness_score >= 35:
        readiness_label = "Building"
    else:
        readiness_label = "Early"

    return {
        "enabled": _enabled(),
        "live_only_enforced": _live_only(),
        "synthetic_seed_blocked": _block_synthetic_seed(),
        "features_json_required_in_production": _require_features(),
        "production_mode": _is_production(),
        "dataset": dataset,
        "ml": {
            "flywheel_enabled": getattr(config, "ML_FLYWHEEL_ENABLED", True),
            "auto_train_enabled": getattr(config, "ML_AUTO_TRAIN", True),
            "min_train_samples": min_train,
            "labeled_live_samples": labeled,
            "samples_until_train": samples_until_train,
            "model_artifact_present": model_present,
        },
        "acquisition_readiness_score": readiness_score,
        "acquisition_readiness_label": readiness_label,
        "copyability_risk": _copyability_risk(labeled, model_present),
        "recommended_actions_en": recommendations,
        "integrity_note_en": (
            "Public oracle accuracy and training exports use live predictions only; "
            "synthetic historical_seed is excluded via oracle_integrity."
        ),
    }


def data_moat_guard_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "live_only": _live_only(),
        "block_synthetic_seed": _block_synthetic_seed(),
        "require_features_json": _require_features(),
        "production_mode": _is_production(),
    }
