"""
Order Book Pattern Recognition Engine — Feature #281 (Wave 3, renamed).

Renamed from "Order Book Intelligence AI/ML" — NOT trading signals.
Rule-based patterns first; ML augmentation deferred until 6 months
rule-based validation + legal review.

Output = historical pattern match only. pattern_match_score ≠ profit probability.
NO financial performance claims (Sharpe, drawdown, win rate prohibited).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OrderBookPatternRecognition")

_FEATURE_ID = 281
_RENAMED_FROM = "Order Book Intelligence AI/ML"
_OFFICIAL_NAME = "Order Book Pattern Recognition Engine"
_STANDALONE = False
_WAVE = 3
_SPRINT = 2
_SEED_PATH = Path("data/order_book_pattern_recognition_seed.json")
_METHODOLOGY_VERSION = "1.0"
_RULE_BASED_VALIDATION_MONTHS = 6
_BACKTEST_YEARS_MIN = 2
_RULE_LATENCY_MAX_SEC = 60
_ML_LATENCY_MAX_SEC = 900

_BANNED_OUTPUT_TERMS = (
    "signal",
    "recommendation",
    "buy",
    "sell",
    "profit probability",
    "win rate",
    "sharpe",
    "drawdown",
    "guaranteed",
)

_DISCLAIMER = (
    "Pattern recognition output describes historical pattern similarity only. "
    "pattern_match_score measures structural match to documented patterns — "
    "not profit probability or investment advice. "
    "Past performance does not indicate future results. "
    "No forward performance guarantee."
)

Phase = Literal["rule_based", "ml_augmentation"]
ConfidenceLevel = Literal["low", "medium", "high"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"patterns": {}, "compliance": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("pattern recognition seed load failed: %s", exc)
        return {"patterns": {}, "compliance": {}}


def build_compliance_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Legal/compliance gate — ML blocked until review + 6-month rule baseline."""
    seed = seed or _load_seed()
    compliance = seed.get("compliance") or {}
    legal_review = bool(compliance.get("legal_review_complete"))
    rule_months = int(compliance.get("rule_based_months_validated", 0))
    rule_met = rule_months >= _RULE_BASED_VALIDATION_MONTHS
    ml_allowed = legal_review and rule_met

    return {
        "legal_review_required": True,
        "legal_review_complete": legal_review,
        "rule_based_validation_months_required": _RULE_BASED_VALIDATION_MONTHS,
        "rule_based_months_validated": rule_months,
        "rule_baseline_met": rule_met,
        "ml_augmentation_allowed": ml_allowed,
        "ml_blocked_until_compliance": not ml_allowed,
        "current_phase": "rule_based" if not ml_allowed else "ml_augmentation",
        "display": (
            f"Phase: {'rule_based' if not ml_allowed else 'ml_augmentation'} | "
            f"Legal review: {'complete' if legal_review else 'pending'} | "
            f"Rule baseline: {rule_months}/{_RULE_BASED_VALIDATION_MONTHS} months"
        ),
    }


