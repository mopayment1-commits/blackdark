"""Canonical Decision Truth governance entrypoint (P1 spine)."""

from __future__ import annotations

import logging
import time
from typing import Any

from decision_truth.admission import evaluate_admission
from decision_truth.compliance import apply_dts_compliance_guards, apply_user_agency
from decision_truth.contract import DecisionContract, DecisionState, build_field_availability
from decision_truth.inputs import extract_admission_inputs
from decision_truth.economics import economic_reality
from decision_truth.portfolio_risk import evaluate_portfolio_risk
from decision_truth.safety_floor import evaluate_safety_floor

logger = logging.getLogger("BLACKDARK.DecisionTruth.Govern")

GOVERNED_CONTEXTS = frozenset({"oracle", "arbitrage_row", "api", "cap646_opportunity", "trust_pulse", "voice"})


def govern_decision_payload(
    payload: dict[str, Any],
    *,
    context: str = "oracle",
    lang: str = "en",
    record: bool = False,
    run_data_governance: bool = True,
    previous_decision_state: str | None = None,
) -> dict[str, Any]:
    """Authoritative Decision Truth path — no silent fallback."""
    out = dict(payload)
    out["decision_truth_context"] = context
    fallback_notes: list[str] = []

    if run_data_governance and not out.get("data_governance"):
        try:
            from data_governance.pipeline import evaluate_data_governance

            sym = str(out.get("symbol") or out.get("asset") or "BTC").upper()
            out = evaluate_data_governance(out, symbol=sym, source_id=str(out.get("source") or context), slo_class="T0", lang=lang)
        except Exception as exc:
            logger.warning("data governance unavailable in govern path", exc_info=True)
            out["data_governance"] = {"error": "unavailable", "state": "UNAVAILABLE"}
            out["data_governance_state"] = "UNAVAILABLE"
            fallback_notes.append(f"data_governance_error:{exc}")

    fp = out.get("fallback_policy") or (out.get("data_governance") or {}).get("fallback_policy")
    if fp and fp.get("used_fallback"):
        fallback_notes.append(f"fallback_source:{fp.get('source')}")

    economics = economic_reality(out)
    net_edge = economics
    out["net_edge_truth"] = net_edge
    out["economic_reality"] = economics
    exec_pack = economics.get("execution_feasibility") or {}
    if exec_pack.get("score") is not None:
        out["execution_feasibility_score"] = exec_pack["score"]
    out["execution_feasibility_detail"] = exec_pack
    cap_pack = economics.get("capacity") or {}
    if cap_pack.get("capacity_usd") is not None:
        out["capacity_usd"] = cap_pack["capacity_usd"]
    out["opportunity_capacity"] = cap_pack
    if economics.get("opportunity_half_life"):
        out["opportunity_half_life"] = economics["opportunity_half_life"]
    portfolio_risk = evaluate_portfolio_risk(out, economics=economics)
    out["portfolio_risk"] = portfolio_risk
    if portfolio_risk.get("portfolio_pre_impact"):
        out["portfolio_pre_impact"] = portfolio_risk["portfolio_pre_impact"]
    inputs = extract_admission_inputs(out, net_edge=net_edge, portfolio_risk=portfolio_risk)
    admission_state, why_not = evaluate_admission(inputs)

    sym = str(out.get("symbol") or out.get("asset") or "BTC")
    invalidation = str(out.get("invalidation") or out.get("invalidation_condition") or "net_edge_or_freshness_breach")
    safety = evaluate_safety_floor(
        inputs,
        {
            "invalidation_condition": invalidation,
            "limitations": out.get("limitations") or [],
            "economics_required": not out.get("truth_indicative_only"),
            "half_life_material": bool(out.get("live_duration_seconds") or out.get("quote_age_ms")),
            "portfolio_risk": portfolio_risk,
        },
    )

    final_state = _combine_states(admission_state, safety)
    _update_stats(final_state)

    grade_present = "grade" in out and out.get("grade") not in (None, "")
    contract = DecisionContract(
        decision_state=final_state,
        symbol=sym,
        time_horizon=str(out.get("time_horizon") or "intraday"),
        net_edge=net_edge,
        execution_feasibility={
            "score": inputs.execution_score,
            "available": inputs.execution_available,
            "liquidity_ok": inputs.liquidity_ok,
            "state": exec_pack.get("state") or ("AVAILABLE" if inputs.execution_available else "UNAVAILABLE"),
            "reason_codes": list(exec_pack.get("reason_codes") or []),
            "components": dict(exec_pack.get("components") or {}),
            "methodology_version": exec_pack.get("methodology_version"),
        },
        risk={
            "ok": inputs.risk_ok,
            "state": "AVAILABLE" if inputs.risk_ok is not None else "UNAVAILABLE",
            "risk_envelope": portfolio_risk.get("risk_envelope"),
            "pre_impact": portfolio_risk.get("pre_impact"),
            "portfolio_pre_impact": portfolio_risk.get("portfolio_pre_impact"),
            "reverse_stress": portfolio_risk.get("reverse_stress"),
            "venue_health": portfolio_risk.get("venue_health"),
            "depeg": portfolio_risk.get("depeg"),
            "portfolio_context": portfolio_risk.get("portfolio_context"),
            "decision_impact": portfolio_risk.get("decision_impact"),
        },
        grade=str(out.get("grade") or "UNAVAILABLE"),
        evidence_class=str(inputs.evidence_class or "UNAVAILABLE"),
        freshness=inputs.freshness_meta,
        uncertainty={
            "high": inputs.uncertainty_high,
            "state": inputs.uncertainty_state,
            "interval": inputs.uncertainty_interval,
            "reason": inputs.uncertainty_reason,
        },
        capacity=cap_pack if cap_pack else {"state": "UNAVAILABLE", "reason": "capacity_not_evaluated"},
        why=["all_mandatory_gates_passed"] if final_state == DecisionState.AVAILABLE else [],
        why_not=list(why_not) + list(safety.failures),
        invalidation_condition=invalidation,
        assumptions=inputs.provenance_context.get("assumptions") or {},
        safety_floor=safety.to_dict(),
        provenance_context=inputs.provenance_context,
        field_availability=build_field_availability(
            inputs.missing_critical,
            grade_present=grade_present,
            capacity_available=str(cap_pack.get("state")) == "AVAILABLE",
            capacity_not_applicable=str(cap_pack.get("state")) == "NOT_APPLICABLE",
            portfolio_impact_available=str((portfolio_risk.get("pre_impact") or {}).get("state")) == "AVAILABLE",
            portfolio_impact_not_applicable=portfolio_risk.get("state") == "NOT_APPLICABLE",
        ),
        failure_integration={
            "failure_state": inputs.failure_state,
            "data_governance_state": inputs.data_governance_state,
            "propagated": bool(inputs.failure_state or inputs.data_governance_state in {"ABSTAINED", "REJECTED", "UNAVAILABLE"}),
        },
    )

    if record:
        from decision_truth.ledger import record_outcome

        record_outcome(contract)

    out["decision_truth"] = {
        "contract": contract.to_dict(),
        "admission": {
            "admission_state": final_state.value,
            "failed_gates": list(why_not),
            "gates": {
                "freshness": {"pass": inputs.freshness_ok is True},
                "data_governance": (out.get("data_governance") or {}).get("gates"),
            },
        },
        "why_not": {"human_explanation": contract.why_not, "codes": contract.why_not},
        "safety_floor": safety.to_dict(),
        "fallback_notes": fallback_notes,
        "silent_fallback": False,
        "lang": lang,
        "previous_decision_state": previous_decision_state,
        "methodology_version": contract.methodology_version,
    }
    out["decision_truth_state"] = final_state.value
    out["admission_state"] = final_state.value
    out = _apply_state_to_verdict(out, final_state)
    out = apply_user_agency(out)
    out = apply_dts_compliance_guards(out)
    return out


