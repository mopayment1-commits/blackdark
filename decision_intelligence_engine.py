"""Decision Intelligence Engine — coherent orchestrator over graph + risk + execution truth."""

from __future__ import annotations

from typing import Any

from canonical_adoption import adopt_decision_market_state, adopt_risk_report
from confidence_truth import claim_insufficient, sanitize_confidence_field
from continuous_learning import calibrate_from_history, record_outcome_evaluation
from decision_graph import attach_learning, attach_outcome, record_decision_bundle
from institutional_memory import query as memory_query
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
    market_state = adopt_decision_market_state(market_state, source="decision_intelligence")
    adopted_risks = [adopt_risk_report(r, source="decision_risk") for r in list(risk_reports or [])]
    gate = aggregate_risk_gate(adopted_risks)
    conf = sanitize_confidence_field(confidence) if confidence is not None else claim_insufficient(
        label="decision",
        notes="No calibrated probability supplied",
    ).to_dict()

    # Prefer calibrated history when sufficient samples exist.
    calib = calibrate_from_history(min_samples=30)
    if calib.get("is_probability"):
        conf = calib

    executable = bool(gate.get("executable")) and bool(decision.get("wants_action", True))
    feasibility = {
        "executable": executable,
        "indicative": not executable,
        "risk_gate": gate,
        "reason": None if executable else "risk_or_policy_block",
    }
    if executable:
        action = {"type": decision.get("action") or "proceed", "status": "authorized"}
    else:
        action = {"type": "stand_down", "status": "blocked", "reason": feasibility["reason"]}

    # Hallucination guard: evidence payloads must be dicts with source or id.
    clean_evidence = []
    for e in evidence or []:
        if not isinstance(e, dict):
            continue
        if not (e.get("source") or e.get("id") or e.get("kind") or e.get("text")):
            continue
        clean_evidence.append(e)
    if evidence and not clean_evidence:
        feasibility = {
            "executable": False,
            "indicative": True,
            "risk_gate": gate,
            "reason": "hallucinated_or_empty_evidence",
        }
        action = {"type": "stand_down", "status": "blocked", "reason": feasibility["reason"]}
        executable = False

    bundle = record_decision_bundle(
        market_state=market_state,
        evidence=clean_evidence,
        contradictions=contradictions,
        hypothesis=hypothesis,
        decision={**decision, "confidence": conf},
        risk={"aggregate": gate, "reports": adopted_risks},
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
            "market_state": market_state,
        },
        graph_id=bundle["graph_id"],
        actor=actor,
    )
    remember("market_state", market_state, graph_id=bundle["graph_id"], actor=actor)
    for e in clean_evidence:
        remember("evidence", e, graph_id=bundle["graph_id"], actor=actor)
    return {
        "engine": "decision_intelligence_engine",
        "graph_id": bundle["graph_id"],
        "decision_node_id": bundle.get("decision_node_id"),
        "executable": executable,
        "confidence": conf,
        "feasibility": feasibility,
        "action": action,
        "auditable": True,
        "replayable": True,
        "canonical_adopted": True,
        "product_complete": False,
        "note": "Unified decision brain: canonical market + graph + typed confidence + risk + memory.",
    }


def close_decision_loop(
    *,
    graph_id: str,
    decision_node_id: str,
    predicted: dict[str, Any],
    actual: dict[str, Any],
    decision_ts: str,
    outcome_ts: str,
    actor: str = "decision_intelligence_engine",
) -> dict[str, Any]:
    """DECISION → OUTCOME → EVALUATION → CALIBRATION → LEARNING (hindsight-safe)."""
    evaluation = record_outcome_evaluation(
        graph_id=graph_id,
        decision_node_id=decision_node_id,
        predicted=predicted,
        actual=actual,
        decision_ts=decision_ts,
        outcome_ts=outcome_ts,
        actor=actor,
    )
    remember(
        "actual_outcome",
        actual,
        graph_id=graph_id,
        actor=actor,
    )
    remember(
        "learning_event",
        evaluation,
        graph_id=graph_id,
        actor=actor,
    )
    outcome_node = attach_outcome(
        graph_id,
        decision_node_id=decision_node_id,
        outcome=actual,
        actor=actor,
    )
    learning_attach = attach_learning(
        graph_id,
        outcome_node_id=outcome_node["node_id"],
        learning={"evaluation": evaluation, "calibration": calibrate_from_history(min_samples=1)},
        actor=actor,
    )
    return {
        "graph_id": graph_id,
        "evaluation": evaluation,
        "learning": learning_attach,
        "calibration": calibrate_from_history(min_samples=30),
        "memory_entries": len(memory_query(graph_id=graph_id, limit=500)),
        "product_complete": False,
    }


def engine_status() -> dict[str, Any]:
    return {
        "surface": "decision_intelligence_engine",
        "product_complete": False,
        "components": [
            "decision_graph",
            "confidence_truth",
            "risk_intelligence",
            "institutional_memory",
            "continuous_learning",
            "canonical_adoption",
            "execution_feasibility",
        ],
        "api": [
            "/api/institutional/decision-intelligence/evaluate",
            "/api/institutional/decision-intelligence/close-loop",
            "/api/institutional/decision-intelligence/status",
        ],
    }
