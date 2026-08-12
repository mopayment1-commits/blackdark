"""
BLACKDARK — D5 Regime bootstrap honesty board (Report-1 H2/H8 cure).

Surfaces bootstrap/synthetic flags publicly so product_complete never hides model maturity.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_STATUS = Path("data/models/regime/training_status.json")


def build_d5_honesty_board() -> dict[str, Any]:
    status: dict[str, Any] = {}
    if _STATUS.exists():
        try:
            status = json.loads(_STATUS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {"error": "unreadable_training_status"}

    regimes = status.get("regimes") if isinstance(status.get("regimes"), dict) else {}
    rows = []
    synthetic_any = False
    bootstrap = bool(
        status.get("per_regime_models_live_bootstrapped")
        or status.get("bootstrap")
        or status.get("bootstrapped")
    )
    for name, meta_raw in regimes.items() if regimes else []:
        meta = meta_raw if isinstance(meta_raw, dict) else {"raw": meta_raw}
        synth = bool(meta.get("synthetic_class_balance") or meta.get("synthetic"))
        synthetic_any = synthetic_any or synth
        rows.append(
            {
                "regime": name,
                "samples": meta.get("samples") or meta.get("n") or meta.get("train_samples"),
                "holdout_accuracy": meta.get("holdout_accuracy") or meta.get("accuracy"),
                "synthetic_class_balance": synth,
                "artifact": f"data/models/regime/{name}/model.joblib",
            }
        )

    mature = (not bootstrap) and (not synthetic_any) and bool(rows)
    return {
        "surface": "d5_regime_honesty",
        "product_complete": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "bootstrap": bootstrap,
        "synthetic_any": synthetic_any,
        "mature_for_committee": mature,
        "regimes": rows,
        "raw_status_keys": sorted(status.keys()) if status else [],
        "public_disclosure": (
            "Regime models may be bootstrapped / class-balanced with synthetic samples. "
            "This board is the mandatory honesty surface — do not claim mature regime ML "
            "while bootstrap or synthetic flags are true."
        ),
        "retrain_path": "python -m ml.train_regime_models",
        "page": "/d5-honesty",
        "api": "/api/public/d5-honesty",
        "closes_weaknesses": ["H2", "H8"],
    }
