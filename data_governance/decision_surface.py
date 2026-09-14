"""Today's Decision Surface — data truth integrated user-facing surface."""

from __future__ import annotations

from typing import Any


def build_decision_surface(payload: dict[str, Any], *, lang: str = "en") -> dict[str, Any]:
    """Build sections A-G from spec §31 with data governance evidence."""
    dg = payload.get("data_governance") or {}
    dt = payload.get("decision_truth") or {}
    contract = dt.get("contract") or {}
    admission = dt.get("admission") or {}
    why_not = dt.get("why_not") or {}
    fresh = dg.get("freshness") or {}
    quality = dg.get("quality") or {}
    prov = dg.get("provenance") or {}

    state = str(
        payload.get("decision_truth_state")
        or admission.get("admission_state")
        or contract.get("decision_state")
        or ""
    )
    admitted = state in {"AVAILABLE", "ADMITTED"}
    why_text = why_not.get("human_explanation")
    if isinstance(why_text, dict):
        why_text = why_text.get("human_explanation") or str(why_text)
    return {
        "A_state": {
            "portfolio": payload.get("portfolio_summary") or {"status": "not_connected"},
            "risk_budget": (contract.get("risk") or dt.get("risk") or {}).get("risk_budget"),
            "decision_state": state,
        },
        "B_material_changes": payload.get("material_changes") or [],
        "C_admitted_opportunities": [payload] if admitted else [],
        "D_rejected": []
        if admitted
        else [
            {
                "reason": why_text,
                "failed_gates": admission.get("failed_gates") or contract.get("why_not"),
                "decision_state": state,
            }
        ],
        "E_pre_impact_warnings": (contract.get("risk") or dt.get("risk") or {}).get("pre_impact")
        or (contract.get("risk") or {}).get("portfolio_pre_impact"),
        "F_unknowns": _unknowns(payload, admission, fresh, quality, state),
        "G_evidence_strip": {
            "source_class": prov.get("lineage", {}).get("nodes", [{}])[0] if prov else "oracle",
            "as_of": fresh.get("as_of") or contract.get("detected_at"),
            "freshness": fresh.get("freshness_state") or contract.get("freshness_state"),
            "quality": quality.get("quality_state") or contract.get("data_quality_state"),
            "methodology_version": (contract.get("methodology_versions") or {}).get("net_edge"),
            "view_evidence": True,
        },
        "progressive_disclosure": True,
    }


def _unknowns(
    payload: dict[str, Any],
    admission: dict[str, Any],
    fresh: dict[str, Any],
    quality: dict[str, Any],
    state: str = "",
) -> list[str]:
    unknowns: list[str] = []
    state = state or str(admission.get("admission_state") or "")
    if state in {"ABSTAINED", "REJECTED", "DEGRADED", "UNAVAILABLE"}:
        unknowns.append("NO DECISION — insufficient evidence")
    if fresh.get("freshness_state") in {"STALE", "UNKNOWN"}:
        unknowns.append("STALE INPUT")
    if quality.get("quality_state") in {"CONFLICTING", "INSUFFICIENT"}:
        unknowns.append("SOURCE CONFLICT" if quality.get("quality_state") == "CONFLICTING" else "INSUFFICIENT EVIDENCE")
    if payload.get("source_conflict"):
        unknowns.append("SOURCE CONFLICT")
    return unknowns
