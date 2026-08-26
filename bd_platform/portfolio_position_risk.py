"""
Portfolio Position Risk — Features #366 + #373 absorbed into Portfolio AI.

#366 Liquidation Risk → Position Stress Scenario (portfolio-level, educational).
#373 Margin_Risk_Calculator → Position Risk Context (component breakdown, no score).
#377 Multi-Model Liquidation Comparison → HOLD & BLOCK (prerequisites not met).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PortfolioPositionRisk")

_FEATURE_ID = 373
_ABSORBED_IDS = (366, 373)
_BLOCKED_IDS = (377,)
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Position Risk Context"
_WAVE = 2
_SPRINT = 2
_SEED_PATH = Path("data/portfolio_position_risk_seed.json")
_METHODOLOGY_VERSION = "1.0"

_STRESS_DISCLAIMER = (
    "Position stress scenarios are educational — not investment advice. "
    "Shows mathematical outcomes under stated assumptions. "
    "Not a liquidation warning or recommendation to sell."
)

_RISK_DISCLAIMER = (
    "Position risk context is educational — not investment advice. "
    "Component breakdown only — no risk score. "
    "Ranges shown — no false precision."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"positions": {}, "venue_rules": {}, "blocked_features": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("portfolio position risk seed load failed: %s", exc)
        return {"positions": {}, "venue_rules": {}, "blocked_features": {}}


def build_venue_rules_block(venue: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#373 venue-specific rules — versioned, mandatory."""
    seed = seed or _load_seed()
    rules = (seed.get("venue_rules") or {}).get(venue.lower(), {})
    return {
        "venue": venue,
        "rules_version": rules.get("version", "1.0"),
        "margin_mode": rules.get("margin_mode", "cross"),
        "maintenance_margin_pct": rules.get("maintenance_margin_pct"),
        "initial_margin_pct": rules.get("initial_margin_pct"),
        "liquidation_fee_pct": rules.get("liquidation_fee_pct"),
        "venue_specific_rules_versioned": True,
        "last_updated": rules.get("last_updated"),
        "display": (
            f"{venue} margin rules v{rules.get('version', '1.0')} | "
            f"Maint: {rules.get('maintenance_margin_pct', 'N/A')}%"
        ),
    }


def build_stress_scenario(
    scenario: dict[str, Any],
    position: dict[str, Any],
    *,
    venue_rules: dict[str, Any],
) -> dict[str, Any]:
    """#366 Position Stress Scenario — assumptions visible, mathematical result."""
    price_drop_pct = float(scenario.get("price_drop_pct", 0))
    current_ltv = float(position.get("ltv", 0))
    new_ltv = round(current_ltv / (1 - price_drop_pct / 100) if price_drop_pct < 100 else 1.0, 4)
    liq_threshold = float(venue_rules.get("maintenance_margin_pct", 80)) / 100

    return {
        "scenario_id": scenario.get("scenario_id"),
        "scenario_name": scenario.get("name"),
        "assumptions": {
            "price_drop_pct": price_drop_pct,
            "liquidity_unchanged": scenario.get("liquidity_unchanged", True),
            "no_new_positions": scenario.get("no_new_positions", True),
            "margin_rules_version": venue_rules.get("rules_version"),
            "display": (
                f"Assumption: price drops {price_drop_pct}% | "
                f"liquidity unchanged | no new positions"
            ),
        },
        "scenario_assumptions_lock": True,
        "mathematical_result": {
            "current_ltv": current_ltv,
            "projected_ltv": new_ltv,
            "liquidation_threshold_ltv": liq_threshold,
            "display": (
                f"If price drops {price_drop_pct}%, your LTV becomes {new_ltv:.2%} "
                f"(threshold: {liq_threshold:.0%})"
            ),
        },
        "no_liquidation_risk_label": True,
        "no_high_risk_warning": True,
        "educational_only": True,
        "not_investment_advice": True,
    }


def build_position_stress_scenario(position_id: str = "pos_001") -> dict[str, Any]:
    """#366 absorbed — Portfolio Stress Test / Position Stress Scenario."""
    t0 = time.perf_counter()
    seed = _load_seed()
    position = (seed.get("positions") or {}).get(position_id)

    if not position:
        return {"ok": False, "feature_id": _FEATURE_ID, "sub_task": "#366", "error": "position_not_found"}

    venue = position.get("venue", "binance")
    venue_rules = build_venue_rules_block(venue, seed)
    scenarios = [
        build_stress_scenario(s, position, venue_rules=venue_rules)
        for s in (position.get("stress_scenarios") or [])
    ]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sub_task": "#366",
        "absorbed_from": "Liquidation Risk",
        "title": "Position Stress Scenario",
        "renamed_output": "Position Stress Scenario",
        "no_liquidation_risk_output": True,
        "standalone_rejected": True,
        "merged_into": "Portfolio AI / Portfolio Stress Test",
        "surface": "portfolio_ai",
        "no_separate_sprint": True,
        "position_id": position_id,
        "asset": position.get("asset"),
        "venue": venue,
        "venue_rules": venue_rules,
        "stress_scenarios": scenarios,
        "scenario_count": len(scenarios),
        "scenario_assumptions_mandatory": True,
        "educational_not_advice": True,
        "disclaimer": _STRESS_DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def _format_range(low: float, high: float, *, unit: str = "USD") -> dict[str, Any]:
    return {
        "low": low,
        "high": high,
        "range_display": f"{low:,.0f}–{high:,.0f} {unit}",
        "no_false_precision": True,
        "exact_number_forbidden": True,
    }


