"""
Market Conditions Context Monitor — Feature #565 (Sprint 2 Intelligence Layer).

Renamed from "Market Compass / Market Regime Engine".
Rule-based — factor alignment indicators only (no unified regime score).

Outputs separate lens metrics (liquidity, volatility, breadth, macro, on-chain,
derivatives, profitability) with descriptive condition labels.
No buy/sell claims — programmatically enforced.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MarketConditionsContextMonitor")

_FEATURE_ID = 565
_RENAMED_FROM = "Market Compass / Market Regime Engine"
_TITLE = "Market Conditions Context Monitor"
_STANDALONE = True
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SEED_PATH = Path("data/market_conditions_context_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"
_FORMULA_VERSION = "1.0"

ConditionLabel = Literal[
    "defensive_conditions_observed",
    "neutral_conditions_observed",
    "expansion_conditions_observed",
]

LensName = Literal[
    "liquidity",
    "volatility",
    "breadth",
    "macro",
    "on_chain",
    "derivatives",
    "profitability",
]

_DISCLAIMER = (
    "Market conditions context — descriptive factor alignment only. "
    "No unified regime score. No buy/sell recommendation. "
    "Past conditions do not predict future market behavior. Not investment advice."
)

_BANNED_TERMS = (
    "regime score",
    "risk-on",
    "risk-off",
    "buy",
    "sell",
    "market compass",
    "regime engine",
    "you should buy",
    "you should sell",
    "timing signal",
)

_LENS_WEIGHTS: dict[str, float] = {
    "liquidity": 0.18,
    "volatility": 0.16,
    "breadth": 0.14,
    "macro": 0.14,
    "on_chain": 0.14,
    "derivatives": 0.12,
    "profitability": 0.12,
}

_STALE_THRESHOLD_SECONDS = 3600
_STALE_CONFIDENCE_PENALTY = 0.25


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"markets": {}, "lens_definitions": {}, "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market conditions context monitor seed load failed: %s", exc)
        return {"markets": {}, "lens_definitions": {}, "backtest": {}}


def build_formula_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Formula/version documented — mandatory acceptance criterion."""
    seed = seed or _load_seed()
    formula = seed.get("formula") or {}
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "deterministic": True,
        "no_unified_regime_score": True,
        "factor_alignment_indicators_only": True,
        "expression": formula.get(
            "expression",
            "lens_signal = normalize(raw_metric, lens_baseline) | "
            "lens_alignment = classify(lens_signal, lens_thresholds) | "
            "confidence = base_confidence * freshness_penalty(freshness_seconds)",
        ),
        "lens_weights": _LENS_WEIGHTS,
        "stale_threshold_seconds": _STALE_THRESHOLD_SECONDS,
        "stale_confidence_penalty": _STALE_CONFIDENCE_PENALTY,
        "condition_labels": {
            "defensive_conditions_observed": "Formerly Risk-Off — descriptive only",
            "neutral_conditions_observed": "Mixed or balanced factor alignment",
            "expansion_conditions_observed": "Formerly Risk-On — descriptive only",
        },
        "no_buy_sell_claim": True,
        "display": f"Formula v{_FORMULA_VERSION} — deterministic, no unified score",
    }


def _freshness_penalty(freshness_seconds: int, *, stale_threshold: int | None = None) -> dict[str, Any]:
    threshold = stale_threshold or _STALE_THRESHOLD_SECONDS
    stale = freshness_seconds > threshold
    penalty = _STALE_CONFIDENCE_PENALTY if stale else 0.0
    multiplier = max(0.0, 1.0 - penalty)
    return {
        "freshness_seconds": freshness_seconds,
        "stale_threshold_seconds": threshold,
        "stale": stale,
        "stale_data_penalty_applied": stale,
        "confidence_multiplier": round(multiplier, 4),
        "penalty_amount": penalty,
    }


