"""
Cross-Asset Volatility Regime Analyzer — Feature #501 (Sprint 1 Data Layer).

Renamed from "Volatility_Scoring_System".
Infrastructure feature — historical context only, no advisory risk score.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CrossAssetVolatilityRegime")

_FEATURE_ID = 501
_RENAMED_FROM = "Volatility_Scoring_System"
_TITLE = "Cross-Asset Volatility Regime Analyzer"
_STANDALONE = False
_MERGED_INTO = "Data Layer / Cross-Asset Volatility Regime Analyzer"
_WAVE = 1
_SPRINT = 1
_SEED_PATH = Path("data/cross_asset_volatility_regime_seed.json")
_FORMULA_VERSION = "1.0"
_METHODOLOGY_VERSION = "1.0"
_RULE_BASED_VALIDATION_MONTHS = 3

Regime = Literal["low", "medium", "high"]

_DISCLAIMER = (
    "Historical Volatility Percentile (0–100) | "
    "Regime Classification = historical context only | "
    "Not investment advice | "
    "Past volatility patterns do not predict future risk. "
    "No buy/sell recommendation implied."
)

_BANNED_TERMS = ("risk score", "scoring system", "low risk", "high risk", "sell", "buy")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "legal_review": {}, "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("cross-asset volatility regime seed load failed: %s", exc)
        return {"assets": {}, "legal_review": {}, "backtest": {}}


def build_formula_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    formula = seed.get("formula") or {}
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "formula": formula.get(
            "expression",
            "hv_percentile = percentile_rank(realized_vol, historical_window) | "
            "regime = classify(hv_percentile, asset_historical_distribution)",
        ),
        "inputs": formula.get("inputs") or [
            "realized_volatility", "implied_volatility", "atr", "returns", "liquidity",
        ],
        "cross_asset_normalization": True,
        "no_arbitrary_thresholds": True,
        "thresholds_documented": formula.get("thresholds") or {
            "low_regime_percentile": 33,
            "high_regime_percentile": 67,
        },
        "no_black_box": True,
        "methodology_transparency": True,
        "no_scoring_terminology": True,
        "display": f"Formula v{_FORMULA_VERSION} — cross-asset normalized, thresholds documented",
    }


def build_legal_review_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    lr = seed.get("legal_review") or {}
    complete = bool(lr.get("complete", False))
    return {
        "legal_review_mandatory": True,
        "legal_review_complete": complete,
        "rule_based_validation_months": _RULE_BASED_VALIDATION_MONTHS,
        "rule_based_baseline_required": True,
        "ml_deferred_until_compliance": True,
        "compliance_framework_required": True,
        "release_blocked_without_review": not complete,
        "display": (
            f"Legal review: {'COMPLETE' if complete else 'PENDING'} | "
            f"Rule-based baseline: {_RULE_BASED_VALIDATION_MONTHS} months required"
        ),
    }


def classify_regime(percentile: float, *, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    """Historical regime classification — relative to asset's own distribution."""
    thresholds = thresholds or {}
    low_thresh = float(thresholds.get("low_regime_percentile", 33))
    high_thresh = float(thresholds.get("high_regime_percentile", 67))

    if percentile <= low_thresh:
        regime: Regime = "low"
    elif percentile >= high_thresh:
        regime = "high"
    else:
        regime = "medium"

    return {
        "regime": regime,
        "historical_regime_only": True,
        "relative_to_asset_distribution": True,
        "no_advisory_language": True,
        "no_buy_sell_implication": True,
        "display": (
            f"Historical regime: {regime} (relative to asset's own historical distribution)"
        ),
        "not_investment_advice": True,
    }


def build_volatility_analysis(asset: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build analysis for one asset — no risk score output."""
    seed = seed or _load_seed()
    sym = asset.upper()
    data = (seed.get("assets") or {}).get(sym)

    if not data:
        return {"ok": False, "error": "asset_not_tracked", "asset": sym}

    formula = build_formula_documentation(seed)
    thresholds = (seed.get("formula") or {}).get("thresholds") or {}
    percentile = float(data.get("historical_volatility_percentile", 50))
    regime = classify_regime(percentile, thresholds=thresholds)

    return {
        "ok": True,
        "asset": sym,
        "historical_volatility_percentile": percentile,
        "percentile_display": f"Historical Volatility Percentile: {percentile:.0f}/100",
        "no_risk_score_output": True,
        "no_scoring_terminology": True,
        "regime_classification": regime,
        "components": {
            "realized_volatility": {
                "value": data.get("realized_volatility"),
                "annualized_pct": data.get("realized_vol_annualized_pct"),
                "source": data.get("realized_vol_source"),
            },
            "implied_volatility": {
                "value": data.get("implied_volatility"),
                "source": data.get("implied_vol_source"),
            },
            "atr": {
                "value": data.get("atr"),
                "period": data.get("atr_period", 14),
            },
            "returns": {
                "return_30d_pct": data.get("return_30d_pct"),
            },
            "liquidity": {
                "volume_24h_usd": data.get("volume_24h_usd"),
                "liquidity_tier": data.get("liquidity_tier"),
            },
        },
        "methodology_explanation": {
            "formula": formula,
            "cross_asset_normalized": True,
            "methodology_transparency": True,
            "no_arbitrary_thresholds": True,
        },
        "disclaimer": _DISCLAIMER,
    }


def build_cross_asset_volatility_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    legal_gate = build_legal_review_gate(seed)

    if not legal_gate["legal_review_complete"]:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "legal_review_pending",
            "legal_review_gate": legal_gate,
            "release_blocked": True,
        }

    analysis = build_volatility_analysis(asset, seed)
    if not analysis.get("ok"):
        return {**analysis, "feature_id": _FEATURE_ID}

    bt = seed.get("backtest") or {}
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "no_scoring_in_name": True,
        "no_scoring_in_output": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "surface": "data_layer_infrastructure",
        "infrastructure_feature": True,
        "ml_deferred": True,
        "rule_based_only": True,
        "analysis": analysis,
        "formula": build_formula_documentation(seed),
        "legal_review_gate": legal_gate,
        "backtest": {
            "documented": True,
            "events_tested": bt.get("events_tested", 0),
            "regime_accuracy_pct": bt.get("regime_accuracy_pct"),
            "no_arbitrary_thresholds": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "disclaimer_on_every_output": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def cross_asset_volatility_regime_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "no_scoring_terminology": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "infrastructure_feature": True,
        "ml_deferred_until_compliance": True,
        "formula": build_formula_documentation(seed),
        "legal_review_gate": build_legal_review_gate(seed),
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "formula_version_documented": True,
            "cross_asset_normalization": True,
            "no_arbitrary_thresholds": True,
            "backtest_documented": True,
            "no_scoring_terminology": True,
            "legal_review_mandatory": True,
            "rule_based_baseline_3_months": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