def govern_arbitrage_row(row: dict[str, Any]) -> dict[str, Any]:
    governed = govern_decision_payload(row, context="arbitrage_row", run_data_governance=False, record=False)
    state = governed.get("decision_truth_state")
    governed["decision_truth_bound"] = True
    if state in {"REJECTED", "ABSTAINED", "UNAVAILABLE", "DEGRADED"}:
        governed["truth_rejected"] = state in {"REJECTED", "ABSTAINED", "UNAVAILABLE"}
        governed["execution_feasibility"] = "not_executable" if state != "DEGRADED" else governed.get("execution_feasibility")
    return governed


def _combine_states(admission: DecisionState, safety) -> DecisionState:
    if admission in {DecisionState.REJECTED, DecisionState.UNAVAILABLE}:
        return admission
    if not safety.passed:
        if any("unavailable" in f or "failure_state" in f for f in safety.failures):
            return DecisionState.UNAVAILABLE
        if len(safety.failures) >= 2:
            return DecisionState.ABSTAINED
        return DecisionState.DEGRADED
    if admission == DecisionState.ADMITTED:
        return DecisionState.AVAILABLE
    return admission


def _apply_state_to_verdict(payload: dict[str, Any], state: DecisionState) -> dict[str, Any]:
    out = dict(payload)
    if state in {DecisionState.REJECTED, DecisionState.ABSTAINED, DecisionState.UNAVAILABLE}:
        from regulatory_compliance_guard import to_public_verdict

        out["verdict"] = to_public_verdict("Do Not Touch")
        out["decision_action"] = "NO_DECISION"
    elif state == DecisionState.DEGRADED:
        out["decision_action"] = "NO_DECISION"
        out.setdefault("degraded", True)
    return out


_STATS = {"evaluated": 0, "admitted": 0, "rejected": 0, "abstained": 0, "degraded": 0, "unavailable": 0}


def _update_stats(state: DecisionState) -> None:
    _STATS["evaluated"] += 1
    bucket = {
        DecisionState.AVAILABLE: "admitted",
        DecisionState.REJECTED: "rejected",
        DecisionState.ABSTAINED: "abstained",
        DecisionState.DEGRADED: "degraded",
        DecisionState.UNAVAILABLE: "unavailable",
    }.get(state)
    if bucket:
        _STATS[bucket] += 1


def govern_stats() -> dict[str, int]:
    return dict(_STATS)
