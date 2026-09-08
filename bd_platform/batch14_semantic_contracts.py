"""Semantic contracts for all Batch14 capabilities 651–700."""

from __future__ import annotations

from typing import Any

from bd_platform.batch14_membership import BATCH14_IDS, canonical_duplicate_ids, outside_shared_core_ids, parameterized_ids
from bd_platform.batch14_prebuild_classification import CANONICAL_DUPLICATE_TARGETS, PREBUILD_CLASSIFICATION
from bd_platform.batch14_semantic_engine import CAPABILITY_SEMANTIC_SPECS

OUTSIDE_CONSUMER_PATHS: dict[int, str] = {
    656: "batch14_three_spec_foundations data lineage surface",
    657: "batch14 extension analytics query governance",
    658: "batch14 white-label embedded analytics contract",
    659: "adaptive intelligence cross-domain decision layer",
    676: "facade to batch13 token unlock forecaster #604",
    682: "batch14 API aggregation layer",
    692: "adaptive intelligence AI analyst shadow mode",
    695: "batch14 excel/sheets integration contract",
    696: "batch14 API data platform surface",
}

CANONICAL_CONTRACTS: dict[int, dict[str, Any]] = {
    660: {
        "canonical_reuse_of": 354,
        "required_keys": {"canonical_reuse_of", "tvl_intelligence", "surface"},
    },
    661: {
        "canonical_reuse_of": 394,
        "required_keys": {"canonical_reuse_of", "chain_tvl", "surface"},
    },
    676: {
        "canonical_reuse_of": 604,
        "required_keys": {"canonical_reuse_of", "surface"},
    },
}


def contract_for(cap_id: int) -> dict[str, Any]:
    classification = PREBUILD_CLASSIFICATION[cap_id]
    if cap_id in parameterized_ids():
        spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
        return {
            "capability_id": cap_id,
            "classification": classification,
            "semantic_rule": spec["rule"],
            "feature": spec["feature"],
            "consumer_path": "batch14_extension_analytics_layer + cap646 gateway",
            "expected_ok": True,
            "required_keys": {spec["rule"], "semantic_rule", "feature", "formula_visible", "three_spec"},
        }
    if cap_id in canonical_duplicate_ids():
        meta = CANONICAL_CONTRACTS[cap_id]
        return {
            "capability_id": cap_id,
            "classification": classification,
            "canonical_reuse_of": CANONICAL_DUPLICATE_TARGETS[cap_id],
            "consumer_path": OUTSIDE_CONSUMER_PATHS.get(cap_id, "canonical facade"),
            "expected_ok": True,
            "required_keys": meta["required_keys"],
        }
    if cap_id in outside_shared_core_ids():
        return {
            "capability_id": cap_id,
            "classification": classification,
            "consumer_path": OUTSIDE_CONSUMER_PATHS.get(cap_id, "batch14 special surface"),
            "expected_ok": True,
            "required_keys": {"capability_id", "three_spec", "surface"},
        }
    return {"capability_id": cap_id, "classification": classification}


def all_contracts() -> dict[int, dict[str, Any]]:
    return {cid: contract_for(cid) for cid in BATCH14_IDS}
