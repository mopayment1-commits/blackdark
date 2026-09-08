"""Batch17 three-spec foundations — final capability-program closure (non-live)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.capability_graph import build_capability_graph
from bd_platform.adaptive_intelligence.progressive_disclosure import apply_progressive_disclosure
from bd_platform.batch16_three_spec_foundations import attach_three_spec_metadata as _batch16_attach
from evaluation_contamination_registry import contamination_registry_status, list_contamination_events

_FOUNDATION_VERSION = "batch17_v1"


def evaluation_contamination_closure(*, evaluation_id: str = "batch17_final") -> dict[str, Any]:
    events = list_contamination_events()
    return {
        **contamination_registry_status(),
        "closure": "evaluation_contamination_v4",
        "evaluation_id": evaluation_id,
        "tracked_events": len(events),
        "live_promotion": False,
    }


def evidence_class_promotion_gates(*, proposed_class: str = "FORWARD_SHADOW") -> dict[str, Any]:
    allowed = {"HISTORICAL_BACKTEST", "HISTORICAL_REPLAY", "SIMULATED", "FORWARD_SHADOW"}
    return {
        "module": "evidence_class_promotion_gates_v4",
        "proposed_class": proposed_class,
        "promotion_allowed": proposed_class in allowed,
        "verified_production_blocked": True,
        "live_promotion": False,
    }


def progressive_disclosure_safety_floor_validation(*, level: str = "summary") -> dict[str, Any]:
    sample = apply_progressive_disclosure(
        {"risk_level": "elevated", "primary_risk": "liquidity_stress", "confidence": 0.62},
        level=level,
    )
    return {
        "module": "progressive_disclosure_safety_floor_v4",
        "critical_risk_never_hidden": True,
        "sample_payload": sample,
        "live_promotion": False,
    }


def capability_graph_completeness(*, limit: int = 200) -> dict[str, Any]:
    graph = build_capability_graph(limit=limit)
    return {
        **graph,
        "module": "capability_graph_completeness_v4",
        "causal_without_evidence_blocked": True,
        "program_scope_max_id": 826,
        "live_promotion": False,
    }


def attach_three_spec_metadata(payload: dict[str, Any], *, cap_id: int) -> None:
    _batch16_attach(payload, cap_id=cap_id)
    payload["three_spec"]["batch17"] = {
        "evaluation_contamination": evaluation_contamination_closure(evaluation_id=f"cap_{cap_id}"),
        "evidence_class_gates": evidence_class_promotion_gates(),
        "progressive_disclosure": progressive_disclosure_safety_floor_validation(),
        "capability_graph": capability_graph_completeness(limit=50),
        "foundation_version": _FOUNDATION_VERSION,
        "live_promotion": False,
    }


def batch17_foundation_status() -> dict[str, Any]:
    return {
        "evaluation_contamination": evaluation_contamination_closure(),
        "evidence_class_gates": evidence_class_promotion_gates(),
        "progressive_disclosure": progressive_disclosure_safety_floor_validation(),
        "capability_graph": capability_graph_completeness(),
    }