def build_scope_lock(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    phase = seed.get("current_phase", 1)
    return {
        "current_phase": phase,
        "phases": {
            1: "Rule-based patterns (Sprint 2)",
            2: "ML augmentation (Wave 3 — after compliance)",
        },
        "no_black_box_before_validation": True,
        "ml_deferred": True,
        "display": (
            f"Phase {phase}: Rule-based patterns first | "
            "ML augmentation = Wave 3 after 6 months rule-based validation + legal review | "
            "No black-box models before validation"
        ),
    }


def build_acceptance_criteria(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Institutional acceptance — NO financial performance claims."""
    seed = seed or _load_seed()
    backtest = seed.get("backtest") or {}
    return {
        "financial_claims_prohibited": True,
        "sharpe_claims_banned": True,
        "drawdown_claims_banned": True,
        "win_rate_claims_banned": True,
        "backtest_results_documented": True,
        "backtest_years_min": _BACKTEST_YEARS_MIN,
        "backtest_years_actual": backtest.get("years", 0),
        "performance_metrics_historical_only": True,
        "no_forward_performance_guarantee": True,
        "pattern_match_score_not_profit_probability": True,
        "rule_based_latency_max_sec": _RULE_LATENCY_MAX_SEC,
        "ml_latency_max_sec": _ML_LATENCY_MAX_SEC,
        "disclaimer_mandatory": True,
        "display": (
            "Backtest results documented (historical only) | "
            f"Backtest ≥ {_BACKTEST_YEARS_MIN} years | "
            "No Sharpe/drawdown/win-rate claims | "
            "pattern_match_score ≠ profit probability"
        ),
    }


def build_pattern_match(pattern: dict[str, Any], *, asset: str) -> dict[str, Any]:
    """Historical pattern match — NOT a trading signal."""
    score = float(pattern.get("pattern_match_score", 0))
    if score >= 0.75:
        confidence: ConfidenceLevel = "high"
    elif score >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    reasons = pattern.get("explainability_reasons") or []
    display_reasons = "; ".join(reasons[:5])

    output = {
        "asset": asset,
        "pattern_id": pattern.get("pattern_id"),
        "pattern_name": pattern.get("pattern_name"),
        "pattern_match_score": round(score, 4),
        "confidence_level": confidence,
        "pattern_match_score_label": "structural similarity — not profit probability",
        "not_a_signal": True,
        "not_a_recommendation": True,
        "historical_only": True,
        "explainability_reasons": reasons,
        "matched_period": pattern.get("matched_period"),
        "historical_outcome": pattern.get("historical_outcome"),
        "historical_outcome_note": "Historical outcome for reference — not predictive",
        "backtest_window_years": pattern.get("backtest_window_years"),
        "feature_count": pattern.get("feature_count", 0),
        "phase": pattern.get("phase", "rule_based"),
        "display": (
            f"Pattern: {pattern.get('pattern_name')} | "
            f"Match score: {score:.2%} (structural) | "
            f"Confidence: {confidence} | "
            f"Reasons: {display_reasons or 'N/A'}"
        ),
        "disclaimer": _DISCLAIMER,
    }

    display_text = output["display"].lower()
    for banned in ("sharpe", "win rate", "profit probability", "guaranteed return"):
        assert banned not in display_text

    return output


def build_backtest_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Backtest documentation — historical metrics only, no forward claims."""
    seed = seed or _load_seed()
    backtest = seed.get("backtest") or {}
    return {
        "years": backtest.get("years", 0),
        "start_date": backtest.get("start_date"),
        "end_date": backtest.get("end_date"),
        "pattern_count": backtest.get("pattern_count", 0),
        "walk_forward_folds": backtest.get("walk_forward_folds", 0),
        "historical_metrics": backtest.get("historical_metrics") or {},
        "historical_only": True,
        "no_forward_guarantee": True,
        "financial_claims_removed": True,
        "display": (
            f"Backtest: {backtest.get('years', 0)} years "
            f"({backtest.get('start_date')} → {backtest.get('end_date')}) | "
            f"Patterns: {backtest.get('pattern_count', 0)} | "
            f"Walk-forward folds: {backtest.get('walk_forward_folds', 0)} | "
            "Historical only — no forward guarantee"
        ),
        "disclaimer": _DISCLAIMER,
    }


def build_pattern_recognition_panel(asset: str = "BTC") -> dict[str, Any]:
    """Pattern recognition panel — Wave 3, rule-based phase active."""
    t0 = time.perf_counter()
    seed = _load_seed()
    gate = build_compliance_gate(seed)
    sym = asset.upper()
    patterns = (seed.get("patterns") or {}).get(sym) or []

    if gate["ml_blocked_until_compliance"] and any(
        p.get("phase") == "ml_augmentation" for p in patterns
    ):
        patterns = [p for p in patterns if p.get("phase") == "rule_based"]

    matches = [build_pattern_match(p, asset=sym) for p in patterns]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "official_name": _OFFICIAL_NAME,
        "standalone": _STANDALONE,
        "wave": _WAVE,
        "asset": sym,
        "surface": "order_book_pattern_recognition",
        "pattern_matches": matches,
        "match_count": len(matches),
        "compliance_gate": gate,
        "scope_lock": build_scope_lock(seed),
        "backtest": build_backtest_documentation(seed),
        "acceptance_criteria": build_acceptance_criteria(seed),
        "not_trading_signals": True,
        "output_type": "historical_pattern_match",
        "methodology_version": _METHODOLOGY_VERSION,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def pattern_recognition_status() -> dict[str, Any]:
    seed = _load_seed()
    gate = build_compliance_gate(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _OFFICIAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "wave": _WAVE,
        "compliance_gate": gate,
        "scope_lock": build_scope_lock(seed),
        "acceptance_criteria": build_acceptance_criteria(seed),
        "banned_output_terms": list(_BANNED_OUTPUT_TERMS),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_investment_advice": True,
        "timestamp": _utcnow(),
    }
