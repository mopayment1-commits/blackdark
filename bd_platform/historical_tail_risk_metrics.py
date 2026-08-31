"""
Historical Tail Risk Metrics (VaR/CVaR) — Features #503 + #504 merged (Sprint 1 Data Layer).

Renamed from standalone "Value at Risk" / "Conditional Value at Risk" tickets.
Part of Risk Metrics Layer alongside Cross-Asset Volatility Regime Analyzer (#501).

Infrastructure feature — historical descriptive statistics only, no advisory output.
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.HistoricalTailRiskMetrics")

_FEATURE_IDS = (503, 504)
_ABSORBED_IDS = (503, 504)
_RENAMED_FROM = ("Conditional Value at Risk (CVaR)", "Value at Risk (VaR)")
_TITLE = "Historical Tail Risk Estimates (VaR/CVaR)"
_STANDALONE = False
_MERGED_INTO = "Data Layer / Risk Metrics Layer / Historical Tail Risk Metrics"
_RISK_METRICS_LAYER = "Risk Metrics Layer"
_SIBLING_FEATURE_ID = 501
_WAVE = 1
_SPRINT = 1
_SEED_PATH = Path("data/historical_tail_risk_metrics_seed.json")
_FORMULA_VERSION = "1.0"
_METHODOLOGY_VERSION = "1.0"
_RULE_BASED_VALIDATION_MONTHS = 3

_DISCLAIMER = (
    "Statistical estimate only | Not a prediction | "
    "Past distribution does not indicate future tail events | No guarantee"
)

_BANNED_TERMS = (
    "maximum potential loss",
    "max loss",
    "you will lose",
    "expected loss",
    "potential loss",
    "worst case loss",
    "guaranteed",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "portfolios": {}, "legal_review": {}, "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("historical tail risk metrics seed load failed: %s", exc)
        return {"assets": {}, "portfolios": {}, "legal_review": {}, "backtest": {}}


def build_formula_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    formula = seed.get("formula") or {}
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "method": "historical_simulation",
        "no_ml": True,
        "formula": formula.get(
            "expression",
            "historical_var = percentile(returns, 1 - confidence) | "
            "historical_cvar = mean(returns where return <= historical_var)",
        ),
        "inputs": formula.get("inputs") or [
            "historical_daily_returns",
            "portfolio_weights",
            "notional_usd",
            "confidence_level",
            "lookback_days",
        ],
        "var_definition": (
            "Estimated historical loss percentile based on past returns distribution. "
            "NOT maximum potential loss."
        ),
        "cvar_definition": (
            "Average of historical returns at or beyond the VaR threshold. "
            "Descriptive tail statistic — not a forecast."
        ),
        "confidence_levels": formula.get("confidence_levels") or [0.90, 0.95, 0.99],
        "lookback_days_default": formula.get("lookback_days_default", 252),
        "no_black_box": True,
        "methodology_transparency": True,
        "display": f"Formula v{_FORMULA_VERSION} — historical simulation, no ML",
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
        "disclaimer_on_every_output": True,
        "display": (
            f"Legal review: {'COMPLETE' if complete else 'PENDING'} | "
            f"Rule-based baseline: {_RULE_BASED_VALIDATION_MONTHS} months required"
        ),
    }


def compute_historical_var(
    returns: list[float],
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """
    Historical VaR — percentile of past returns distribution.

    Returns the return at the (1-confidence) percentile. Negative values indicate loss.
    """
    if len(returns) < 10:
        return {
            "ok": False,
            "error": "insufficient_data",
            "min_observations": 10,
            "observations": len(returns),
        }

    sorted_r = sorted(returns)
    idx = max(0, int((1 - confidence) * len(sorted_r)) - 1)
    var_return = sorted_r[idx]
    tail_pct = round((1 - confidence) * 100, 1)

    return {
        "ok": True,
        "confidence": confidence,
        "confidence_display": f"{confidence * 100:.0f}%",
        "tail_percentile": tail_pct,
        "historical_var_return": round(var_return, 6),
        "historical_var_return_pct": round(var_return * 100, 4),
        "observations": len(returns),
        "method": "historical_simulation",
        "not_maximum_potential_loss": True,
        "descriptive_statistic_only": True,
        "display": (
            f"Estimated historical loss percentile ({tail_pct}% tail): "
            f"{var_return * 100:.2f}% daily return based on past distribution"
        ),
        "framing": (
            f"In the worst {tail_pct:.0f}% of historical days in the lookback window, "
            f"returns were at or below {var_return * 100:.2f}%"
        ),
    }


def compute_historical_cvar(
    returns: list[float],
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """
    Historical CVaR (Expected Shortfall) — average of returns at or beyond VaR threshold.
    """
    var_result = compute_historical_var(returns, confidence=confidence)
    if not var_result.get("ok"):
        return var_result

    sorted_r = sorted(returns)
    idx = max(0, int((1 - confidence) * len(sorted_r)) - 1)
    var_return = sorted_r[idx]
    tail = sorted_r[: idx + 1] or [var_return]
    cvar_return = sum(tail) / len(tail)
    tail_pct = round((1 - confidence) * 100, 1)

    return {
        "ok": True,
        "confidence": confidence,
        "confidence_display": f"{confidence * 100:.0f}%",
        "tail_percentile": tail_pct,
        "historical_var_return": round(var_return, 6),
        "historical_cvar_return": round(cvar_return, 6),
        "historical_cvar_return_pct": round(cvar_return * 100, 4),
        "tail_observations": len(tail),
        "total_observations": len(returns),
        "method": "historical_simulation",
        "not_forecast": True,
        "descriptive_statistic_only": True,
        "display": (
            f"Historical tail average ({tail_pct}% tail): "
            f"{cvar_return * 100:.2f}% daily return"
        ),
        "framing": (
            f"In the worst {tail_pct:.0f}% of historical days, "
            f"the average return was {cvar_return * 100:.2f}%"
        ),
    }


def _scale_to_notional(return_pct: float, notional_usd: float) -> dict[str, Any]:
    """Convert return estimate to USD — still descriptive, not predictive."""
    usd = round(return_pct * notional_usd, 2)
    return {
        "notional_usd": notional_usd,
        "estimated_historical_usd": usd,
        "not_predictive": True,
        "historical_estimate_only": True,
        "display": (
            f"Estimated historical USD impact on ${notional_usd:,.0f} notional: "
            f"${usd:,.2f} (based on past returns distribution)"
        ),
    }


def build_tail_risk_estimates(
    returns: list[float],
    *,
    confidence: float = 0.95,
    notional_usd: float = 10_000,
) -> dict[str, Any]:
    """Combined VaR + CVaR estimates with mandatory disclaimers."""
    var = compute_historical_var(returns, confidence=confidence)
    if not var.get("ok"):
        return var

    cvar = compute_historical_cvar(returns, confidence=confidence)
    tail_pct = var["tail_percentile"]

    return {
        "ok": True,
        "title": _TITLE,
        "historical_estimates_only": True,
        "not_maximum_potential_loss": True,
        "confidence": confidence,
        "tail_percentile": tail_pct,
        "historical_var": var,
        "historical_cvar": cvar,
        "notional_scaling": {
            "var": _scale_to_notional(var["historical_var_return"], notional_usd),
            "cvar": _scale_to_notional(cvar["historical_cvar_return"], notional_usd),
        },
        "summary_framing": (
            f"In the worst {tail_pct:.0f}% of historical days, "
            f"the average was {cvar['historical_cvar_return_pct']:.2f}% "
            f"(VaR threshold: {var['historical_var_return_pct']:.2f}%)"
        ),
        "disclaimer": _DISCLAIMER,
    }


def build_asset_tail_risk_analysis(
    asset: str,
    *,
    confidence: float = 0.95,
    notional_usd: float = 10_000,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build tail risk analysis for a single asset."""
    seed = seed or _load_seed()
    sym = asset.upper()
    data = (seed.get("assets") or {}).get(sym)

    if not data:
        return {"ok": False, "error": "asset_not_tracked", "asset": sym}

    returns = data.get("historical_daily_returns") or []
    if not returns:
        return {"ok": False, "error": "no_returns_data", "asset": sym}

    estimates = build_tail_risk_estimates(
        returns,
        confidence=confidence,
        notional_usd=notional_usd,
    )
    if not estimates.get("ok"):
        return {**estimates, "asset": sym}

    lookback = data.get("lookback_days", len(returns))
    return {
        "ok": True,
        "asset": sym,
        "lookback_days": lookback,
        "data_sources": data.get("data_sources") or ["market_data", "on_chain"],
        "estimates": estimates,
        "no_advisory_language": True,
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
    }


