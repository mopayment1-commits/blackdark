"""DTS-034 — Daily Evidence Autopsy (WHAT / WHY / RISKS)."""

from __future__ import annotations

from typing import Any


def build_daily_evidence_autopsy(payload: dict[str, Any], *, lang: str = "en") -> dict[str, Any]:
    """Build grounded daily brief structure from canonical facts."""
    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    lifecycle = ((payload.get("decision_truth") or {}).get("evidence_lifecycle") or {})
    changes = payload.get("material_changes") or lifecycle.get("decision_changes") or []

    what_changed = []
    for ch in _as_list(changes):
        item = _grounded_item(
            title=str(ch.get("field") or ch.get("change") or ch.get("title") or "material_change"),
            detail=str(ch.get("detail") or ch.get("reason") or ""),
            evidence_ref=_evidence_ref(payload, contract, ch),
        )
        if item["grounded"]:
            what_changed.append(item)

    if not what_changed and payload.get("decision_truth_state"):
        what_changed.append(
            _grounded_item(
                title="decision_state",
                detail=f"Decision state is {payload['decision_truth_state']}",
                evidence_ref=_evidence_ref(payload, contract, {}),
            )
        )

    why_matters = []
    state = str(payload.get("decision_truth_state") or "")
    if state in {"REJECTED", "ABSTAINED", "DEGRADED"}:
        why_matters.append(
            _grounded_item(
                title="admission_outcome",
                detail=f"Opportunity {state.lower()} — economics, execution, or evidence gates did not support admission.",
                evidence_ref=_evidence_ref(payload, contract, {"field": "why_not"}),
            )
        )
    elif state == "AVAILABLE":
        net = contract.get("net_edge") or {}
        why_matters.append(
            _grounded_item(
                title="admitted_opportunity",
                detail=f"Net edge after costs: {net.get('expected_net_edge_bps', 'N/A')} bps",
                evidence_ref=_evidence_ref(payload, contract, {"field": "net_edge"}),
            )
        )

    risks = []
    inv = contract.get("invalidation_condition")
    if inv:
        risks.append(
            _grounded_item(
                title="invalidation",
                detail=str(inv),
                evidence_ref=_evidence_ref(payload, contract, {"field": "invalidation_condition"}),
            )
        )
    pre = (contract.get("risk") or {}).get("portfolio_pre_impact")
    if pre:
        risks.append(
            _grounded_item(
                title="portfolio_pre_impact",
                detail=str(pre.get("summary") or pre.get("state") or "pre-impact evaluated"),
                evidence_ref=_evidence_ref(payload, contract, {"field": "portfolio_pre_impact"}),
            )
        )

    return {
        "structure": ["WHAT_CHANGED", "WHY_IT_MATTERS", "RISKS_INVALIDATION"],
        "WHAT_CHANGED": what_changed,
        "WHY_IT_MATTERS": why_matters,
        "RISKS_INVALIDATION": risks,
        "lang": lang,
        "generic_ai_prose": False,
        "all_material_items_grounded": all(
            item.get("grounded") for section in (what_changed, why_matters, risks) for item in section
        ),
        "methodology_version": "dts-p5-daily-evidence-autopsy-1.0",
    }


def _as_list(changes: Any) -> list[dict[str, Any]]:
    if isinstance(changes, list):
        return [c if isinstance(c, dict) else {"change": str(c)} for c in changes]
    return []


def _grounded_item(title: str, detail: str, evidence_ref: dict[str, Any]) -> dict[str, Any]:
    grounded = bool(evidence_ref.get("source") or evidence_ref.get("decision_id"))
    return {
        "title": title,
        "detail": detail,
        "evidence_ref": evidence_ref,
        "grounded": grounded,
        "drill_down_available": grounded,
    }


def _evidence_ref(payload: dict[str, Any], contract: dict[str, Any], change: dict[str, Any]) -> dict[str, Any]:
    prov = contract.get("provenance_context") or {}
    fresh = contract.get("freshness") or {}
    return {
        "source": prov.get("source") or payload.get("source") or "decision_truth_contract",
        "timestamp": fresh.get("as_of") or payload.get("timestamp"),
        "freshness": fresh.get("state") or fresh.get("freshness_state"),
        "evidence_class": contract.get("evidence_class"),
        "methodology_version": contract.get("methodology_version"),
        "decision_id": payload.get("decision_id"),
        "field": change.get("field"),
    }
