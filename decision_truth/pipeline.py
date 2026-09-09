"""Decision Truth unified pipeline (DTS-002 pipeline)."""

from __future__ import annotations

from typing import Any

from decision_truth.admission import evaluate_admission_gate
from decision_truth.calibration import calibration_summary
from decision_truth.capacity import estimate_capacity
from decision_truth.change import detect_change
from decision_truth.contract import build_decision_contract
from decision_truth.evidence import compute_evidence_grade, resolve_evidence_class
from decision_truth.execution import compute_execution_feasibility
from decision_truth.half_life import attach_half_life
from decision_truth.net_edge import compute_formal_net_edge
from decision_truth.outcome import pre_register_outcome
from decision_truth.rejection import build_why_not, record_rejection
from decision_truth.risk import compute_risk_envelope, exchange_health_context, reverse_stress, stablecoin_depeg_assessment
from decision_truth.simulation import simulation_summary
from decision_truth.smart_money import build_smart_money_context


def evaluate_decision_truth(
    opportunity: dict[str, Any],
    *,
    portfolio: dict[str, Any] | None = None,
    lang: str = "en",
    previous_decision_state: str | None = None,
) -> dict[str, Any]:
    """Run full Decision Truth pipeline and attach results to opportunity dict."""
    opp = dict(opportunity)
    portfolio = portfolio or {}

    net_edge = compute_formal_net_edge(opp)
    execution = compute_execution_feasibility(opp, net_edge=net_edge)
    capacity = estimate_capacity(opp, net_edge=net_edge)
    half_life = attach_half_life(opp)
    risk = compute_risk_envelope(opp, portfolio=portfolio)
    risk["reverse_stress"] = reverse_stress(portfolio)
    risk["stablecoin"] = stablecoin_depeg_assessment(opp)
    risk["exchange_health"] = exchange_health_context(opp)

    admission = evaluate_admission_gate(
        opp,
        net_edge=net_edge,
        execution=execution,
        capacity=capacity,
        risk=risk,
        evidence_grade=compute_evidence_grade(opp, net_edge=net_edge, admission={"admission_state": "ADMITTED"}),
    )
    evidence_grade = compute_evidence_grade(opp, net_edge=net_edge, admission=admission)
    evidence_class = resolve_evidence_class(opp)
    opp["simulation_summary"] = simulation_summary(opp)
    opp["calibration_summary"] = calibration_summary()
    opp["evidence_class"] = evidence_class

    admission = evaluate_admission_gate(
        opp,
        net_edge=net_edge,
        execution=execution,
        capacity=capacity,
        risk=risk,
        evidence_grade=evidence_grade,
    )

    why_not = build_why_not(admission=admission, net_edge=net_edge, execution=execution, lang=lang)
    contract = build_decision_contract(
        opp,
        net_edge=net_edge,
        execution=execution,
        capacity=capacity,
        half_life=half_life,
        risk=risk,
        evidence_grade=evidence_grade,
        evidence_class=evidence_class,
        admission=admission,
        why_not=why_not.get("reason_codes"),
    )

    record_rejection(
        opportunity_id=str(contract["decision_id"]),
        admission_state=admission["admission_state"],
        failed_gates=admission.get("failed_gates") or [],
        gross_edge=net_edge.get("theoretical_edge_usd"),
        expected_net_edge=net_edge.get("expected_net_edge_usd"),
        execution_score=execution.get("execution_feasibility_score"),
    )

    if previous_decision_state and previous_decision_state != contract["decision_state"]:
        change = detect_change(
            decision_id=str(contract["decision_id"]),
            previous_state=previous_decision_state,
            new_state=str(contract["decision_state"]),
            changed_inputs={"admission": admission.get("failed_gates")},
            reason="admission_state_change",
        )
    else:
        change = {"changed": False}

    pre_register_outcome(
        decision_id=str(contract["decision_id"]),
        prediction=str(opp.get("verdict") or contract["decision_state"]),
        confidence=float(net_edge.get("fill_probability") or 0.5),
        horizon=str(contract.get("time_horizon") or "1h"),
        invalidation_condition=str(contract.get("invalidation_condition") or ""),
        evidence_class=evidence_class,
        methodology_versions=contract.get("methodology_versions") or {},
    )

    safety_floor = {
        "freshness": contract.get("freshness_state"),
        "data_quality": contract.get("data_quality_state"),
        "evidence_class": evidence_class,
        "uncertainty": net_edge.get("net_edge_interval"),
        "limitations": ["not_investment_advice", "no_future_guarantee"],
        "invalidation_trigger": contract.get("invalidation_condition"),
        "execution_feasibility": execution.get("execution_feasibility_score"),
    }

    result = {
        "decision_truth": {
            "net_edge": net_edge,
            "execution_feasibility": execution,
            "capacity": capacity,
            "half_life": half_life,
            "risk": risk,
            "evidence_grade": evidence_grade,
            "admission": admission,
            "contract": contract,
            "why_not": why_not,
            "safety_floor": safety_floor,
            "smart_money": build_smart_money_context(opp),
            "change": change,
            "six_heroes": _six_heroes_surface(contract, opp, lang),
            "evidence_trail": _evidence_trail(contract, net_edge, execution, capacity, risk, evidence_grade),
        }
    }
    opp.update(result)
    return opp


def _six_heroes_surface(contract: dict[str, Any], opp: dict[str, Any], lang: str) -> dict[str, Any]:
    from i18n_service import t

    return {
        "my_capital": opp.get("portfolio_summary") or {"status": "user_configured"},
        "market_state": opp.get("market_regime") or contract.get("freshness_state"),
        "best_verified_opportunity": None if contract["decision_state"] in {"REJECTED", "ABSTAINED"} else contract.get("expected_net_edge"),
        "main_risk": (contract.get("portfolio_impact") or ["risk_unspecified"])[0] if isinstance(contract.get("portfolio_impact"), list) else contract.get("risk_score"),
        "smart_money_evidence": opp.get("smart_money"),
        "decision_brief": t("dts.six_heroes.brief", lang),
        "progressive_disclosure": True,
        "command_view_optional": True,
    }


def _evidence_trail(*parts: Any) -> dict[str, Any]:
    contract, net_edge, execution, capacity, risk, evidence_grade = parts
    return {
        "source": "decision_truth_pipeline_v1",
        "timestamp": contract.get("detected_at"),
        "freshness": contract.get("freshness_state"),
        "cost_autopsy": (net_edge.get("cost_autopsy") or {}).get("components"),
        "net_edge": net_edge,
        "execution_feasibility": execution,
        "capacity": capacity,
        "risk": risk,
        "evidence_grade": evidence_grade,
        "invalidation_condition": contract.get("invalidation_condition"),
    }
