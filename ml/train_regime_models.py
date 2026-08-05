"""
BLACKDARK — Per-regime model training entry (D5).

Honest behavior: trains only when enough live labeled samples exist per regime.
Otherwise writes a status file and leaves artifacts absent (registry stays weights_live).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml.regime_models import REGIMES, _REGIME_MODEL_ROOT, regime_model_registry

MIN_SAMPLES_PER_REGIME = 40
STATUS_PATH = Path(__file__).resolve().parents[1] / "data" / "models" / "regime" / "training_status.json"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def collect_regime_buckets() -> dict[str, list[dict[str, Any]]]:
    """Best-effort bucket labeled predictions by stored market_regime."""
    buckets = {r: [] for r in REGIMES}
    try:
        from database import fetch_labeled_oracle_predictions

        rows = await fetch_labeled_oracle_predictions(limit=2000, include_synthetic=False)
    except Exception:
        return buckets

    for row in rows or []:
        regime = str(row.get("market_regime") or row.get("regime") or "neutral").lower()
        if regime not in buckets:
            regime = "neutral"
        buckets[regime].append(row)
    return buckets


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
            # Placeholder artifact marker — real sklearn fit wires in when feature matrix is stable.
            # Do not claim a production model until a real joblib payload exists with metrics.
            target = _REGIME_MODEL_ROOT / regime
            target.mkdir(parents=True, exist_ok=True)
            meta_path = target / "meta.json"
            meta_path.write_text(
                json.dumps(
                    {
                        "regime": regime,
                        "samples": len(samples),
                        "status": "meta_only_pending_sklearn_fit",
                        "updated_at": _utcnow(),
                        "note": "meta written; model.joblib not claimed until real train completes",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            entry["meta_path"] = str(meta_path.relative_to(Path(__file__).resolve().parents[1]))
            entry["status"] = "meta_only_pending_sklearn_fit"
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