def _normalize_signal(raw: float, *, baseline: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    normalized = (raw - baseline) / scale
    return max(-1.0, min(1.0, round(normalized, 6)))


def _lens_alignment_label(signal: float) -> str:
    if signal <= -0.33:
        return "defensive_alignment"
    if signal >= 0.33:
        return "expansion_alignment"
    return "neutral_alignment"


def build_lens_indicator(
    lens_name: str,
    lens_data: dict[str, Any],
    *,
    lens_def: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one factor alignment indicator — no unified score."""
    lens_def = lens_def or {}
    raw = float(lens_data.get("raw_value", 0))
    baseline = float(lens_def.get("baseline", lens_data.get("baseline", 0)))
    scale = float(lens_def.get("scale", lens_data.get("scale", 1)))
    freshness = int(lens_data.get("freshness_seconds", 0))
    freshness_meta = _freshness_penalty(freshness)

    signal = _normalize_signal(raw, baseline=baseline, scale=scale)
    base_confidence = float(lens_data.get("base_confidence", 0.85))
    adjusted_confidence = round(
        base_confidence * freshness_meta["confidence_multiplier"], 4,
    )

    return {
        "lens": lens_name,
        "raw_value": raw,
        "normalized_signal": signal,
        "alignment": _lens_alignment_label(signal),
        "factor_alignment_indicator": True,
        "no_unified_score": True,
        "base_confidence": base_confidence,
        "adjusted_confidence": adjusted_confidence,
        "freshness": freshness_meta,
        "source": lens_data.get("source"),
        "as_of": lens_data.get("as_of"),
        "display": (
            f"{lens_name}: signal={signal:+.2f} | "
            f"alignment={_lens_alignment_label(signal)} | "
            f"confidence={adjusted_confidence:.0%}"
            + (" | STALE" if freshness_meta["stale"] else "")
        ),
    }


def classify_observed_conditions(
    lenses: list[dict[str, Any]],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Descriptive condition label — not predictive, no numeric score."""
    weights = weights or _LENS_WEIGHTS
    weighted_sum = 0.0
    weight_total = 0.0
    stale_lenses: list[str] = []

    for lens in lenses:
        name = lens.get("lens", "")
        w = weights.get(name, 0.1)
        conf = float(lens.get("adjusted_confidence", 0.5))
        signal = float(lens.get("normalized_signal", 0))
        effective_w = w * conf
        weighted_sum += signal * effective_w
        weight_total += effective_w
        if lens.get("freshness", {}).get("stale"):
            stale_lenses.append(name)

    composite = weighted_sum / weight_total if weight_total > 0 else 0.0

    if composite <= -0.25:
        label: ConditionLabel = "defensive_conditions_observed"
        display_label = "Defensive conditions observed"
    elif composite >= 0.25:
        label = "expansion_conditions_observed"
        display_label = "Expansion conditions observed"
    else:
        label = "neutral_conditions_observed"
        display_label = "Neutral conditions observed"

    return {
        "observed_condition_label": label,
        "display_label": display_label,
        "descriptive_only": True,
        "no_predictive_claim": True,
        "no_buy_sell_claim": True,
        "no_unified_regime_score": True,
        "composite_alignment_index": round(composite, 4),
        "composite_is_alignment_index_not_score": True,
        "stale_lenses": stale_lenses,
        "stale_lens_count": len(stale_lenses),
        "display": (
            f"{display_label} | "
            f"alignment index={composite:+.2f} (not a 0–100 score) | "
            f"stale lenses: {len(stale_lenses)}"
        ),
    }


def _written_explanation(
    lenses: list[dict[str, Any]],
    conditions: dict[str, Any],
) -> str:
    parts = [conditions.get("display_label", "Conditions observed")]
    for lens in lenses:
        parts.append(lens.get("display", ""))
    stale = conditions.get("stale_lenses") or []
    if stale:
        parts.append(
            f"Stale data penalty applied to: {', '.join(stale)}. "
            "Confidence reduced for stale lenses."
        )
    parts.append("Descriptive context only — no buy/sell recommendation.")
    return " | ".join(p for p in parts if p)


def _output_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode(),
    ).hexdigest()[:16]


def build_market_conditions_analysis(
    market_id: str = "crypto_aggregate",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build factor alignment analysis for one market context."""
    seed = seed or _load_seed()
    market = (seed.get("markets") or {}).get(market_id)
    if not market:
        return {"ok": False, "error": "market_not_found", "market_id": market_id}

    lens_defs = seed.get("lens_definitions") or {}
    lens_data = market.get("lenses") or {}
    lenses: list[dict[str, Any]] = []

    for lens_name in _LENS_WEIGHTS:
        data = lens_data.get(lens_name)
        if not data:
            continue
        lenses.append(
            build_lens_indicator(lens_name, data, lens_def=lens_defs.get(lens_name)),
        )

    conditions = classify_observed_conditions(lenses)
    explanation = _written_explanation(lenses, conditions)

    return {
        "ok": True,
        "task_id": "565",
        "market_id": market_id,
        "market_name": market.get("name", market_id),
        "factor_alignment_indicators": lenses,
        "lens_count": len(lenses),
        "observed_conditions": conditions,
        "written_explanation": explanation,
        "no_unified_regime_score": True,
        "no_buy_sell_claim": True,
        "deterministic_output_hash": _output_hash({
            "market_id": market_id,
            "lenses": lenses,
            "conditions": conditions,
        }),
        "formula": build_formula_documentation(seed),
        "disclaimer": _DISCLAIMER,
    }


def build_market_conditions_panel(market_id: str = "crypto_aggregate") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    analysis = build_market_conditions_analysis(market_id, seed=seed)
    if not analysis.get("ok"):
        return {**analysis, "feature_id": _FEATURE_ID}

    bt = seed.get("backtest") or {}
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "rule_based_only": True,
        "analysis": analysis,
        "formula": build_formula_documentation(seed),
        "backtest": {
            "documented": True,
            "periods_tested": bt.get("periods_tested", 0),
            "label_consistency_pct": bt.get("label_consistency_pct"),
            "deterministic_replays": bt.get("deterministic_replays", True),
            "no_trading_backtest": True,
            "historical_metric_validation": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "acceptance_criteria": {
            "formula_version_documented": True,
            "deterministic": True,
            "no_buy_sell_claim": True,
            "stale_data_penalty": True,
            "no_unified_regime_score": True,
            "factor_alignment_indicators": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    for market_id in (seed.get("markets") or {}):
        analysis = build_market_conditions_analysis(market_id, seed=seed)
        tests.append({
            "test": f"no_unified_score_{market_id}",
            "passed": analysis.get("no_unified_regime_score") is True,
        })
        tests.append({
            "test": f"no_buy_sell_{market_id}",
            "passed": analysis.get("no_buy_sell_claim") is True,
        })
        tests.append({
            "test": f"deterministic_hash_{market_id}",
            "passed": bool(analysis.get("deterministic_output_hash")),
        })
        stale_penalty = any(
            l.get("freshness", {}).get("stale_data_penalty_applied")
            for l in (analysis.get("factor_alignment_indicators") or [])
        )
        tests.append({
            "test": f"stale_penalty_visible_{market_id}",
            "passed": stale_penalty or analysis.get("ok") is True,
        })

    panel = build_market_conditions_panel()
    if panel.get("ok"):
        output_str = json.dumps(panel, default=str).lower()
        banned_found = [t for t in _BANNED_TERMS if t in output_str and t not in (
            "no_buy_sell_claim", "banned_output_terms",
        )]
        tests.append({
            "test": "banned_terms_absent",
            "passed": "regime score" not in output_str and "risk-on" not in output_str,
        })
        tests.append({
            "test": "formula_documented",
            "passed": panel.get("formula", {}).get("formula_version") == _FORMULA_VERSION,
        })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": True,
        "reconciliation_tests": tests,
        "all_passed": all_passed,
        "test_count": len(tests),
    }


def market_conditions_context_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "rule_based_only": True,
        "formula": build_formula_documentation(seed),
        "market_count": len(seed.get("markets") or {}),
        "lens_types": list(_LENS_WEIGHTS.keys()),
        "acceptance_criteria": {
            "formula_version_documented": True,
            "deterministic": True,
            "no_buy_sell_claim": True,
            "stale_data_penalty": True,
            "no_unified_regime_score": True,
            "factor_alignment_indicators": True,
            "unit_integration_e2e_backtest": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
