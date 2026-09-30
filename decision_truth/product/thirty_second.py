"""DTS-048 — 30-second truth surface from canonical outputs."""

from __future__ import annotations

from typing import Any


def build_thirty_second_truth(payload: dict[str, Any], *, six_heroes: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compose 30-second grasp from governed DTS — no independent summary logic."""
    heroes = (six_heroes or {}).get("heroes") or {}
    contract = ((payload.get("decision_truth") or {}).get("contract") or {})
    state = str(payload.get("decision_truth_state") or "UNAVAILABLE")
    no_dec = payload.get("decision_action") == "NO_DECISION" or state != "AVAILABLE"

    capital = (heroes.get("my_capital") or {}).get("data") or {"status": "not_connected"}
    main_risk = (heroes.get("main_risk") or {}).get("data") or contract.get("risk")
    best_opp = (heroes.get("best_verified_opportunity") or {}).get("data")
    market = (heroes.get("market_state") or {}).get("data") or {"symbol": payload.get("symbol")}

    changes = payload.get("material_changes") or []
    lifecycle = ((payload.get("decision_truth") or {}).get("evidence_lifecycle") or {})
    if not changes:
        changes = lifecycle.get("decision_changes") or []

    confidence = {
        "decision_state": state,
        "grade": contract.get("grade"),
        "abstaining": no_dec,
        "uncertainty": contract.get("uncertainty"),
    }

    return {
        "grasp_seconds_target": 30,
        "capital_position": capital,
        "main_risk": main_risk,
        "best_verified_opportunity": best_opp,
        "worth_attention": state == "AVAILABLE" and not no_dec,
        "what_changed": changes[:3] if changes else [{"note": "no_material_changes_recorded"}],
        "system_confidence": confidence,
        "derived_from": "canonical_decision_truth",
        "independent_summary": False,
        "methodology_version": "dts-p5-thirty-second-truth-1.0",
    }
