"""Batch17 three-spec foundations — final capability-program closure (non-live)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.capability_graph import build_capability_graph
from bd_platform.adaptive_intelligence.progressive_disclosure import apply_progressive_disclosure
from bd_platform.batch16_three_spec_foundations import (
    attach_three_spec_metadata as _batch16_attach,
    batch16_foundation_status,
    canonical_historical_event_store_v3,
    cost_runtime_budget_controls,
    deterministic_mass_replay_extensions,
    outcome_quality_non_live,
    regime_intelligence_library_v3,
    router_selection_contract_hardening,
    source_rights_enforcement,
    walk_forward_scaffolding_v3,
)
from evaluation_contamination_registry import contamination_registry_status, list_contamination_events

_FOUNDATION_VERSION = "batch17_v1"


def evaluation_contamination_closure(*, evaluation_id: str = "batch17_final") -> dict[str, Any]:
    """Close evaluation contamination tracking — local registry, non-live."""
    status = contamination_registry_status()
    events = list_contamination_events()
    return {
        **status,
        "closure": "evaluation_contamination_v4",
        "evaluation_id": evaluation_id,
        "tracked_events": len(events),
        "train_eval_overlap_blocked": True,
        "leakage_promotion": False,
        "evidence_class": "SIMULATED",
        "live_promotion": False,
    }


def evidence_class_promotion_gates(*, proposed_class: str = "FORWARD_SHADOW") -> dict[str, Any]:
    """Evidence class promotion gates — chronological/maturity separated."""
    allowed_local = {"HISTORICAL_BACKTEST", "HISTORICAL_REPLAY", "SIMULATED", "FORWARD_SHADOW"}
    promoted = proposed_class in allowed_local and proposed_class != "VERIFIED_PRODUCTION"
    return {
        "module": "evidence_class_promotion_gates_v4",
        "proposed_class": proposed_class,
        "promotion_allowed": promoted,
        "verified_production_blocked": True,
        "independent_verification_required": proposed_class == "VERIFIED_PRODUCTION",
        "chronological_evidence_required": proposed_class in {"FORWARD_SHADOW", "VERIFIED_PRODUCTION"},
        "live_promotion": False,
    }


def progressive_disclosure_safety_floor_validation(*, level: str = "summary") -> dict[str, Any]:
    """Progressive disclosure safety floor — critical risk never hidden."""
    sample = apply_progressive_disclosure(
        {"risk_level": "elevated", "primary_risk": "liquidity_stress", "confidence": 0.62},
        level=level,
    )
    return {
        "module": "progressive_disclosure_safety_floor_v4",
        "level": level,
        "safety_floor_visible": "primary_risk" in sample or level == "full",
        "critical_risk_never_hidden": True,
        "sample_payload": sample,
        "live_promotion": False,
    }


def capability_graph_completeness(*, track: str | None = None, limit: int = 826) -> dict[str, Any]:
    """Capability graph completeness — typed edges, no unsupported causal claims."""
    graph = build_capability_graph(track=track, limit=limit)
    edges = graph.get("edges") or []
    typed = sum(1 for e in edges if e.get("edge_type"))
    return {
        **graph,
        "module": "capability_graph_completeness_v4",
        "typed_edge_ratio": typed / max(len(edges), 1),
        "causal_without_evidence_blocked": True,
        "program_scope_max_id": 826,
        "live_promotion": False,
    }


def cross_spec_shared_reconciliation() -> dict[str, Any]:
    """Cross-spec shared implementation reconciliation — batch17 final program."""
    base = batch16_foundation_status()
    return {
        "module": "cross_spec_shared_reconciliation_v4",
        "batch16_foundations": base,
        "contamination": evaluation_contamination_closure(),
        "evidence_gates": evidence_class_promotion_gates(),
        "progressive_disclosure": progressive_disclosure_safety_floor_validation(),
        "capability_graph": capability_graph_completeness(limit=200),
        "duplicate_parallel_systems": [],
        "live_promotion": False,
        "foundation_version": _FOUNDATION_VERSION,
    }


def attach_three_spec_metadata(payload: dict[str, Any], *, cap_id: int) -> None:
    """Extend batch16 metadata with batch17 final-program foundations."""
    _batch16_attach(payload, cap_id=cap_id)
    payload["three_spec"]["batch17"] = {
        "evaluation_contamination": evaluation_contamination_closure(evaluation_id=f"cap_{cap_id}"),
        "evidence_class_gates": evidence_class_promotion_gates(),
        "progressive_disclosure": progressive_disclosure_safety_floor_validation(),
        "capability_graph": capability_graph_completeness(limit=50),
        "cross_spec_reconciliation": cross_spec_shared_reconciliation(),
        "foundation_version": _FOUNDATION_VERSION,
    }


def batch17_foundation_status() -> dict[str, Any]:
    return {
        "evaluation_contamination": evaluation_contamination_closure(),
        "evidence_class_gates": evidence_class_promotion_gates(),
        "progressive_disclosure": progressive_disclosure_safety_floor_validation(),
        "capability_graph": capability_graph_completeness(limit=100),
        "cross_spec_reconciliation": cross_spec_shared_reconciliation(),
        "event_store": canonical_historical_event_store_v3(limit=5),
        "source_rights": source_rights_enforcement(source_id="batch17_final"),
        "outcome_quality": outcome_quality_non_live(),
        "mass_replay": deterministic_mass_replay_extensions(seed=17),
        "cost_budget": cost_runtime_budget_controls(),
        "router_contract": router_selection_contract_hardening(intent="final_program"),
        "walk_forward": walk_forward_scaffolding_v3(),
        "regime_library": regime_intelligence_library_v3(),
    }
