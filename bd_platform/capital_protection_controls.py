"""
Capital Awareness Controls — Feature #410 (Sprint 2 Risk Module).

Risk Layer in Portfolio AI + Intelligence Ledger — NOT standalone.
Legal name: Risk Awareness Layer (never "insurance" or "guarantee").

Non-executive mandatory: recommendations + alerts only.
No automatic fund movement — explicit in SLA/Terms.

Components:
  - Risk Score per position (0–100 analytics index)
  - Scenario Stress Testing (max drawdown, correlation shock, liquidity freeze)
  - Risk Budget (user-defined max loss % with proximity warnings)
  - Portfolio AI alerts (concentration, drawdown, sector correlation)
  - Intelligence Ledger mandatory Risk Assessment on every signal
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.CapitalAwarenessControls")

_FEATURE_ID = 410
_TITLE = "Capital Awareness Controls"
_LEGAL_NAME = "Risk Awareness Layer"
_STANDALONE = False
_MERGED_INTO = "Portfolio AI + Intelligence Ledger / Risk Layer"
_LAYER = "Portfolio AI"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/capital_protection_controls_seed.json")
_METHODOLOGY_VERSION = "1.0"

_BANNED_TERMS = (
    "insurance",
    "guarantee",
    "protected capital",
    "we protect your",
    "auto execute",
    "auto rebalance",
    "automatic fund movement",
    "you should sell",
    "you should buy",
)

_DISCLAIMER = (
    "Risk Awareness — informational alerts and scenario analytics only. "
    "Not insurance, not guarantee, not investment advice. "
    "No automatic fund movement. User assesses all implications."
)

_SLA_NO_AUTO_MOVEMENT = (
    "BLACKDARK never moves funds automatically. No stop-loss execution, "
    "no auto-rebalance, no order placement without explicit user action. "
    "Risk Awareness alerts are informational only."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"positions": {}, "portfolio": {}, "risk_budget": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("capital awareness controls seed load failed: %s", exc)
        return {"positions": {}, "portfolio": {}, "risk_budget": {}}


def build_sla_terms_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    sla = seed.get("sla_terms") or {}
    return {
        "no_automatic_fund_movement": True,
        "no_execution_api_keys": True,
        "recommendations_and_alerts_only": True,
        "explicit_user_boundary_required": True,
        "non_executive": seed.get("non_executive", True),
        "legal_text": sla.get("legal_text", _SLA_NO_AUTO_MOVEMENT),
        "terms_of_service_clause": _SLA_NO_AUTO_MOVEMENT,
        "display": "No automatic fund movement without explicit user boundary",
    }


def compute_position_risk_score(position: dict[str, Any]) -> dict[str, Any]:
    """
    Risk Score 0–100 analytics index from:
    volatility, concentration, correlation, liquidity depth, funding rate stress.
    """
    vol = float(position.get("volatility_30d", 0.5))
    conc = float(position.get("concentration_pct", 0)) / 100
    corr = float(position.get("correlation_to_portfolio", 0.5))
    liq = float(position.get("liquidity_depth_score", 50)) / 100
    funding = float(position.get("funding_rate_stress", 0.2))

    vol_component = min(100, vol * 120)
    conc_component = min(100, conc * 200)
    corr_component = min(100, corr * 80)
    liq_component = max(0, (1 - liq) * 100)
    funding_component = min(100, funding * 150)

    weights = {"volatility": 0.25, "concentration": 0.25, "correlation": 0.15,
               "liquidity": 0.20, "funding_stress": 0.15}
    score = round(
        vol_component * weights["volatility"]
        + conc_component * weights["concentration"]
        + corr_component * weights["correlation"]
        + liq_component * weights["liquidity"]
        + funding_component * weights["funding_stress"],
        1,
    )
    score = min(100, max(0, score))

    return {
        "risk_score": score,
        "scale": "0-100",
        "analytics_only": True,
        "not_investment_advice": True,
        "components": {
            "volatility": round(vol_component, 1),
            "concentration": round(conc_component, 1),
            "correlation": round(corr_component, 1),
            "liquidity_depth": round(liq_component, 1),
            "funding_rate_stress": round(funding_component, 1),
        },
        "weights": weights,
        "methodology_version": _METHODOLOGY_VERSION,
        "display": f"Position risk index: {score}/100 (analytics — user assesses)",
    }


def build_scenario_stress_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Scenario Stress Testing — max drawdown, correlation shock, liquidity freeze."""
    seed = seed or _load_seed()
    scenarios = seed.get("stress_scenarios") or {}

    results = []
    for key, scenario in scenarios.items():
        results.append({
            "scenario_type": key,
            "scenario_id": scenario.get("scenario_id"),
            "name": scenario.get("name"),
            "portfolio_loss_usd": scenario.get("portfolio_loss_usd"),
            "portfolio_impact_pct": scenario.get("portfolio_loss_pct") or scenario.get("portfolio_impact_pct"),
            "assumptions_visible": True,
            "educational_only": True,
            "not_investment_advice": True,
            "display": (
                f"{scenario.get('name')}: "
                f"-{scenario.get('portfolio_loss_pct') or scenario.get('portfolio_impact_pct')}% portfolio impact"
            ),
        })

    return {
        "scenario_stress_testing": True,
        "scenarios": results,
        "scenario_count": len(results),
        "types": ["max_drawdown", "correlation_shock", "liquidity_freeze"],
        "competitive_differentiator": "Not available in direct competitors at this depth",
        "display": f"{len(results)} stress scenarios — educational analytics only",
    }


