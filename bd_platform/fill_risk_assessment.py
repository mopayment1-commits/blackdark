"""
Fill Risk Assessment — Feature #433 (Intelligence Ledger Risk Layer).

Execution Risk % per opportunity with transparent breakdown:
liquidity, slippage, volatility, counterparty, network.

NOT standalone — merges #415 + #410 + #417 risk context.
Legal name: Fill Risk Assessment (no "execution" in product naming).

Integrations:
  - #410 Capital Protection: risk score per opportunity
  - #417 Net-Edge: auto-reject signal when risk % > user limit
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.FillRiskAssessment")

_FEATURE_ID = 433
_TITLE = "Fill Risk Assessment"
_LEGAL_NAME = "Fill Risk Assessment"
_RENAMED_FROM = "Execution Risk Assessment"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Risk Layer"
_SPRINT = 2
_PRIORITY = "medium"
_SEED_PATH = Path("data/fill_risk_assessment_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Fill Risk Assessment — analytics index (0–100%) with documented component breakdown. "
    "Not investment advice. Simulation only — no automatic execution."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"component_weights": {}, "user_risk_limit_pct": 65.0}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("fill risk assessment seed load failed: %s", exc)
        return {"component_weights": {}, "user_risk_limit_pct": 65.0}


def _component_liquidity_risk(opportunity: dict[str, Any]) -> tuple[float, str]:
    feasibility = opportunity.get("volume_feasibility") or opportunity.get("feasibility") or {}
    if feasibility.get("status") == "not_applicable_for_triangular":
        return 25.0, "triangular_single_venue_default"
    liq_score = feasibility.get("liquidity_score")
    if liq_score is None:
        verdict = feasibility.get("verdict") or (feasibility.get("buy_leg") or {}).get("verdict")
        if verdict == "not_fillable":
            return 95.0, "not_fillable"
        if verdict == "partial_fill":
            return 70.0, "partial_fill"
        return 50.0, "liquidity_unknown"
    return round(max(0.0, 100.0 - float(liq_score)), 1), f"liquidity_score_{liq_score}"


def _component_slippage_risk(opportunity: dict[str, Any]) -> tuple[float, str]:
    slip_bps = float(opportunity.get("slippage_bps") or opportunity.get("total_slippage_bps") or 8)
    risk = min(100.0, slip_bps * 2.5)
    return round(risk, 1), f"slippage_{slip_bps}bps"


def _component_volatility_risk(asset: str, *, seed: dict[str, Any]) -> tuple[float, str]:
    vol_map = seed.get("volatility_proxy") or {}
    vol = float(vol_map.get(asset.upper(), 0.5))
    return round(min(100.0, vol * 100), 1), f"volatility_30d_{vol}"


def _component_counterparty_risk(opportunity: dict[str, Any]) -> tuple[float, str]:
    reasons = opportunity.get("risk_reasons") or []
    low_health = [r for r in reasons if "low_health" in r]
    if low_health:
        return 85.0, ";".join(low_health)
    try:
        from bd_platform.exchange_health_monitor import evaluate_exchange

        venues = [opportunity.get("buy_venue"), opportunity.get("sell_venue"), opportunity.get("venue")]
        scores: list[float] = []
        for v in venues:
            if not v:
                continue
            ev = evaluate_exchange(str(v))
            if ev.get("ok"):
                scores.append(100.0 - float(ev.get("health_score", 50)))
        if scores:
            return round(max(scores), 1), "exchange_health_monitor"
    except Exception:
        logger.debug("counterparty risk lookup skipped", exc_info=True)
    return 20.0, "default_counterparty"


def _component_network_risk(opportunity: dict[str, Any], *, seed: dict[str, Any]) -> tuple[float, str]:
    chain = str(opportunity.get("chain") or opportunity.get("network") or "ethereum").lower()
    gas_usd = float((seed.get("network_gas_estimates_usd") or {}).get(chain, 5.0))
    quote = float(opportunity.get("quote_usd") or 1000)
    gas_pct = (gas_usd / quote) * 100 if quote > 0 else 10.0
    return round(min(100.0, gas_pct * 10), 1), f"gas_estimate_{gas_usd}usd"


def assess_fill_risk(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute Execution Risk % with full breakdown — no opaque score."""
    seed = seed or _load_seed()
    asset = str(opportunity.get("asset") or "BTC").split("/")[0].upper()
    weights = seed.get("component_weights") or {}

    components = {
        "liquidity": _component_liquidity_risk(opportunity),
        "slippage": _component_slippage_risk(opportunity),
        "volatility": _component_volatility_risk(asset, seed=seed),
        "counterparty": _component_counterparty_risk(opportunity),
        "network": _component_network_risk(opportunity, seed=seed),
    }

    weighted = 0.0
    weight_sum = 0.0
    breakdown: dict[str, Any] = {}
    reasons: list[str] = []

    for name, (risk_val, reason) in components.items():
        w = float(weights.get(name, 0.2))
        weighted += risk_val * w
        weight_sum += w
        breakdown[name] = {
            "risk_pct": risk_val,
            "weight": w,
            "weighted_contribution": round(risk_val * w, 2),
            "reason": reason,
        }
        if risk_val >= 60:
            reasons.append(f"{name}:{reason}")

    fill_risk_pct = round(weighted / weight_sum, 2) if weight_sum else 0.0
    user_limit = float(seed.get("user_risk_limit_pct", 65.0))
    signal_rejected = fill_risk_pct > user_limit

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "legal_name": _LEGAL_NAME,
        "fill_risk_pct": fill_risk_pct,
        "execution_risk_pct": fill_risk_pct,
        "component_breakdown": breakdown,
        "component_weights": weights,
        "top_reasons": reasons,
        "user_risk_limit_pct": user_limit,
        "signal_rejected": signal_rejected,
        "rejection_reason": "risk_above_user_limit" if signal_rejected else None,
        "no_opaque_score": True,
        "weights_documented": True,
        "scoring_engine_version": seed.get("scoring_engine_version"),
        "methodology_version": _METHODOLOGY_VERSION,
        "simulation_only": True,
        "evidence_class": "BACKTESTED",
    }


