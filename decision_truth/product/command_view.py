"""DTS-026 — Optional Command View (high-density, not default)."""

from __future__ import annotations

from typing import Any


def build_command_view(payload: dict[str, Any], *, enabled: bool = False) -> dict[str, Any] | None:
    """Assemble optional command view from canonical outputs only."""
    if not enabled:
        return None

    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    dt = payload.get("decision_truth") or {}
    product = dt.get("product_experience") or {}

    return {
        "enabled": True,
        "optional": True,
        "not_default": True,
        "portfolio": payload.get("portfolio_summary") or payload.get("portfolio_risk"),
        "market": {
            "symbol": payload.get("symbol"),
            "regime": payload.get("regime"),
            "freshness": contract.get("freshness"),
        },
        "opportunities": {
            "current_state": payload.get("decision_truth_state"),
            "contract_summary": {
                "net_edge": contract.get("net_edge"),
                "execution_feasibility": contract.get("execution_feasibility"),
                "grade": contract.get("grade"),
            },
        },
        "risk": contract.get("risk"),
        "evidence": {
            "grade": contract.get("grade"),
            "evidence_class": contract.get("evidence_class"),
            "lifecycle": dt.get("evidence_lifecycle"),
        },
        "alerts": payload.get("alerts") or payload.get("in_app_alerts") or [],
        "rejection_engine": product.get("rejection_engine"),
        "derived_from": "canonical_decision_truth",
        "parallel_logic": False,
        "methodology_version": "dts-p5-command-view-1.0",
    }
