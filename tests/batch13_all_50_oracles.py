"""Independent oracles for all Batch13 capabilities 601–650."""

from __future__ import annotations

from typing import Any

from tests.batch13_independent_semantic_oracles import independent_primary


def oracle_expected_keys(cap_id: int, payload: dict[str, Any], contract: dict[str, Any]) -> None:
    for key in contract.get("required_keys", set()):
        assert key in payload, f"cap {cap_id} missing contract key {key}"


def oracle_shared_core(cap_id: int, rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    return independent_primary(cap_id, rule, inputs, symbol=symbol)


def oracle_external_blocked(cap_id: int) -> dict[str, Any]:
    return {
        "ok": False,
        "capability_id": cap_id,
        "classification": "EXTERNAL_DEPENDENCY_BLOCKED",
        "dependency_status": "blocked",
    }


def oracle_canonical_613(canonical_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_reuse_of": 88,
        "surface": canonical_payload.get("surface"),
        "liquidation_asset": (canonical_payload.get("liquidation") or {}).get("asset"),
    }