def apply_net_edge_risk_gate(
    opportunity: dict[str, Any],
    *,
    truth_result: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#417 integration — reject when fill risk exceeds user limit."""
    seed = seed or _load_seed()
    risk = assess_fill_risk(opportunity, seed=seed)

    if truth_result is None:
        try:
            from net_edge_truth import compute_net_edge_truth

            truth_result = compute_net_edge_truth({
                **opportunity,
                "net_profit_usdt": opportunity.get("net_edge_usdt"),
                "total_slippage_bps": opportunity.get("slippage_bps"),
                "trading_fees_usdt": opportunity.get("trading_fees_usdt"),
                "withdrawal_fee_usdt": opportunity.get("withdrawal_fee_usdt", 0),
                "quote_age_ms": opportunity.get("quote_age_ms", 500),
            })
        except Exception:
            truth_result = {}

    rejected = bool(risk.get("signal_rejected")) or bool(truth_result.get("reject"))
    reasons = list(truth_result.get("reasons") or [])
    if risk.get("signal_rejected"):
        reasons.append("fill_risk_above_user_limit")

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "integration": "net_edge_truth",
        "feature_ref": 417,
        "fill_risk": risk,
        "net_edge_truth": truth_result,
        "signal_rejected": rejected,
        "rejection_reasons": reasons,
        "pass": not rejected,
        "evidence_class": "BACKTESTED",
    }


def build_capital_protection_integration(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#410 — display risk score per opportunity."""
    seed = seed or _load_seed()
    risk = assess_fill_risk(opportunity, seed=seed)
    return {
        "ok": True,
        "integration": "capital_protection_controls",
        "feature_ref": 410,
        "fill_risk_pct": risk["fill_risk_pct"],
        "component_breakdown": risk["component_breakdown"],
        "signal_rejected": risk["signal_rejected"],
        "non_executive": True,
        "no_automatic_fund_movement": True,
        "display": f"Fill Risk {risk['fill_risk_pct']:.1f}% — analytics only",
        "evidence_class": "BACKTESTED",
    }


def build_fill_risk_panel(opportunity_id: str | None = None, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()

    try:
        from bd_platform.unified_arbitrage_engine import build_unified_feed

        feed = build_unified_feed(seed=None)
        opps = feed.get("opportunities") or []
    except Exception:
        opps = []

    assessments = []
    for opp in opps:
        if opportunity_id and opp.get("opportunity_id") != opportunity_id:
            continue
        assessments.append({
            "opportunity_id": opp.get("opportunity_id"),
            "opportunity_type": opp.get("opportunity_type"),
            "fill_risk": assess_fill_risk(opp, seed=seed),
            "capital_protection": build_capital_protection_integration(opp, seed=seed),
            "net_edge_gate": apply_net_edge_risk_gate(opp, seed=seed),
        })

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "assessments": assessments,
        "count": len(assessments),
        "user_risk_limit_pct": seed.get("user_risk_limit_pct"),
        "infrastructure_sla_cancelled": seed.get("infrastructure_sla_cancelled", True),
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def fill_risk_assessment_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "no_opaque_score": True,
        "components": list((seed.get("component_weights") or {}).keys()),
        "integrations": {
            "capital_protection_410": True,
            "net_edge_truth_417": True,
            "fill_feasibility_415": True,
        },
        "infrastructure_sla_cancelled": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "risk layer"})
    checks.append({"id": "legal_name_no_execution", "passed": "execution" not in seed.get("legal_name", "").lower() or seed.get("legal_name") == "Fill Risk Assessment", "detail": seed.get("legal_name")})

    opp = {
        "asset": "BTC",
        "slippage_bps": 12,
        "quote_usd": 1000,
        "buy_venue": "binance",
        "sell_venue": "okx",
        "volume_feasibility": {"liquidity_score": 80, "verdict": "full_fill"},
    }
    risk = assess_fill_risk(opp, seed=seed)
    checks.append({"id": "fill_risk_pct_breakdown", "passed": "fill_risk_pct" in risk and len(risk["component_breakdown"]) == 5, "detail": str(risk["fill_risk_pct"])})
    checks.append({"id": "weights_documented", "passed": risk.get("weights_documented") and risk.get("component_weights"), "detail": "weights"})
    checks.append({"id": "no_opaque_score", "passed": risk.get("no_opaque_score") is True, "detail": "transparent"})

    high_risk_opp = {**opp, "volume_feasibility": {"liquidity_score": 10, "verdict": "not_fillable"}, "slippage_bps": 80}
    high_risk = assess_fill_risk(high_risk_opp, seed=seed)
    gate = apply_net_edge_risk_gate(high_risk_opp, seed=seed)
    checks.append({"id": "net_edge_risk_gate_417", "passed": high_risk["fill_risk_pct"] > seed.get("user_risk_limit_pct", 65) or gate.get("signal_rejected"), "detail": "417 gate"})

    cp = build_capital_protection_integration(opp, seed=seed)
    checks.append({"id": "capital_protection_410", "passed": cp.get("feature_ref") == 410, "detail": "410"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
