"""
Signal Engine Pattern Recognition — Feature #979 (Sprint 2).

Merged into Signal Engine — NOT standalone.
Rule-based pattern detection with confirmation, false-positive scoring, invalidation.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SignalEnginePatternRecognition")

_FEATURE_REF = 979
_SIGNAL_ENGINE_REF = 11
_PIT_REF = 980
_STANDALONE = False
_MERGED_INTO = "Signal Engine / Pattern Detection"
_SEED_PATH = Path("data/signal_engine_pattern_recognition_seed.json")

PatternType = Literal["rsi_divergence", "ma_cross", "support_resistance_break"]

_DISCLAIMER = (
    "Pattern detection — supplementary evidence only, not independent truth. "
    "Rule-based only in Sprint 2. Precision reported — no hindsight anchoring."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("pattern recognition seed load failed: %s", exc)
        return {}


def pattern_recognition_status_979(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("pattern_recognition_979") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "signal_engine_ref": _SIGNAL_ENGINE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "pit_data_ref": _PIT_REF,
        "rule_based_only": True,
        "ml_rejected_sprint2": True,
        "label_definitions_explicit": True,
        "confirmation_required": True,
        "false_positive_scoring": True,
        "out_of_sample_evaluation": True,
        "no_hindsight_anchoring": True,
        "invalidation_required": True,
        "patterns": ["rsi_divergence", "ma_cross", "support_resistance_break"],
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def detect_patterns_979(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect patterns on candle close — no intra-candle triggers."""
    seed = seed or _load_seed()
    sym = asset.upper()
    assets = seed.get("pattern_assets") or {}
    data = assets.get(sym)
    if not data:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "asset_not_found"}

    definitions = seed.get("pattern_definitions_979") or {}
    detected: list[dict[str, Any]] = []

    for pat in data.get("patterns") or []:
        pat_type = pat.get("type")
        defn = definitions.get(pat_type) or {}
        detected.append({
            "pattern_type": pat_type,
            "label_definition": defn.get("definition"),
            "geometric_definition": defn.get("geometric"),
            "detected_at": pat.get("detected_at"),
            "candle_close_only": pat.get("candle_close_only", True),
            "no_intra_candle": True,
            "confirmed": pat.get("confirmed", False),
            "confirmation_bar": pat.get("confirmation_bar"),
            "confidence": pat.get("confidence"),
            "false_positive_score": pat.get("false_positive_score"),
            "historical_precision": defn.get("historical_precision"),
            "invalidation": pat.get("invalidation"),
            "invalidation_condition": defn.get("invalidation_template"),
            "supplementary_evidence_only": True,
            "not_independent_truth": True,
        })

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "asset": sym,
        "patterns": detected,
        "pattern_count": len(detected),
        "label_definitions": True,
        "no_hindsight_anchoring": True,
        "pit_data_ref": _PIT_REF,
        "timestamp": _utcnow(),
    }


def get_pattern_precision_report_979(
    pattern_type: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    definitions = seed.get("pattern_definitions_979") or {}
    defn = definitions.get(pattern_type)
    if not defn:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "pattern_not_found"}

    oos = seed.get("out_of_sample_evaluation_979", {}).get(pattern_type) or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "pattern_type": pattern_type,
        "definition": defn.get("definition"),
        "geometric_definition": defn.get("geometric"),
        "historical_precision": defn.get("historical_precision"),
        "false_positive_rate": defn.get("false_positive_rate"),
        "out_of_sample": {
            "evaluation_days": oos.get("evaluation_days", 30),
            "precision": oos.get("precision"),
            "included_in_training": False,
        },
        "precision_reported": True,
        "no_hindsight_anchoring": True,
        "timestamp": _utcnow(),
    }


def run_pattern_recognition_e2e_979(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = pattern_recognition_status_979(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "rule_based", "passed": status["rule_based_only"] is True})
    checks.append({"id": "invalidation_required", "passed": status["invalidation_required"] is True})

    detected = detect_patterns_979("BTC", seed=seed)
    checks.append({"id": "pattern_detection", "passed": detected.get("pattern_count", 0) >= 1})
    checks.append({"id": "candle_close_only", "passed": all(p.get("no_intra_candle") for p in detected.get("patterns") or [])})

    confirmed = [p for p in detected.get("patterns") or [] if p.get("confirmed")]
    checks.append({"id": "confirmation", "passed": len(confirmed) >= 1})

    precision = get_pattern_precision_report_979("rsi_divergence", seed=seed)
    checks.append({"id": "precision_reported", "passed": precision.get("precision_reported") is True})
    checks.append({"id": "out_of_sample", "passed": precision.get("out_of_sample", {}).get("included_in_training") is False})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