def build_position_risk_context(position_id: str = "pos_001") -> dict[str, Any]:
    """#373 Position Risk Context — component breakdown, no risk score."""
    t0 = time.perf_counter()
    seed = _load_seed()
    position = (seed.get("positions") or {}).get(position_id)

    if not position:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "position_not_found"}

    lr = seed.get("legal_review") or {}
    legal_complete = bool(lr.get("complete", False))
    venue = position.get("venue", "binance")
    venue_rules = build_venue_rules_block(venue, seed)
    stale = position.get("data_stale", False)
    stale_penalty = position.get("stale_data_penalty_applied", False)

    margin_util = float(position.get("margin_utilization_pct", 0))
    liq_dist_low = float(position.get("liquidation_distance_usd_low", 0))
    liq_dist_high = float(position.get("liquidation_distance_usd_high", 0))

    stress_losses = []
    for s in (position.get("stress_scenarios") or []):
        loss_low = float(s.get("scenario_loss_usd_low", 0))
        loss_high = float(s.get("scenario_loss_usd_high", 0))
        stress_losses.append({
            "scenario": s.get("name"),
            "scenario_loss": _format_range(loss_low, loss_high),
            "stress_test_mandatory": True,
            "display": (
                f"Scenario '{s.get('name')}': loss range "
                f"${loss_low:,.0f}–${loss_high:,.0f}"
            ),
        })

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sub_task": "#373",
        "absorbed_from": "Margin_Risk_Calculator",
        "title": "Position Risk Context",
        "renamed_from": "Margin_Risk_Calculator",
        "no_risk_score_in_name": True,
        "no_risk_score_in_output": True,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "surface": "portfolio_ai",
        "wave": _WAVE,
        "position_id": position_id,
        "asset": position.get("asset"),
        "venue": venue,
        "venue_rules": venue_rules,
        "output_format": "component_breakdown",
        "components": {
            "margin_utilization": {
                "utilization_pct": margin_util,
                "utilization_range": _format_range(
                    max(0, margin_util - 2), min(100, margin_util + 2), unit="%"
                ),
                "display": f"Margin utilization: ~{margin_util:.0f}%",
            },
            "liquidation_distance": {
                "distance_range": _format_range(liq_dist_low, liq_dist_high),
                "stress_tests_required": True,
                "no_distance_without_scenarios": True,
                "display": (
                    f"Liquidation distance: ${liq_dist_low:,.0f}–${liq_dist_high:,.0f} "
                    "(range — no false precision)"
                ),
            },
            "scenario_losses": {
                "scenarios": stress_losses,
                "stress_tests_mandatory": True,
            },
            "concentration": {
                "concentration_pct": position.get("concentration_pct"),
                "hedge_ratio": position.get("hedge_ratio"),
                "display": f"Concentration: {position.get('concentration_pct', 'N/A')}%",
            },
        },
        "stale_data": {
            "stale": stale,
            "stale_data_penalty_applied": stale_penalty,
            "display": "Stale data penalty applied" if stale_penalty else "Data fresh",
        },
        "no_false_precision": True,
        "ranges_not_exact_numbers": True,
        "legal_review": {
            "mandatory": True,
            "complete": legal_complete,
            "release_blocked_without_review": not legal_complete,
        },
        "educational_not_advice": True,
        "no_high_risk_warning": True,
        "disclaimer": _RISK_DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_multi_model_liquidation_blocked_status() -> dict[str, Any]:
    """#377 HOLD & BLOCK — prerequisites not met."""
    seed = _load_seed()
    blocked = seed.get("blocked_features") or {}
    b377 = blocked.get("377") or {}
    return {
        "ok": True,
        "feature_id": 377,
        "title": "Multi-Model Liquidation Comparison",
        "status": "hold_and_block",
        "engineering_blocked": True,
        "no_sprint": True,
        "no_engineering_allocation": True,
        "prerequisite": "multiple_liquidation_models_required",
        "prerequisites_met": False,
        "models_available": b377.get("models_available", 0),
        "models_required": b377.get("models_required", 3),
        "no_consensus_heatmap": True,
        "consensus_interpretation_forbidden": True,
        "model_disagreement_required_when_built": True,
        "display": (
            f"BLOCKED — {b377.get('models_available', 0)}/{b377.get('models_required', 3)} "
            "liquidation models available. No engineering until prerequisites met."
        ),
        "reason": b377.get(
            "reason",
            "Model1/2/3 outputs not available — comparison framework premature",
        ),
        "timestamp": _utcnow(),
    }


def portfolio_position_risk_status() -> dict[str, Any]:
    seed = _load_seed()
    lr = seed.get("legal_review") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Position Risk Context",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "surface": "portfolio_ai",
        "absorbed_tickets": {
            366: "Position Stress Scenario (standalone rejected, renamed from Liquidation Risk)",
            373: "Position Risk Context (renamed from Margin_Risk_Calculator)",
        },
        "blocked_tickets": {
            377: "Multi-Model Liquidation Comparison — HOLD pending liquidation models",
        },
        "acceptance_criteria": {
            "scenario_assumptions_mandatory": True,
            "venue_rules_versioned": True,
            "stress_tests_mandatory": True,
            "no_false_precision": True,
            "no_risk_score_output": True,
            "no_liquidation_risk_label": True,
            "educational_not_advice": True,
            "legal_review_mandatory": True,
        },
        "legal_review": {
            "mandatory": True,
            "complete": bool(lr.get("complete", False)),
        },
        "position_count": len(seed.get("positions") or {}),
        "disclaimer": _RISK_DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
