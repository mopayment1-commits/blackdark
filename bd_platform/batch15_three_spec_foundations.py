"""Batch15 three-spec foundations — progression from Batch14 architecture/shadow stages."""

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

_FOUNDATION_VERSION = "batch15_v1"
_DATA_DIR = Path("data")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def walk_forward_scaffolding(*, horizon_days: int = 30, folds: int = 5) -> dict[str, Any]:
    """Walk-forward evaluation scaffolding — batch15 progression (still architecture-only)."""
    return {
        "scaffolding": "walk_forward_v2",
        "horizon_days": horizon_days,
        "folds": folds,
        "mode": "architecture_only",
        "live_evaluation": False,
        "calibration_gate": "maturity_gated",
        "evidence_class": "SIMULATED",
        "progression_from": "batch14_v1",
    }


def regime_intelligence_library(*, regime: str = "neutral", library_size: int = 12) -> dict[str, Any]:
    """Regime intelligence library — architecture-only progression."""
    return {
        "library": "regime_intelligence_v2",
        "regime": regime,
        "regime_count": library_size,
        "architecture_only": True,
        "maturity_gate": True,
        "live_promotion": False,
        "progression_from": "batch14_v1",
    }


def human_validation_loop_shadow(*, mode: str = "shadow") -> dict[str, Any]:
    """Human validation loop — shadow progression with task templates."""
    return {
        "loop": "human_validation_v2",
        "mode": mode,
        "production_learning": False,
        "requires_human_signoff": True,
        "task_templates": ["comprehension_check", "task_success_rate", "abstain_review"],
        "calibrated_promotion": False,
    }


def universal_command_controlled(*, intent: str = "analytics") -> dict[str, Any]:
    """Universal command — controlled implementation (deterministic routing, no autonomous learning)."""
    routed = route_intelligence_request(goal=intent, symbol="BTC", tier="institutional")
    return {
        "command": "universal_command_v1",
        "intent": intent,
        "controlled": True,
        "autonomous_learning": False,
        "selected_route": routed.get("decision_contract", {}).get("selected_capability_id"),
        "abstain": routed.get("abstain", False),
        "decision_contract": build_decision_contract(
            goal=f"universal_command:{intent}",
            symbol="BTC",
            candidates=[{"capability_id": 702, "relevance_score": 3.0}],
            tier="institutional",
        ),
    }


def attach_three_spec_metadata(payload: dict[str, Any], *, cap_id: int) -> None:
    """Attach batch15 three-spec metadata to every facade payload."""
    payload["three_spec"] = {
        "pit": pit_availability_model(),
        "lineage": {
            "dataset": dataset_lineage_registry(dataset_id=f"cap_{cap_id}"),
            "model": model_lineage_registry(model_id=f"cap_{cap_id}_router"),
            "rule": rule_lineage_registry(rule_id=f"cap_{cap_id}_contract"),
        },
        "source_quality": source_quality_registry(source_id=f"cap_{cap_id}"),
        "source_rights": source_rights_registry(source_id=f"cap_{cap_id}"),
        "walk_forward": walk_forward_scaffolding(),
        "regime_library": regime_intelligence_library(),
        "human_validation": human_validation_loop_shadow(),
        "universal_command": universal_command_controlled(intent="risk_data"),
        "event_store_sample": canonical_historical_event_store(limit=3),
        "evidence_class": "SIMULATED",
        "live_promotion": False,
        "foundation_version": _FOUNDATION_VERSION,
    }


def batch15_foundation_status() -> dict[str, Any]:
    """Status snapshot for tests and closure evidence."""
    return {
        "pit_availability_model": pit_availability_model(),
        "walk_forward_scaffolding": walk_forward_scaffolding(),
        "regime_intelligence_library": regime_intelligence_library(),
        "human_validation_loop": human_validation_loop_shadow(),
        "universal_command": universal_command_controlled(),
        "dataset_lineage": dataset_lineage_registry(),
        "source_quality": source_quality_registry(),
        "source_rights": source_rights_registry(),
    }