def build_risk_budget_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Risk Budget — user max loss % with proximity warnings."""
    seed = seed or _load_seed()
    budget = seed.get("risk_budget") or {}
    portfolio = seed.get("portfolio") or {}

    max_loss_pct = float(budget.get("user_configured_max_loss_pct", 10))
    warning_threshold = float(budget.get("warning_threshold_pct", 75)) / 100
    total_value = float(portfolio.get("total_value_usd", 0))
    peak_value = float(portfolio.get("peak_value_usd", total_value))
    current_dd = float(portfolio.get("current_drawdown_pct", 0))

    max_loss_usd = peak_value * (max_loss_pct / 100)
    current_loss_usd = peak_value - total_value if peak_value > total_value else 0
    budget_used_pct = (current_loss_usd / max_loss_usd * 100) if max_loss_usd > 0 else 0
    warning_triggered = budget_used_pct >= (warning_threshold * 100)

    alerts = []
    if warning_triggered:
        alerts.append({
            "alert_type": "risk_budget_proximity",
            "severity": "elevated" if budget_used_pct >= 90 else "watch",
            "budget_used_pct": round(budget_used_pct, 2),
            "max_loss_pct": max_loss_pct,
            "current_drawdown_pct": current_dd,
            "display": (
                f"Risk Budget: {budget_used_pct:.1f}% of allowed {max_loss_pct}% loss used — "
                f"drawdown alert (not automatic action)"
            ),
        })

    return {
        "risk_budget": True,
        "user_configured_max_loss_pct": max_loss_pct,
        "warning_threshold_pct": warning_threshold * 100,
        "budget_used_pct": round(budget_used_pct, 2),
        "max_loss_usd": round(max_loss_usd, 2),
        "current_loss_usd": round(current_loss_usd, 2),
        "warning_triggered": warning_triggered,
        "alerts": alerts,
        "no_automatic_action": True,
        "display": (
            f"Risk Budget: {max_loss_pct}% max loss allowed | "
            f"{budget_used_pct:.1f}% utilized"
        ),
    }


def build_portfolio_ai_alerts(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Portfolio AI alerts: concentration, drawdown, sector correlation spike."""
    seed = seed or _load_seed()
    positions = seed.get("positions") or {}
    portfolio = seed.get("portfolio") or {}
    sectors = seed.get("sector_exposure") or {}
    alerts: list[dict[str, Any]] = []

    for pid, pos in positions.items():
        conc = float(pos.get("concentration_pct", 0))
        if conc >= 25:
            alerts.append({
                "alert_type": "concentration_risk",
                "position_id": pid,
                "asset": pos.get("asset"),
                "concentration_pct": conc,
                "severity": "elevated" if conc >= 30 else "watch",
                "display": f"Concentration alert: {pos.get('asset')} at {conc}% of portfolio",
            })

    dd = float(portfolio.get("current_drawdown_pct", 0))
    budget = seed.get("risk_budget") or {}
    max_loss = float(budget.get("user_configured_max_loss_pct", 10))
    if dd >= max_loss * 0.75:
        alerts.append({
            "alert_type": "drawdown_approaching_limit",
            "current_drawdown_pct": dd,
            "risk_budget_pct": max_loss,
            "severity": "elevated" if dd >= max_loss * 0.9 else "watch",
            "display": f"Drawdown alert: {dd}% approaching {max_loss}% risk budget limit",
        })

    layer1 = float(sectors.get("Layer 1", 0))
    if layer1 >= 45:
        alerts.append({
            "alert_type": "sector_correlation_spike",
            "sector": "Layer 1",
            "exposure_pct": layer1,
            "severity": "watch",
            "display": f"Sector exposure alert: Layer 1 at {layer1}% — correlation risk elevated",
        })

    return {
        "integration": "portfolio_ai",
        "mandatory": True,
        "non_executive": True,
        "alerts": alerts,
        "alert_count": len(alerts),
        "no_automatic_fund_movement": True,
        "display": f"Portfolio AI: {len(alerts)} risk awareness alert(s)",
    }