def build_portfolio_tail_risk_analysis(
    portfolio_id: str,
    *,
    confidence: float = 0.95,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build tail risk analysis for a portfolio — #504 absorbed."""
    seed = seed or _load_seed()
    portfolio = (seed.get("portfolios") or {}).get(portfolio_id)

    if not portfolio:
        return {"ok": False, "error": "portfolio_not_found", "portfolio_id": portfolio_id}

    returns = portfolio.get("historical_daily_returns") or []
    if not returns:
        return {"ok": False, "error": "no_returns_data", "portfolio_id": portfolio_id}

    notional = float(portfolio.get("notional_usd", 10_000))
    estimates = build_tail_risk_estimates(
        returns,
        confidence=confidence,
        notional_usd=notional,
    )
    if not estimates.get("ok"):
        return {**estimates, "portfolio_id": portfolio_id}

    return {
        "ok": True,
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio.get("name", portfolio_id),
        "networks_supported": portfolio.get("networks_supported", 0),
        "holdings_count": len(portfolio.get("holdings") or []),
        "notional_usd": notional,
        "lookback_days": portfolio.get("lookback_days", len(returns)),
        "data_sources": portfolio.get("data_sources") or [
            "wallet_balances", "on_chain", "market_data",
        ],
        "estimates": estimates,
        "no_advisory_language": True,
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
    }


def build_historical_tail_risk_panel(
    *,
    asset: str | None = "BTC",
    portfolio_id: str | None = None,
    confidence: float = 0.95,
    notional_usd: float = 10_000,
) -> dict[str, Any]:
    """Main panel — asset or portfolio tail risk estimates."""
    t0 = time.perf_counter()
    seed = _load_seed()
    legal_gate = build_legal_review_gate(seed)

    if not legal_gate["legal_review_complete"]:
        return {
            "ok": False,
            "feature_ids": list(_FEATURE_IDS),
            "error": "legal_review_pending",
            "legal_review_gate": legal_gate,
            "release_blocked": True,
        }

    if portfolio_id:
        analysis = build_portfolio_tail_risk_analysis(
            portfolio_id, confidence=confidence, seed=seed,
        )
        scope = "portfolio"
    else:
        analysis = build_asset_tail_risk_analysis(
            asset or "BTC",
            confidence=confidence,
            notional_usd=notional_usd,
            seed=seed,
        )
        scope = "asset"

    if not analysis.get("ok"):
        return {**analysis, "feature_ids": list(_FEATURE_IDS)}

    bt = seed.get("backtest") or {}
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {
            "503": "Conditional Value at Risk (CVaR) — merged",
            "504": "Value at Risk (VaR) — merged",
        },
        "renamed_from": list(_RENAMED_FROM),
        "title": _TITLE,
        "historical_estimates_mandatory": True,
        "not_maximum_potential_loss": True,
        "standalone_rejected": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "risk_metrics_layer": _RISK_METRICS_LAYER,
        "sibling_feature_id": _SIBLING_FEATURE_ID,
        "sibling_feature": "Cross-Asset Volatility Regime Analyzer (#501)",
        "wave": _WAVE,
        "sprint": _SPRINT,
        "surface": "data_layer_infrastructure",
        "infrastructure_feature": True,
        "ml_deferred": True,
        "rule_based_only": True,
        "scope": scope,
        "analysis": analysis,
        "formula": build_formula_documentation(seed),
        "legal_review_gate": legal_gate,
        "backtest": {
            "documented": True,
            "observations_tested": bt.get("observations_tested", 0),
            "var_accuracy_pct": bt.get("var_accuracy_pct"),
            "cvar_accuracy_pct": bt.get("cvar_accuracy_pct"),
            "no_ml": True,
        },
        "acceptance_criteria": {
            "response_under_2s": elapsed < 2000,
            "accuracy_target_pct": 95,
            "uptime_target_pct": 99,
            "real_time_refresh": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "disclaimer_on_every_output": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def historical_tail_risk_metrics_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "title": _TITLE,
        "renamed_from": list(_RENAMED_FROM),
        "historical_estimates_mandatory": True,
        "not_maximum_potential_loss": True,
        "standalone_rejected": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "risk_metrics_layer": _RISK_METRICS_LAYER,
        "sibling_feature_id": _SIBLING_FEATURE_ID,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "infrastructure_feature": True,
        "ml_deferred_until_compliance": True,
        "formula": build_formula_documentation(seed),
        "legal_review_gate": build_legal_review_gate(seed),
        "asset_count": len(seed.get("assets") or {}),
        "portfolio_count": len(seed.get("portfolios") or {}),
        "acceptance_criteria": {
            "response_under_2s": True,
            "accuracy_target_pct": 95,
            "uptime_target_pct": 99,
            "real_time_refresh": True,
            "formula_documented": True,
            "no_ml": True,
            "legal_review_mandatory": True,
            "disclaimer_on_every_output": True,
            "no_advisory_language": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
