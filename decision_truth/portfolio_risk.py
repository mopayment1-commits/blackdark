"""Portfolio risk orchestration for Decision Truth (P3)."""

from __future__ import annotations

from typing import Any

from decision_truth.depeg import evaluate_depeg_risk
from decision_truth.portfolio_context import resolve_portfolio_context
from decision_truth.pre_impact import evaluate_pre_impact
from decision_truth.reverse_stress import evaluate_reverse_stress
from decision_truth.risk_envelope import build_risk_envelope
from decision_truth.venue_health import evaluate_venue_health_decision

METHODOLOGY_VERSION = "dts-p3-portfolio-risk-1.0"

_IMPACT_ORDER = {"reject": 5, "abstain": 4, "degrade": 3, "contextual_warning": 2, "none": 1, None: 0}


def evaluate_portfolio_risk(payload: dict[str, Any], *, economics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Canonical portfolio / risk evaluation path."""
    if payload.get("truth_indicative_only"):
        return {
            "state": "NOT_APPLICABLE",
            "reason": "advisory_only",
            "methodology_version": METHODOLOGY_VERSION,
        }

    portfolio_context = resolve_portfolio_context(payload)
    envelope = build_risk_envelope(payload, portfolio_context=portfolio_context)
    venue_health = evaluate_venue_health_decision(payload)
    depeg = evaluate_depeg_risk(payload)
    pre_impact = evaluate_pre_impact(
        payload,
        envelope=envelope,
        portfolio_context=portfolio_context,
        economics=economics,
        venue_health=venue_health,
        depeg=depeg,
    )
    reverse_stress = evaluate_reverse_stress(payload, envelope=envelope, portfolio_context=portfolio_context)

    decision_impact = _combine_impact(
        pre_impact.get("decision_impact"),
        venue_health.get("decision_impact"),
        depeg.get("decision_impact"),
    )

    return {
        "state": "AVAILABLE",
        "methodology_version": METHODOLOGY_VERSION,
        "portfolio_context": portfolio_context,
        "risk_envelope": envelope,
        "pre_impact": pre_impact,
        "portfolio_pre_impact": pre_impact.get("portfolio_pre_impact"),
        "reverse_stress": reverse_stress,
        "venue_health": venue_health,
        "depeg": depeg,
        "decision_impact": decision_impact,
        "material_breach": bool(pre_impact.get("material_breach")),
        "risk_ok": decision_impact in {"none", "degrade", "contextual_warning"},
    }


def _combine_impact(*impacts: str | None) -> str:
    best = "none"
    best_rank = 0
    for impact in impacts:
        rank = _IMPACT_ORDER.get(impact, 0)
        if rank > best_rank:
            best = str(impact)
            best_rank = rank
    return best
