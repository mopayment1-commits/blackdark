"""Evidence / simulation / calibration lifecycle orchestrator (P4)."""

from __future__ import annotations

from typing import Any

from decision_truth.anti_cherry_picking import validate_performance_claim
from decision_truth.calibration import evaluate_calibration
from decision_truth.change_detector import detect_decision_changes
from decision_truth.evidence_grade import evaluate_evidence_grade
from decision_truth.evidence_taxonomy import resolve_evidence_class
from decision_truth.history_integrity import record_history_event
from decision_truth.methodology_versions import attach_methodology_versions, methodology_bundle
from decision_truth.outcome_ledger import pre_register_decision
from decision_truth.provenance import build_provenance_context
from decision_truth.simulation import evaluate_simulation_context

METHODOLOGY_VERSION = "dts-p4-evidence-lifecycle-1.0"


def evaluate_evidence_lifecycle(
    payload: dict[str, Any],
    *,
    economics: dict[str, Any] | None = None,
    portfolio_risk: dict[str, Any] | None = None,
    previous_snapshot: dict[str, Any] | None = None,
    previous_decision_state: str | None = None,
    pre_register: bool = True,
) -> dict[str, Any]:
    """Run P4 lifecycle stages and return governed pack."""
    evidence = resolve_evidence_class(payload)
    evidence_class = evidence["evidence_class"]
    provenance = build_provenance_context(payload)
    calibration = evaluate_calibration(payload, evidence_class=evidence_class, confidence=payload.get("confidence_percent"))
    portfolio_ctx = (portfolio_risk or {}).get("portfolio_context")
    simulation = evaluate_simulation_context(
        payload,
        economics=economics,
        portfolio_context=portfolio_ctx,
        evidence_class=evidence_class,
    )
    grade = evaluate_evidence_grade(
        payload,
        economics=economics,
        calibration=calibration,
        simulation=simulation,
        evidence_class=evidence_class,
    )

    changes = detect_decision_changes(payload, previous_snapshot, previous_decision_state=previous_decision_state)

    prereg = None
    decision_id = payload.get("decision_id")
    if pre_register and not payload.get("truth_indicative_only"):
        snapshot = {
            "decision_id": decision_id,
            "symbol": payload.get("symbol") or payload.get("asset"),
            "time_horizon": payload.get("time_horizon") or "intraday",
            "decision_state": payload.get("decision_truth_state") or payload.get("decision_state"),
            "confidence": payload.get("confidence_percent"),
            "uncertainty": payload.get("uncertainty"),
            "invalidation_condition": payload.get("invalidation") or payload.get("invalidation_condition"),
            "evidence_class": evidence_class,
            "grade": grade.get("overall_grade"),
            "assumptions": payload.get("assumptions") or {},
            "methodology_version": METHODOLOGY_VERSION,
            "methodology_versions": methodology_bundle(),
            "why_not": (payload.get("decision_truth") or {}).get("why_not"),
        }
        prereg = pre_register_decision(snapshot)
        decision_id = prereg["decision_id"]

    history_event = None
    new_state = payload.get("decision_truth_state") or payload.get("decision_state")
    if previous_decision_state and new_state and str(previous_decision_state) != str(new_state):
        history_event = record_history_event(
            previous_state=str(previous_decision_state),
            new_state=str(new_state),
            cause="decision_state_transition",
            evidence_delta={"changes": changes},
            methodology_version=METHODOLOGY_VERSION,
            decision_id=decision_id,
        )

    cherry = validate_performance_claim(
        {
            "decision_id": decision_id,
            "evidence_snapshot_hash": prereg.get("evidence_snapshot_hash") if prereg else None,
            "retroactive_horizon_change": payload.get("retroactive_horizon_change"),
            "retroactive_threshold_change": payload.get("retroactive_threshold_change"),
            "subset_selection": payload.get("subset_selection"),
            "subset_disclosed": payload.get("subset_disclosed"),
            "losses_omitted": payload.get("losses_omitted"),
            "post_outcome_preregistration": payload.get("post_outcome_preregistration"),
        }
    )

    pack = attach_methodology_versions(
        {
            "state": "AVAILABLE",
            "methodology_version": METHODOLOGY_VERSION,
            "evidence_class_context": evidence,
            "provenance": provenance,
            "calibration": calibration,
            "simulation": simulation,
            "evidence_grade": grade,
            "decision_changes": changes,
            "pre_registration": prereg,
            "decision_id": decision_id,
            "history_event": history_event,
            "anti_cherry_picking": cherry,
        }
    )
    return pack