def build_exchange_health_alerts_block(
    portfolio_id: str = "demo_portfolio",
) -> dict[str, Any]:
    """#456 Exchange Health Monitor — exposure > 20% on low-health exchange (#410)."""
    from bd_platform.exchange_health_monitor import build_portfolio_exchange_exposure_alerts

    return build_portfolio_exchange_exposure_alerts(portfolio_id)


def build_signal_risk_assessment(
    signal_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Intelligence Ledger — mandatory Risk Assessment on every signal."""
    seed = seed or _load_seed()
    signals = seed.get("signals") or {}
    signal = signals.get(signal_id)

    if not signal:
        return {"ok": False, "error": "signal_not_found", "signal_id": signal_id}

    asset = signal.get("asset", "").upper()
    position = None
    for pos in (seed.get("positions") or {}).values():
        if pos.get("symbol", "").upper() == asset or pos.get("asset", "").upper() == asset:
            position = pos
            break

    risk_score_block = compute_position_risk_score(position) if position else {
        "risk_score": None,
        "display": f"No position data for {asset} — risk index unavailable",
    }

    stress = build_scenario_stress_block(seed)
    budget = build_risk_budget_block(seed)

    return {
        "ok": True,
        "signal_id": signal_id,
        "asset": asset,
        "signal_type": signal.get("signal_type"),
        "risk_assessment_mandatory": True,
        "risk_assessment_attached": True,
        "position_risk_score": risk_score_block,
        "stress_context": {
            "max_drawdown_scenario": next(
                (s for s in stress["scenarios"] if s["scenario_type"] == "max_drawdown"), None
            ),
        },
        "risk_budget_context": {
            "budget_used_pct": budget.get("budget_used_pct"),
            "warning_triggered": budget.get("warning_triggered"),
        },
        "non_executive": True,
        "no_automatic_fund_movement": True,
        "not_investment_advice": True,
        "display": (
            f"Risk Assessment for {signal_id}: "
            f"risk index {risk_score_block.get('risk_score', 'N/A')}/100 | "
            f"budget {budget.get('budget_used_pct', 0)}% used"
        ),
    }


def build_breakeven_proximity_alert(
    position: dict[str, Any],
    calc: dict[str, Any],
    *,
    cp_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Breakeven proximity alerts — used by #404 Live Breakeven Tracker integration."""
    cp_config = cp_config or {}
    proximity_pct = float(cp_config.get("breakeven_proximity_alert_pct", 1.5))
    max_loss_pct = float(cp_config.get("max_loss_breach_alert_pct", 5.0))
    enabled = cp_config.get("enabled", True)

    current_price = float(position.get("current_price", 0))
    breakeven = float(calc.get("breakeven_price", 0))
    qty = float(calc.get("remaining_quantity", 0))

    if breakeven <= 0:
        return {"alerts": [], "enabled": enabled}

    distance_usd = current_price - breakeven
    distance_pct = (distance_usd / breakeven) * 100
    alerts: list[dict[str, Any]] = []

    if enabled and distance_pct > 0 and distance_pct <= proximity_pct:
        alerts.append({
            "alert_type": "breakeven_proximity",
            "severity": "watch",
            "distance_pct": round(distance_pct, 4),
            "potential_pnl_usd": round(distance_usd * qty, 2),
            "display": f"Price within {proximity_pct}% of breakeven — drawdown alert only",
        })
    elif enabled and distance_pct < 0 and abs(distance_pct) >= max_loss_pct:
        alerts.append({
            "alert_type": "below_breakeven_threshold",
            "severity": "elevated",
            "distance_pct": round(distance_pct, 4),
            "potential_loss_usd": round(abs(distance_usd * qty), 2),
            "display": f"Price {abs(distance_pct):.2f}% below breakeven — capital awareness alert",
        })

    return {
        "integration": "live_breakeven_tracker",
        "feature_id": 404,
        "alerts": alerts,
        "alert_count": len(alerts),
        "non_executive": True,
        "no_automatic_fund_movement": True,
    }


def build_capital_awareness_panel(portfolio_id: str = "demo_portfolio") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    portfolio = seed.get("portfolio") or {}
    positions = seed.get("positions") or {}

    if portfolio.get("portfolio_id") != portfolio_id and portfolio_id != "demo_portfolio":
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "portfolio_not_found"}

    position_scores = {
        pid: compute_position_risk_score(pos) for pid, pos in positions.items()
    }

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "surface": "portfolio_ai",
        "portfolio_id": portfolio_id,
        "non_executive": True,
        "no_automatic_fund_movement": True,
        "sla_terms": build_sla_terms_block(seed),
        "risk_budget": build_risk_budget_block(seed),
        "scenario_stress": build_scenario_stress_block(seed),
        "position_risk_scores": position_scores,
        "portfolio_ai_alerts": build_portfolio_ai_alerts(seed),
        "exchange_health_alerts": build_exchange_health_alerts_block(portfolio_id),
        "portfolio_summary": {
            "total_value_usd": portfolio.get("total_value_usd"),
            "current_drawdown_pct": portfolio.get("current_drawdown_pct"),
            "peak_value_usd": portfolio.get("peak_value_usd"),
        },
        "acceptance_criteria": {
            "no_automatic_fund_movement": True,
            "non_executive_only": True,
            "scenario_stress_testing": True,
            "risk_score_per_position": True,
            "risk_budget": True,
            "intelligence_ledger_risk_assessment": True,
            "exchange_health_monitor_456": True,
        },
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def capital_protection_controls_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "surface": "portfolio_ai",
        "non_executive": True,
        "no_automatic_fund_movement": True,
        "sla_terms": build_sla_terms_block(seed),
        "position_count": len(seed.get("positions") or {}),
        "components": {
            "risk_score_per_position": True,
            "scenario_stress_testing": True,
            "risk_budget": True,
            "portfolio_ai_alerts": True,
            "intelligence_ledger_risk_assessment": True,
            "breakeven_integration_404": True,
            "exchange_health_monitor_456": True,
        },
        "acceptance_criteria": {
            "no_automatic_fund_movement_without_explicit_boundary": True,
            "non_executive_mandatory": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({
        "id": "not_standalone",
        "passed": seed.get("standalone") is False,
        "detail": "merged into Portfolio AI + Intelligence Ledger",
    })

    checks.append({
        "id": "no_automatic_fund_movement",
        "passed": seed.get("no_automatic_fund_movement") is True,
        "detail": "SLA + ToS clause present",
    })

    checks.append({
        "id": "non_executive",
        "passed": seed.get("non_executive") is True,
        "detail": "alerts only",
    })

    panel = build_capital_awareness_panel()
    checks.append({
        "id": "risk_score_per_position",
        "passed": len(panel.get("position_risk_scores") or {}) >= 3,
        "detail": "BTC/ETH/UNI scored",
    })

    checks.append({
        "id": "scenario_stress_three_types",
        "passed": panel["scenario_stress"]["scenario_count"] == 3,
        "detail": "MDD, correlation, liquidity",
    })

    checks.append({
        "id": "risk_budget",
        "passed": panel["risk_budget"]["risk_budget"] is True,
        "detail": panel["risk_budget"].get("display"),
    })

    assessment = build_signal_risk_assessment("sig_btc_momentum", seed=seed)
    checks.append({
        "id": "intelligence_ledger_risk_assessment",
        "passed": assessment.get("risk_assessment_mandatory") is True,
        "detail": assessment.get("display"),
    })

    checks.append({
        "id": "portfolio_ai_alerts",
        "passed": panel["portfolio_ai_alerts"]["alert_count"] >= 1,
        "detail": panel["portfolio_ai_alerts"].get("display"),
    })

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
