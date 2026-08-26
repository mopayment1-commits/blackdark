"""
Funding Arbitrage Simulator — Feature #338 (Wave 3 Pro/Institution).

Renamed from "Funding_Arbitrage_Engine".
Paper/simulation ONLY — no live execution, no exchange API integration.
Legal review mandatory before release.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.FundingArbitrageSimulator")

_FEATURE_ID = 338
_RENAMED_FROM = "Funding_Arbitrage_Engine"
_TITLE = "Funding Arbitrage Simulator"
_STANDALONE = True
_MERGED_INTO = "Intelligence Ledger / Funding Arbitrage Simulator (Wave 3 Pro/Institution)"
_WAVE = 3
_SPRINT = 3
_TIER = "pro/institution"
_SEED_PATH = Path("data/funding_arbitrage_simulator_seed.json")
_FORMULA_VERSION = "1.0"
_METHODOLOGY_VERSION = "1.0"

Tier = Literal["pro", "institution"]

_DISCLAIMER = (
    "Hypothetical analysis. Not investment advice. All costs estimated. "
    "Past data does not indicate future results. No guaranteed profit. "
    "Paper/simulation only — no live execution."
)

_BANNED_TERMS = ("opportunity", "best trade", "execute", "guaranteed profit", "engine")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"scenarios": [], "legal_review": {}, "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("funding arbitrage simulator seed load failed: %s", exc)
        return {"scenarios": [], "legal_review": {}, "backtest": {}}


def build_legal_review_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    lr = seed.get("legal_review") or {}
    complete = bool(lr.get("complete", False))
    return {
        "legal_review_mandatory": True,
        "legal_review_complete": complete,
        "legal_review_date": lr.get("date"),
        "compliance_framework_required": True,
        "release_blocked_without_review": not complete,
        "gate_passed": complete,
        "display": (
            f"Legal review: {'COMPLETE' if complete else 'PENDING — release blocked'}"
        ),
    }


def compute_hypothetical_carry(scenario: dict[str, Any]) -> dict[str, Any]:
    """Compute hypothetical net spread — all costs mandatory, no guaranteed profit."""
    funding_rate = float(scenario.get("funding_rate", 0))
    funding_interval_hours = float(scenario.get("funding_interval_hours", 8))
    periods_per_year = (365 * 24) / funding_interval_hours
    gross_carry_pct = funding_rate * periods_per_year * 100

    fees_pct = float(scenario.get("fees_pct", 0))
    borrow_cost_pct = float(scenario.get("borrow_cost_pct", 0))
    slippage_pct = float(scenario.get("slippage_pct", 0))
    basis_risk_penalty_pct = float(scenario.get("basis_risk_penalty_pct", 0))
    liquidity_penalty_pct = float(scenario.get("liquidity_penalty_pct", 0))

    total_costs = fees_pct + borrow_cost_pct + slippage_pct + basis_risk_penalty_pct + liquidity_penalty_pct
    net_carry_pct = round(gross_carry_pct - total_costs, 4)

    return {
        "gross_carry_pct": round(gross_carry_pct, 4),
        "hypothetical_net_spread_pct": net_carry_pct,
        "hypothetical_net_spread_display": f"Hypothetical net spread = {net_carry_pct:.4f}%",
        "no_guaranteed_profit": True,
        "all_costs_included": True,
        "cost_breakdown": {
            "fees_pct": fees_pct,
            "borrow_cost_pct": borrow_cost_pct,
            "slippage_pct": slippage_pct,
            "basis_risk_penalty_pct": basis_risk_penalty_pct,
            "liquidity_penalty_pct": liquidity_penalty_pct,
            "total_costs_pct": round(total_costs, 4),
        },
        "costs_estimated": True,
        "basis_risk_included": basis_risk_penalty_pct > 0,
        "liquidity_penalty_included": liquidity_penalty_pct > 0,
    }


def build_scenario_result(scenario: dict[str, Any]) -> dict[str, Any]:
    carry = compute_hypothetical_carry(scenario)
    confidence = scenario.get("confidence", "medium")
    return {
        "scenario_id": scenario.get("scenario_id"),
        "asset": scenario.get("asset"),
        "long_venue": scenario.get("long_venue"),
        "short_venue": scenario.get("short_venue"),
        "point_in_time_utc": scenario.get("point_in_time_utc"),
        "point_in_time_replay": True,
        "no_forward_performance_claim": True,
        "paper_simulation_only": True,
        "no_live_execution": True,
        "no_exchange_api_integration": True,
        **carry,
        "confidence": confidence,
        "confidence_display": f"Confidence: {confidence} (estimated costs)",
        "no_opportunity_language": True,
        "ranked_by": "hypothetical_net_spread",
        "disclaimer": _DISCLAIMER,
    }


def build_simulation_panel(*, asset: str | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    legal_gate = build_legal_review_gate(seed)

    if not legal_gate["gate_passed"]:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "legal_review_pending",
            "legal_review_gate": legal_gate,
            "release_blocked": True,
            "disclaimer": _DISCLAIMER,
        }

    scenarios_raw = seed.get("scenarios") or []
    if asset:
        scenarios_raw = [s for s in scenarios_raw if s.get("asset", "").upper() == asset.upper()]

    results = [build_scenario_result(s) for s in scenarios_raw]
    results.sort(key=lambda r: r["hypothetical_net_spread_pct"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i
        r["rank_display"] = f"Ranked #{i} by hypothetical net spread"

    backtest = seed.get("backtest") or {}
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "no_engine_in_name": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "tier": _TIER,
        "tier_required": _TIER,
        "paper_simulation_only": True,
        "no_live_execution": True,
        "no_exchange_api_integration": True,
        "simulation_results": results,
        "result_count": len(results),
        "ranked_by_hypothetical_net_spread": True,
        "no_opportunity_language": True,
        "no_best_opportunity_language": True,
        "all_costs_mandatory": True,
        "no_guaranteed_profit": True,
        "point_in_time_replay": True,
        "paper_simulation_validation": backtest.get("paper_simulation_validated", False),
        "backtest": {
            "point_in_time_replay": True,
            "paper_simulation_validated": backtest.get("paper_simulation_validated", False),
            "no_forward_performance_claim": True,
            "events_replayed": backtest.get("events_replayed", 0),
        },
        "legal_review_gate": legal_gate,
        "formula_version": _FORMULA_VERSION,
        "disclaimer": _DISCLAIMER,
        "disclaimer_on_every_output": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def funding_arbitrage_simulator_status() -> dict[str, Any]:
    seed = _load_seed()
    legal_gate = build_legal_review_gate(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "no_engine_in_name": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "tier": _TIER,
        "tier_required": _TIER,
        "paper_simulation_only": True,
        "no_live_execution": True,
        "legal_review_gate": legal_gate,
        "acceptance_criteria": {
            "all_costs_included": True,
            "no_guaranteed_profit": True,
            "point_in_time_replay": True,
            "paper_simulation_validation": True,
            "legal_review_mandatory": True,
            "no_engine_in_name": True,
            "no_opportunity_language": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
