"""Internal SLO registry per source class — no fabricated external SLA."""

from __future__ import annotations

from typing import Any

from capability_spine.gates import FEATURE_FRESHNESS_SLO
from data_governance.registry import SourceClass

SLO_REGISTRY: dict[str, dict[str, Any]] = {
    SourceClass.ORDER_BOOK.value: {
        "freshness_target_s": 2,
        "availability_target": 0.995,
        "recovery_target_s": 30,
        "max_acceptable_gap_s": 5,
        "fallback_trigger": "stale_or_disconnect",
        "abstain_trigger": "unrecoverable_gap",
    },
    SourceClass.CEX_SPOT.value: {
        "freshness_target_s": 15,
        "availability_target": 0.99,
        "recovery_target_s": 60,
        "max_acceptable_gap_s": 30,
        "fallback_trigger": "primary_stale",
        "abstain_trigger": "all_sources_stale",
    },
    SourceClass.ONCHAIN_RPC.value: {
        "freshness_target_s": 30,
        "availability_target": 0.98,
        "recovery_target_s": 120,
        "max_acceptable_gap_s": 60,
        "fallback_trigger": "rpc_failover",
        "abstain_trigger": "unfinalized_when_required",
    },
    SourceClass.MACRO.value: {
        "freshness_target_s": 86400,
        "availability_target": 0.99,
        "recovery_target_s": 3600,
        "max_acceptable_gap_s": 86400,
        "fallback_trigger": "release_event",
        "abstain_trigger": "missing_release",
    },
}


def get_slo(source_class: str) -> dict[str, Any]:
    return SLO_REGISTRY.get(source_class, SLO_REGISTRY[SourceClass.CEX_SPOT.value])


def get_feature_slo(source: str, feature: str) -> dict[str, Any]:
    """Per-source/per-feature freshness SLO (CAP-41)."""
    key = f"{source}:{feature}"
    return FEATURE_FRESHNESS_SLO.get(key, {"source": source, "max_age_s": 60, "state_on_breach": "STALE"})


def slo_registry_status() -> dict[str, Any]:
    return {
        "classes_defined": list(SLO_REGISTRY.keys()),
        "feature_keys_defined": list(FEATURE_FRESHNESS_SLO.keys()),
        "count": len(SLO_REGISTRY),
        "feature_count": len(FEATURE_FRESHNESS_SLO),
        "false_external_sla_claims": [],
    }
