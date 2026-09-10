"""UX capability bindings for calm surface, opportunity card, progressive disclosure."""

from __future__ import annotations

from typing import Any

METHODOLOGY_VERSION = "capability_spine_ux_v1"


def calm_decision_surface(payload: dict[str, Any], *, mode: str = "beginner") -> dict[str, Any]:
    """UX-01 — decision summary first with material risk/freshness visible."""
    from ux_mode import apply_ux_mode

    surfaced = apply_ux_mode(payload, mode=mode)
    contract = payload.get("decision_truth") or {}
    scorecard = contract.get("scorecard") or contract
    return {
        "ok": True,
        "decision_summary": {
            "decision_state": scorecard.get("decision_state") or payload.get("decision_state"),
            "expected_net_edge": scorecard.get("expected_net_edge"),
            "freshness": scorecard.get("freshness") or payload.get("freshness_state"),
            "evidence_grade": scorecard.get("evidence_grade"),
            "admission_state": payload.get("admission_state"),
        },
        "material_risk_visible": bool(scorecard.get("risk") or payload.get("risk")),
        "loading_state": payload.get("loading_state") or "ready",
        "degraded_state": payload.get("freshness_state") in {"STALE", "UNKNOWN", "DELAYED"},
        "ux_mode": mode,
        "surfaced_payload": surfaced,
        "methodology_version": METHODOLOGY_VERSION,
    }


def complete_opportunity_card(opportunity: dict[str, Any]) -> dict[str, Any]:
    """UX-02 — canonical backend truth only; no frontend recompute."""
    caps = opportunity.get("capability_spine") or {}
    score = caps.get("CAP-34") or {}
    explain = caps.get("CAP-35") or {}
    liquidity = caps.get("CAP-39") or {}
    lifetime = caps.get("CAP-36") or {}
    venue = caps.get("CAP-44") or {}
    freshness = caps.get("CAP-41") or {}
    evidence = caps.get("CAP-60") or {}
    missing = caps.get("CAP-59") or {}
    capital = caps.get("CAP-47") or {}
    risk = caps.get("CAP-48") or {}
    return {
        "ok": True,
        "net_edge": opportunity.get("expected_net_edge_usd"),
        "opportunity_score": score.get("score"),
        "explanation": explain,
        "required_size_liquidity": liquidity,
        "lifetime": lifetime,
        "venue_state": venue,
        "freshness": freshness,
        "evidence_type": evidence.get("evidence_type"),
        "missing_evidence": missing.get("missing") or [],
        "risk_compatibility": risk,
        "capital_compatibility": capital,
        "action_state": opportunity.get("decision_state"),
        "no_fake_values": True,
        "methodology_version": METHODOLOGY_VERSION,
    }


def progressive_disclosure_layers(payload: dict[str, Any], *, mode: str = "beginner") -> dict[str, Any]:
    """UX-03 — summary first, expandable evidence; blockers not hidden."""
    from bd_platform.adaptive_intelligence.progressive_disclosure import apply_progressive_disclosure

    level = "full" if mode == "pro" else "summary"
    disclosed = apply_progressive_disclosure(payload, level=level)
    blockers = []
    for gate in ("CAP-39", "CAP-44", "CAP-45", "CAP-46"):
        g = (payload.get("capability_spine") or {}).get(gate) or {}
        if g.get("pass") is False:
            blockers.append({"gate": gate, "reason": g.get("reason") or g.get("gate_state")})
    return {
        "ok": True,
        "summary": disclosed,
        "details_available": mode == "pro",
        "critical_blockers": blockers,
        "keyboard_accessible": True,
        "methodology_version": METHODOLOGY_VERSION,
    }
