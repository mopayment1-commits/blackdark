"""Decision Intelligence Engine — coherent orchestrator over graph + risk + execution truth."""

from __future__ import annotations

from typing import Any

from confidence_truth import claim_insufficient, sanitize_confidence_field
from decision_graph import record_decision_bundle
from institutional_memory import remember
from risk_intelligence import aggregate_risk_gate


def evaluate_decision(
    *,
    market_state: dict[str, Any],
    evidence: list[dict[str, Any]],
    hypothesis: dict[str, Any],
    decision: dict[str, Any],
    risk_reports: list[dict[str, Any]],
    contradictions: list[dict[str, Any]] | None = None,
    confidence: Any = None,
    actor: str = "decision_intelligence_engine",
) -> dict[str, Any]:
    """Build an auditable decision with risk-influenced execution feasibility."""
    gate = aggregate_risk_gate(list(risk_reports or []))
    conf = sanitize_confidence_field(confidence) if confidence is not None else claim_insufficient(
        label="decision",
        notes="No calibrated probability supplied",
    ).to_dict()

    executable = bool(gate.get("executable")) and bool(decision.get("wants_action", True))
    feasibility = {
        "executable": executable,
        "indicative": not executable,
        "risk_gate": gate,
        "reason": None if executable else "risk_or_policy_block",
    }
    action = None
    if executable:
        action = {"type": decision.get("action") or "proceed", "status": "authorized"}
    else:
        action = {"type": "stand_down", "status": "blocked", "reason": feasibility["reason"]}

    bundle = record_decision_bundle(
        market_state=market_state,
        evidence=evidence,
        contradictions=contradictions,
        hypothesis=hypothesis,
        decision={**decision, "confidence": conf},
        risk={"aggregate": gate, "reports": risk_reports},
        execution_feasibility=feasibility,
        action=action,
        confidence=conf,
        actor=actor,
    )
    remember(
        "decision",
        {
            "graph_id": bundle["graph_id"],
            "executable": executable,
            "confidence": conf,
            "decision": decision,
        },
        graph_id=bundle["graph_id"],
        actor=actor,
    )
    return {
        "engine": "decision_intelligence_engine",
        "graph_id": bundle["graph_id"],
        "executable": executable,
        "confidence": conf,
        "feasibility": feasibility,
        "action": action,
        "auditable": True,
        "product_complete": True,
        "note": "Coherent decision brain: graph + typed confidence + risk gates + memory.",
    }


def engine_status() -> dict[str, Any]:
    return {
        "surface": "decision_intelligence_engine",
        "product_complete": True,
        "components": [
            "decision_graph",
            "confidence_truth",
            "risk_intelligence",
            "institutional_memory",
            "execution_feasibility",
        ],
    }
