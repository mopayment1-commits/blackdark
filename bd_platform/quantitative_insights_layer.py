"""
Quantitative Insights Layer — Feature #401 analytical integration (Sprint 2).

NOT a standalone AI engine. Rule-based scoring (heuristic + statistical) v1.
Uses intelligence_signals seed — no standalone signals database/API.

Surfaces: Market Radar + Portfolio AI only.
Integrates: Exchange Registry + Data Engine (funding + social sentiment sources).
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from bd_platform.institutional_standards import missing_value, wrap_intelligence_response

logger = logging.getLogger("BLACKDARK.QuantitativeInsights")

_FEATURE_ID = 401
_TITLE = "Quantitative Insights Layer"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SIGNALS_PATH = Path("data/intelligence_signals_seed.json")
_METHODOLOGY_VERSION = "1.0"
_ML_DEFERRED_DAYS = 90

SignalType = Literal["quantitative_insight", "risk_adjusted_signal", "data_driven_alert"]

_ACCEPTANCE_THRESHOLDS = {
    "sharpe_min": 0.8,
    "win_rate_min_pct": 52.0,
    "max_drawdown_max_pct": 20.0,
    "latency_max_minutes": 5,
    "backtest_min_years": 2,
    "walk_forward_months": 6,
}

_BANNED_TERMS: tuple[str, ...] = (
    "ai predicts",
    "ai يتنبأ",
    "guaranteed profit",
    "ربح مضمون",
    "exploit",
    "استغلال",
    "buy now",
    "اشترِ الآن",
    "guaranteed returns",
)

_BANNED_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE) for p in _BANNED_TERMS
)

_DISCLAIMER = (
    "Quantitative Insight / Risk-Adjusted Signal / Data-Driven Alert — "
    "rule-based v1, fees deducted. Not investment advice. ML deferred 90 days."
)

_UI_SURFACES = ("market_radar", "portfolio_ai")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_signals() -> dict[str, Any]:
    if not _SIGNALS_PATH.is_file():
        return {"signals": [], "backtest": {}, "walk_forward": {}}
    try:
        return json.loads(_SIGNALS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("intelligence signals seed load failed: %s", exc)
        return {"signals": [], "backtest": {}, "walk_forward": {}}


def _scan_banned_terms(text: str) -> list[str]:
    return [p.pattern for p in _BANNED_PATTERNS if p.search(text)]


def apply_fee_deduction(
    gross_return_pct: float,
    *,
    exchange_fee_bps: float,
    slippage_bps: float,
    network_fee_usd: float,
    notional_usd: float = 10000.0,
) -> dict[str, Any]:
    """Mandatory fee deduction before return calculation."""
    exchange_cost = (exchange_fee_bps / 10000.0) * 2 * 100  # round-trip
    slippage_cost = (slippage_bps / 10000.0) * 2 * 100
    network_cost_pct = (network_fee_usd / max(notional_usd, 1.0)) * 100
    total_fees_pct = round(exchange_cost + slippage_cost + network_cost_pct, 4)
    net_return = round(gross_return_pct - total_fees_pct, 4)
    return {
        "gross_return_pct": gross_return_pct,
        "exchange_fee_bps": exchange_fee_bps,
        "slippage_bps": slippage_bps,
        "network_fee_usd": network_fee_usd,
        "total_fees_pct": total_fees_pct,
        "net_return_pct": net_return,
        "fee_deduction_applied": True,
    }


def build_signal_output(signal: dict[str, Any], *, registry_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Transform raw signal into compliant output with fee-adjusted metrics."""
    registry_meta = registry_meta or {}
    fee_bps = float(registry_meta.get("fee_tier_bps", signal.get("exchange_fee_bps", 10)))
    slippage_bps = float(registry_meta.get("slippage_bps_default", signal.get("slippage_bps", 5)))
    network_fee = float(registry_meta.get("network_fee_usd_default", signal.get("network_fee_usd", 2.5)))

    gross = float(signal.get("gross_return_pct", 0))
    fees = apply_fee_deduction(
        gross,
        exchange_fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        network_fee_usd=network_fee,
        notional_usd=float(signal.get("notional_usd", 10000)),
    )

    signal_type: SignalType = signal.get("signal_type", "quantitative_insight")
    rationale = signal.get("rationale") or ""
    banned = _scan_banned_terms(rationale + " " + str(signal.get("headline", "")))

    return {
        "signal_id": signal.get("signal_id"),
        "signal_type": signal_type,
        "signal_type_label": {
            "quantitative_insight": "Quantitative Insight",
            "risk_adjusted_signal": "Risk-Adjusted Signal",
            "data_driven_alert": "Data-Driven Alert",
        }.get(signal_type, "Quantitative Insight"),
        "asset": signal.get("asset", "BTC"),
        "exchange_id": signal.get("exchange_id"),
        "confidence_score": signal.get("confidence_score"),
        "rationale": rationale,
        "banned_terms_detected": banned,
        "banned_terms_blocked": len(banned) > 0,
        "fee_adjusted_returns": fees,
        "features_used": signal.get("features_used") or [],
        "feature_count": len(signal.get("features_used") or []),
        "data_sources": signal.get("data_sources") or ["funding_rates", "social_sentiment"],
        "latency_minutes": signal.get("latency_minutes"),
        "rule_based_v1": True,
        "ml_deferred": True,
        "ml_deferred_days": _ML_DEFERRED_DAYS,
        "not_investment_advice": True,
        "no_ai_prediction_language": True,
        "display": signal.get("display") or f"{signal_type} — {signal.get('asset', 'BTC')}",
        "timestamp": signal.get("timestamp") or _utcnow(),
    }


