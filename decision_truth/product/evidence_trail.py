"""DTS-047 — Full Evidence Trail from canonical contract (no UI store duplication)."""

from __future__ import annotations

from typing import Any


TRAIL_FIELDS = (
    "source",
    "timestamp",
    "freshness",
    "data_quality",
    "calculation",
    "cost_autopsy",
    "net_edge",
    "execution_feasibility",
    "capacity",
    "risk",
    "portfolio_impact",
    "evidence_grade",
    "evidence_class",
    "uncertainty",
    "simulation",
    "calibration",
    "invalidation_condition",
    "decision_changes",
    "outcome_history",
)


def build_full_evidence_trail(payload: dict[str, Any]) -> dict[str, Any]:
    """Assemble drill-down trail from canonical decision truth — no UI copy."""
    dt = payload.get("decision_truth") or {}
    contract = dt.get("contract") or {}
    lifecycle = dt.get("evidence_lifecycle") or payload.get("evidence_lifecycle") or {}
    dg = payload.get("data_governance") or {}
    prov = contract.get("provenance_context") or dg.get("provenance") or {}
    fresh = contract.get("freshness") or dg.get("freshness") or {}
    net = contract.get("net_edge") or payload.get("net_edge_truth") or {}

    trail = {
        "source": {
            "value": prov.get("source") or payload.get("source"),
            "provenance": prov,
            "available": bool(prov or payload.get("source")),
        },
        "timestamp": {
            "value": fresh.get("as_of") or payload.get("timestamp"),
            "available": bool(fresh.get("as_of") or payload.get("timestamp")),
        },
        "freshness": {"value": fresh, "available": bool(fresh)},
        "data_quality": {
            "value": dg.get("quality") or contract.get("data_quality_state"),
            "available": bool(dg.get("quality") or contract.get("data_quality_state")),
        },
        "calculation": {
            "value": {
                "methodology_version": contract.get("methodology_version"),
                "assumptions": contract.get("assumptions"),
            },
            "available": bool(contract.get("methodology_version")),
        },
        "cost_autopsy": {
            "value": net.get("cost_autopsy") or net.get("components"),
            "available": bool(net.get("cost_autopsy") or net.get("components")),
        },
        "net_edge": {"value": net, "available": bool(net)},
        "execution_feasibility": {
            "value": contract.get("execution_feasibility"),
            "available": bool(contract.get("execution_feasibility")),
        },
        "capacity": {"value": contract.get("capacity"), "available": bool(contract.get("capacity"))},
        "risk": {"value": contract.get("risk"), "available": bool(contract.get("risk"))},
        "portfolio_impact": {
            "value": (contract.get("risk") or {}).get("portfolio_pre_impact"),
            "available": bool((contract.get("risk") or {}).get("portfolio_pre_impact")),
        },
        "evidence_grade": {
            "value": contract.get("grade"),
            "available": contract.get("grade") not in {None, "UNAVAILABLE"},
        },
        "evidence_class": {
            "value": contract.get("evidence_class"),
            "available": contract.get("evidence_class") not in {None, "UNAVAILABLE"},
        },
        "uncertainty": {"value": contract.get("uncertainty"), "available": bool(contract.get("uncertainty"))},
        "simulation": {
            "value": lifecycle.get("simulation"),
            "available": str((lifecycle.get("simulation") or {}).get("state")) == "AVAILABLE",
            "not_applicable": (lifecycle.get("simulation") or {}).get("state") == "NOT_APPLICABLE",
        },
        "calibration": {
            "value": lifecycle.get("calibration"),
            "available": str((lifecycle.get("calibration") or {}).get("state")) in {"AVAILABLE", "CALIBRATION_INSUFFICIENT_DATA"},
        },
        "invalidation_condition": {
            "value": contract.get("invalidation_condition"),
            "available": bool(contract.get("invalidation_condition")),
        },
        "decision_changes": {
            "value": lifecycle.get("decision_changes") or lifecycle.get("history_event"),
            "available": bool(lifecycle.get("decision_changes") or lifecycle.get("history_event")),
        },
        "outcome_history": {
            "value": lifecycle.get("pre_registration") or lifecycle.get("ledger"),
            "available": bool(lifecycle.get("pre_registration")),
        },
    }

    gaps = [k for k in TRAIL_FIELDS if not _field_present(trail.get(k))]
    return {
        "trail": trail,
        "decision_id": payload.get("decision_id"),
        "canonical_owner": "decision_truth.contract",
        "ui_store_duplication": False,
        "gaps": gaps,
        "complete": len(gaps) == 0,
        "methodology_version": "dts-p5-evidence-trail-1.0",
    }


def _field_present(entry: dict[str, Any] | None) -> bool:
    if not entry:
        return False
    if entry.get("not_applicable"):
        return True
    return bool(entry.get("available"))
