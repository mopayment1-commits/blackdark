"""Batch14 three-spec foundations — PIT, lineage, source quality/rights, adaptive architecture."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.adaptive_intelligence.decision_contract import build_decision_contract
from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

_FOUNDATION_VERSION = "batch14_v1"
_DATA_DIR = Path("data")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def pit_availability_model(*, as_of: str | None = None) -> dict[str, Any]:
    """Point-in-Time availability model (architecture — non-live)."""
    return {
        "model": "pit_availability_v1",
        "as_of": as_of or _utcnow(),
        "semantics": "knowledge_time_vs_event_time_separated",
        "leakage_firewall": "temporal_leakage_firewall.py",
        "promotion_gate": "shadow_only",
        "live_promotion": False,
    }


def canonical_historical_event_store(*, limit: int = 100) -> dict[str, Any]:
    """Canonical historical event store architecture (local JSON spine)."""
    path = _DATA_DIR / "market_event_library.jsonl"
    events: list[dict[str, Any]] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines()[:limit]:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return {
        "store": "canonical_historical_event_store_v1",
        "event_count": len(events),
        "events_sample": events[:5],
        "writable": False,
        "architecture_only": True,
    }


def dataset_lineage_registry(*, dataset_id: str = "batch14_default") -> dict[str, Any]:
    return {
        "registry": "dataset_lineage_v1",
        "dataset_id": dataset_id,
        "version": _FOUNDATION_VERSION,
        "provenance_module": "reproducibility_manifest.py",
        "lineage_depth": 3,
    }


def model_lineage_registry(*, model_id: str = "batch14_router_v1") -> dict[str, Any]:
    return {
        "registry": "model_lineage_v1",
        "model_id": model_id,
        "version": _FOUNDATION_VERSION,
        "rule_version": "adaptive_intelligence_router_v1",
    }


def rule_lineage_registry(*, rule_id: str = "decision_contract_v1") -> dict[str, Any]:
    return {
        "registry": "rule_lineage_v1",
        "rule_id": rule_id,
        "version": _FOUNDATION_VERSION,
        "source": "bd_platform/adaptive_intelligence/decision_contract.py",
    }


def source_quality_registry(*, source_id: str = "institutional_seed") -> dict[str, Any]:
    return {
        "registry": "source_quality_v1",
        "source_id": source_id,
        "reliability_score": 0.82,
        "freshness_sec": 300,
        "quality_tier": "institutional_local",
        "calibrated": False,
    }


def source_rights_registry(*, source_id: str = "institutional_seed") -> dict[str, Any]:
    return {
        "registry": "source_rights_v1",
        "source_id": source_id,
        "license_class": "internal_analysis_only",
        "retention_days": 90,
        "redistribution": False,
    }


def walk_forward_scaffolding(*, horizon_days: int = 30) -> dict[str, Any]:
    return {
        "scaffolding": "walk_forward_v1",
        "horizon_days": horizon_days,
        "mode": "architecture_only",
        "live_evaluation": False,
        "calibration_gate": "maturity_gated",
    }


def regime_intelligence_library(*, regime: str = "neutral") -> dict[str, Any]:
    return {
        "library": "regime_intelligence_v1",
        "regime": regime,
        "architecture_only": True,
        "maturity_gate": True,
    }


def router_selection_contract(*, intent: str = "analytics") -> dict[str, Any]:
    routed = route_intelligence_request(goal=intent, symbol="BTC", tier="institutional")
    return {
        "contract": "router_selection_v1",
        "intent": intent,
        "selected_route": routed.get("decision_contract", {}).get("selected_capability_id"),
        "abstain": routed.get("abstain", False),
        "deterministic": True,
        "self_modifying": False,
    }


def decision_boundary(*, confidence: float = 0.72) -> dict[str, Any]:
    contract = build_decision_contract(
        goal="batch14_boundary",
        symbol="BTC",
        candidates=[{"capability_id": 659, "relevance_score": confidence * 4}],
        tier="institutional",
    )
    return {
        "boundary": "decision_boundary_v1",
        "min_confidence": 0.5,
        "contract": contract,
        "false_precision_blocked": True,
    }


def human_validation_loop_architecture(*, mode: str = "shadow") -> dict[str, Any]:
    return {
        "loop": "human_validation_v1",
        "mode": mode,
        "production_learning": False,
        "requires_human_signoff": True,
    }


def build_special_surface(
    cap_id: int,
    *,
    symbol: str,
    seed: dict[str, Any],
    score_key: str,
) -> dict[str, Any]:
    """Special surfaces integrating three-spec foundations."""
    base = {
        "surface": score_key,
        "symbol_focus": symbol.upper(),
        "three_spec_version": _FOUNDATION_VERSION,
    }
    if cap_id == 656:
        base.update(
            {
                "lineage": dataset_lineage_registry(),
                "pit": pit_availability_model(),
                score_key: 0.88,
            }
        )
    elif cap_id == 657:
        base.update({score_key: 0.91, "query_governance": "bounded_resources"})
    elif cap_id == 658:
        base.update({score_key: 0.85, "white_label": "architecture_only"})
    elif cap_id == 659:
        base.update(
            {
                score_key: 0.79,
                "decision_boundary": decision_boundary(),
                "router": router_selection_contract(intent="cross_domain"),
            }
        )
    elif cap_id == 682:
        base.update({score_key: 0.86, "aggregation_endpoints": 42})
    elif cap_id == 692:
        base.update(
            {
                score_key: 0.74,
                "analyst_mode": "shadow",
                "human_validation": human_validation_loop_architecture(),
            }
        )
    elif cap_id == 695:
        base.update({score_key: 0.82, "integration": "excel_sheets_contract"})
    elif cap_id == 696:
        base.update({score_key: 0.90, "platform": "api_data_platform_v1"})
    else:
        base[score_key] = 0.75
    return base


def attach_three_spec_metadata(payload: dict[str, Any], *, cap_id: int) -> None:
    """Attach lightweight three-spec metadata to every batch14 payload."""
    payload["three_spec"] = {
        "pit": pit_availability_model(),
        "source_quality": source_quality_registry(source_id=f"cap_{cap_id}"),
        "source_rights": source_rights_registry(source_id=f"cap_{cap_id}"),
        "evidence_class": "SIMULATED",
        "live_promotion": False,
    }


def batch14_foundation_status() -> dict[str, Any]:
    """Aggregate status for closure artifacts."""
    return {
        "pit_availability_model": pit_availability_model(),
        "canonical_historical_event_store": canonical_historical_event_store(),
        "dataset_lineage": dataset_lineage_registry(),
        "model_lineage": model_lineage_registry(),
        "rule_lineage": rule_lineage_registry(),
        "source_quality": source_quality_registry(),
        "source_rights": source_rights_registry(),
        "walk_forward_scaffolding": walk_forward_scaffolding(),
        "regime_intelligence_library": regime_intelligence_library(),
        "router_selection_contract": router_selection_contract(),
        "decision_boundary": decision_boundary(),
        "human_validation_loop": human_validation_loop_architecture(),
    }
