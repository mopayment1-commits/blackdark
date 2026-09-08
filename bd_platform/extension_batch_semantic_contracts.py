"""Shared semantic contract helpers for extension batch facades."""

from __future__ import annotations

from typing import Any

_REQUIRED = frozenset({
    "ok", "capability_id", "canonical_reuse_of", "facade_layer", "analysis_only", "three_spec",
})


def contract_for(
    capability_id: int,
    *,
    canonical_targets: dict[int, int],
    classification: str = "E. CANONICAL_DUPLICATE_REUSE",
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "classification": classification,
        "canonical_owner": canonical_targets[capability_id],
        "required_keys": _REQUIRED,
        "consumer": "institutional_api",
        "entitlement_tier": "institutional",
    }


def all_contracts(*, batch_ids: list[int], canonical_targets: dict[int, int]) -> dict[int, dict[str, Any]]:
    return {cid: contract_for(cid, canonical_targets=canonical_targets) for cid in batch_ids}
