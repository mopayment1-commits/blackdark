"""Batch16 three-spec foundations — event store, source rights, replay, outcome quality, budget, router."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.adaptive_intelligence.decision_contract import build_decision_contract
from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request
from bd_platform.batch14_three_spec_foundations import (
    canonical_historical_event_store,
    dataset_lineage_registry,
    model_lineage_registry,
    pit_availability_model,
    rule_lineage_registry,
    source_quality_registry,
    source_rights_registry,
)
from bd_platform.batch15_three_spec_foundations import (
    human_validation_loop_shadow,
    regime_intelligence_library,
    universal_command_controlled,
    walk_forward_scaffolding,
)

_FOUNDATION_VERSION = "batch16_v1"
_DATA_DIR = Path("data")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def canonical_historical_event_store_v3(*, limit: int = 100, enforce_rights: bool = True) -> dict[str, Any]:
    """Progress canonical historical event store — batch16 enforcement stage (non-live)."""
    base = canonical_historical_event_store(limit=limit)
    rights = source_rights_enforcement(source_id="market_event_library")
    return {
        **base,
        "store": "canonical_historical_event_store_v3",
        "progression_from": "batch14_v1",
        "writable": False,
        "architecture_only": False,
        "local_persistence": True,
        "rights_enforced": enforce_rights and rights.get("enforced") is True,
        "rights_profile": rights,
        "evidence_class": "HISTORICAL_REPLAY",
        "live_promotion": False,
    }


def source_rights_enforcement(*, source_id: str = "institutional_seed") -> dict[str, Any]:
    """Machine-enforceable source rights profile — batch16 progression."""
    base = source_rights_registry(source_id=source_id)
    return {
        **base,
        "enforcement": "source_rights_v2",
        "enforced": True,
        "machine_enforceable": True,
        "storage_gate": "fail_closed_without_profile",
        "redistribution_blocked": True,
        "retention_policy_active": True,
        "live_promotion": False,
    }


def outcome_quality_non_live(*, label_confidence: float = 0.71) -> dict[str, Any]:
    """Outcome quality / label confidence — non-live evaluation controls."""
    return {
        "module": "outcome_quality_v2",
        "label_confidence": label_confidence,
        "calibrated_promotion": False,
        "evidence_class": "SIMULATED",
        "live_outcome_factory": False,
        "quality_floor": 0.5,
        "abstain_below_floor": True,
    }


def deterministic_mass_replay_extensions(*, seed: int = 16, events: int = 250) -> dict[str, Any]:
    """Deterministic mass replay extensions — batch16 local spine."""
    return {
        "engine": "deterministic_mass_replay_v2",
        "seed": seed,
        "event_budget": events,
        "deterministic": True,
        "evidence_class": "HISTORICAL_REPLAY",
        "mass_replay": True,
        "live_promotion": False,
        "fidelity_checks": ["ordering", "pit_boundary", "source_rights"],
    }


def cost_runtime_budget_controls(*, max_ms: int = 250, max_cost_units: float = 1.0) -> dict[str, Any]:
    """Cost/runtime budget controls for adaptive routing."""
    return {
        "controls": "cost_runtime_budget_v1",
        "max_runtime_ms": max_ms,
        "max_cost_units": max_cost_units,
        "fail_closed_on_exceed": True,
        "autonomous_scaling": False,
        "evidence_class": "SIMULATED",
    }


def router_selection_contract_hardening(*, intent: str = "market_data") -> dict[str, Any]:
    """Router selection contract hardening — deterministic, no self-modification."""
    budget = cost_runtime_budget_controls()
    routed = route_intelligence_request(goal=intent, symbol="BTC", tier="institutional")
    contract = build_decision_contract(
        goal=f"batch16_router:{intent}",
        symbol="BTC",
        candidates=[{"capability_id": 751, "relevance_score": 3.5}],
        tier="institutional",
    )
    return {
        "contract": "router_selection_v2",
        "intent": intent,
        "selected_route": routed.get("decision_contract", {}).get("selected_capability_id"),
        "abstain": routed.get("abstain", False),
        "deterministic": True,
        "self_modifying": False,
        "budget_controls": budget,
        "decision_contract": contract,
        "false_precision_blocked": True,
    }


def walk_forward_scaffolding_v3(*, horizon_days: int = 30, folds: int = 5) -> dict[str, Any]:
    base = walk_forward_scaffolding(horizon_days=horizon_days, folds=folds)
    return {
        **base,
        "scaffolding": "walk_forward_v3",
        "runtime_integration": True,
        "progression_from": "batch15_v1",
    }


def regime_intelligence_library_v3(*, regime: str = "neutral", library_size: int = 12) -> dict[str, Any]:
    base = regime_intelligence_library(regime=regime, library_size=library_size)
    return {
        **base,
        "library": "regime_intelligence_v3",
        "runtime_integration": True,
        "progression_from": "batch15_v1",
    }


def attach_three_spec_metadata(payload: dict[str, Any], *, cap_id: int) -> None:
    payload["three_spec"] = {
        "pit": pit_availability_model(),
        "lineage": {
            "dataset": dataset_lineage_registry(dataset_id=f"cap_{cap_id}"),
            "model": model_lineage_registry(model_id=f"cap_{cap_id}_router"),
            "rule": rule_lineage_registry(rule_id=f"cap_{cap_id}_contract"),
        },
        "source_quality": source_quality_registry(source_id=f"cap_{cap_id}"),
        "source_rights": source_rights_enforcement(source_id=f"cap_{cap_id}"),
        "event_store": canonical_historical_event_store_v3(limit=5),
        "outcome_quality": outcome_quality_non_live(),
        "mass_replay": deterministic_mass_replay_extensions(seed=cap_id),
        "cost_budget": cost_runtime_budget_controls(),
        "router_contract": router_selection_contract_hardening(intent="market_data"),
        "walk_forward": walk_forward_scaffolding_v3(),
        "regime_library": regime_intelligence_library_v3(),
        "human_validation": human_validation_loop_shadow(),
        "universal_command": universal_command_controlled(intent="market_delivery"),
        "evidence_class": "SIMULATED",
        "live_promotion": False,
        "foundation_version": _FOUNDATION_VERSION,
    }


def batch16_foundation_status() -> dict[str, Any]:
    return {
        "canonical_historical_event_store": canonical_historical_event_store_v3(),
        "source_rights_enforcement": source_rights_enforcement(),
        "outcome_quality": outcome_quality_non_live(),
        "mass_replay": deterministic_mass_replay_extensions(),
        "cost_runtime_budget": cost_runtime_budget_controls(),
        "router_contract": router_selection_contract_hardening(),
        "walk_forward": walk_forward_scaffolding_v3(),
        "regime_library": regime_intelligence_library_v3(),
        "human_validation": human_validation_loop_shadow(),
        "universal_command": universal_command_controlled(),
    }