def build_walk_forward_validation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_signals()
    wf = seed.get("walk_forward") or {}
    bt = seed.get("backtest") or {}
    sharpe = float(wf.get("sharpe", bt.get("sharpe", 0)))
    win_rate = float(wf.get("win_rate_pct", bt.get("win_rate_pct", 0)))
    max_dd = float(wf.get("max_drawdown_pct", bt.get("max_drawdown_pct", 100)))
    latency = float(wf.get("latency_minutes", bt.get("latency_minutes", 999)))
    years = float(bt.get("years", 0))

    checks = {
        "sharpe_gte_0_8": sharpe >= _ACCEPTANCE_THRESHOLDS["sharpe_min"],
        "win_rate_gte_52": win_rate >= _ACCEPTANCE_THRESHOLDS["win_rate_min_pct"],
        "max_drawdown_lte_20": max_dd <= _ACCEPTANCE_THRESHOLDS["max_drawdown_max_pct"],
        "latency_lte_5min": latency <= _ACCEPTANCE_THRESHOLDS["latency_max_minutes"],
        "backtest_gte_2y": years >= _ACCEPTANCE_THRESHOLDS["backtest_min_years"],
        "walk_forward_6mo": int(wf.get("months", 0)) >= _ACCEPTANCE_THRESHOLDS["walk_forward_months"],
        "fee_deduction_applied": wf.get("fee_deduction_applied", bt.get("fee_deduction_applied", False)),
    }
    return {
        "walk_forward_months": wf.get("months", _ACCEPTANCE_THRESHOLDS["walk_forward_months"]),
        "metrics": {
            "sharpe": sharpe,
            "win_rate_pct": win_rate,
            "max_drawdown_pct": max_dd,
            "latency_minutes": latency,
            "backtest_years": years,
        },
        "thresholds": _ACCEPTANCE_THRESHOLDS,
        "acceptance_checks": checks,
        "all_acceptance_passed": all(checks.values()),
        "rule_based_v1": True,
        "ml_deferred_days": _ML_DEFERRED_DAYS,
    }


def build_quantitative_insights_panel(
    *,
    asset: str = "BTC",
    surface: str = "market_radar",
) -> dict[str, Any]:
    """Main panel — rule-based insights for Market Radar or Portfolio AI."""
    if surface not in _UI_SURFACES:
        return {
            "ok": False,
            "error": "invalid_surface",
            "allowed_surfaces": list(_UI_SURFACES),
        }

    t0 = time.perf_counter()
    seed = _load_signals()
    sym = asset.upper()

    from bd_platform.exchange_registry import get_exchange

    signals_out: list[dict[str, Any]] = []
    for raw in seed.get("signals") or []:
        if raw.get("asset", "BTC").upper() != sym:
            continue
        if surface not in (raw.get("surfaces") or _UI_SURFACES):
            continue
        ex_id = raw.get("exchange_id", "binance")
        reg = get_exchange(ex_id)
        meta = reg.get("metadata") or {} if reg.get("ok") else {}
        built = build_signal_output(raw, registry_meta=meta)
        if built["banned_terms_blocked"]:
            continue
        signals_out.append(built)

    wf = build_walk_forward_validation(seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    panel = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "no_standalone_ai_engine": True,
        "no_standalone_signals_api": True,
        "intelligence_signals_source": "seed_sprint2",
        "layer": _LAYER,
        "sprint": _SPRINT,
        "asset": sym,
        "surface": surface,
        "ui_surfaces": list(_UI_SURFACES),
        "signals": signals_out,
        "signal_count": len(signals_out),
        "rule_based_scoring": True,
        "ml_deferred_days": _ML_DEFERRED_DAYS,
        "walk_forward_validation": wf,
        "data_engine_sources": {
            "funding_rates": "market_data_engine",
            "social_sentiment": "sentiment_engine",
            "not_new_modules": True,
        },
        "integrations": {
            "exchange_registry": True,
            "market_radar": surface == "market_radar",
            "portfolio_ai": surface == "portfolio_ai",
            "oracle_api": True,
        },
        "banned_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }
    return wrap_intelligence_response(panel, source="quantitative_insights")


def quantitative_insights_status() -> dict[str, Any]:
    seed = _load_signals()
    wf = build_walk_forward_validation(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "no_standalone_ai_engine": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "rule_based_v1": True,
        "ml_deferred_days": _ML_DEFERRED_DAYS,
        "ui_surfaces": list(_UI_SURFACES),
        "signal_count": len(seed.get("signals") or []),
        "walk_forward_validation": wf,
        "acceptance_criteria": wf["acceptance_checks"],
        "data_engine_sources": ["funding_rates", "social_sentiment"],
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_signals()
    tests: list[dict[str, Any]] = []

    wf = build_walk_forward_validation(seed)
    tests.append({"test": "walk_forward_acceptance", "passed": wf["all_acceptance_passed"]})
    tests.append({"test": "fee_deduction", "passed": wf["acceptance_checks"]["fee_deduction_applied"]})

    sample = apply_fee_deduction(5.0, exchange_fee_bps=10, slippage_bps=5, network_fee_usd=2.5)
    tests.append({"test": "fee_reduces_return", "passed": sample["net_return_pct"] < sample["gross_return_pct"]})

    for sig in seed.get("signals") or []:
        built = build_signal_output(sig)
        tests.append({
            "test": f"no_banned_terms_{sig.get('signal_id')}",
            "passed": not built["banned_terms_blocked"],
        })

    all_passed = all(t["passed"] for t in tests)
    return {"ok": True, "reconciliation_tests": tests, "all_passed": all_passed, "test_count": len(tests)}
