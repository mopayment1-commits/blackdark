"""DTS-044 — Reject bad opportunities from real canonical decision records."""

from __future__ import annotations

from typing import Any


def build_reject_bad_opportunity_proof(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Build reject proof only from real governed decision — no fabricated examples."""
    state = str(payload.get("decision_truth_state") or "")
    if state not in {"REJECTED", "ABSTAINED", "DEGRADED"}:
        return None

    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    net = contract.get("net_edge") or payload.get("net_edge_truth") or {}
    exec_feas = contract.get("execution_feasibility") or {}
    if not contract.get("decision_state") and not net:
        return None

    raw_edge = net.get("gross_edge_bps") or net.get("raw_opportunity_bps") or payload.get("raw_opportunity_bps")
    return {
        "flow": ["RAW_OPPORTUNITY", "COST_EXECUTION_RISK_EVIDENCE", "BLACKDARK_REJECTED"],
        "raw_opportunity": {
            "gross_edge_bps": raw_edge,
            "symbol": payload.get("symbol"),
            "source": "canonical_decision_record",
        },
        "economic_reality": {
            "expected_net_edge_bps": net.get("expected_net_edge_bps"),
            "realizable_net_edge_bps": net.get("realizable_net_edge_bps"),
            "cost_autopsy": net.get("cost_autopsy") or net.get("components"),
        },
        "execution": {
            "score": exec_feas.get("score"),
            "fill_probability": payload.get("fill_probability"),
            "reason_codes": exec_feas.get("reason_codes"),
        },
        "risk_evidence": {
            "why_not": contract.get("why_not"),
            "grade": contract.get("grade"),
            "evidence_class": contract.get("evidence_class"),
        },
        "verdict": state,
        "decision_id": payload.get("decision_id"),
        "fabricated": False,
        "derived_from": "canonical_govern_pipeline",
        "methodology_version": "dts-p5-reject-proof-1.0",
    }
