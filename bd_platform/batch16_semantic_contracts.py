"""Batch16 semantic contracts for canonical-reuse facades 751-800."""

from __future__ import annotations

from typing import Any

from bd_platform.batch16_membership import BATCH16_IDS, CANONICAL_DUPLICATE_TARGETS

_REQUIRED = frozenset({
    "ok", "capability_id", "canonical_reuse_of", "facade_layer", "analysis_only", "three_spec",
})


def contract_for(capability_id: int) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "classification": "E. CANONICAL_DUPLICATE_REUSE",
        "canonical_owner": CANONICAL_DUPLICATE_TARGETS[capability_id],
        "required_keys": _REQUIRED,
        "consumer": "institutional_api",
        "entitlement_tier": "institutional",
    }


def all_contracts() -> dict[int, dict[str, Any]]:
    return {cid: contract_for(cid) for cid in BATCH16_IDS}
