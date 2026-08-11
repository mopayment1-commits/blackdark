"""
BLACKDARK — Buyer-facing Model Card (Report-2 C-P1-02).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


async def build_buyer_model_card() -> dict[str, Any]:
    regime = {}
    try:
        import json
        from pathlib import Path

        p = Path("data/models/regime/training_status.json")
        if p.exists():
            regime = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        regime = {}

    provenance = {}
    try:
        from data_provenance_score import compute_data_provenance_score

        provenance = compute_data_provenance_score(symbol="BTC")
    except Exception:
        provenance = {"score": None}

    coverage = {}
    try:
        from coverage_honesty import build_coverage_honesty_board

        coverage = await build_coverage_honesty_board()
    except Exception:
        coverage = {}

    bootstrap = bool(
        regime.get("per_regime_models_live_bootstrapped")
        or regime.get("bootstrap")
        or any(
            (regime.get("regimes") or {}).get(r, {}).get("synthetic_class_balance")
            for r in ("risk_on", "neutral", "risk_off", "panic")
        )
        if isinstance(regime.get("regimes"), dict)
        else regime.get("synthetic_used")
    )

    return {
        "surface": "buyer_model_card",
        "product_complete": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "model_name": "BLACKDARK Unified Oracle Direction v1",
        "version": "unified_multimodal_v1",
        "intended_use": (
            "Decision-support for crypto market direction and opportunity veto — "
            "not automated portfolio management advice."
        ),
        "out_of_scope": [
            "Guaranteed returns",
            "Legal/financial advice",
            "Venues outside LIVE coverage catalog",
        ],
        "performance_limits": {
            "regime_training": regime.get("regimes") or regime,
            "bootstrap_honesty": bootstrap,
            "holdout_note": "Regime accuracies vary; bootstrap/synthetic flags disclosed",
        },
        "failure_modes": [
            "Cold-start half-life falls back to directional 1h prior until history accumulates",
            "Coverage limited to LIVE venues — planned venues excluded from decisions",
            "DEX live leg requires Jupiter wallet + keys; otherwise dry-run economics",
            "Net-Edge soft advisory on some directional paths",
        ],
        "data_provenance": provenance,
        "coverage": {
            "live_count": (coverage.get("live") or {}).get("count"),
            "page": "/coverage-honesty",
        },
        "governance": {
            "kill_rate": "/kill-rate",
            "miss_feed": "/miss-feed",
            "anti_hype": "/anti-hype",
            "audit_chain": "oracle_audit_chain.py",
        },
        "update_cadence": "continuous flywheel + regime retrain path",
        "page": "/model-card",
        "api": "/api/institutional/model-card",
        "pdf_ready": True,
    }
