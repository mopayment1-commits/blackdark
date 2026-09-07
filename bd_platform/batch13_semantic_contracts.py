"""Semantic contracts for all Batch13 capabilities 601–650."""

from __future__ import annotations

from typing import Any

from bd_platform.batch13_membership import BATCH13_IDS, external_dependency_ids, outside_shared_core_ids, parameterized_ids
from bd_platform.batch13_prebuild_classification import PREBUILD_CLASSIFICATION
from bd_platform.batch13_semantic_engine import CAPABILITY_SEMANTIC_SPECS

OUTSIDE_CONSUMER_PATHS: dict[int, str] = {
    627: "comparison_engine institutional data terminal",
    629: "heroes single_sentence_oracle hero surface",
    630: "intelligence_ux_extensions market scan",
    631: "heroes unified_live_technical_analysis hero surface",
    637: "trust_pulse scenario engine catalog semantics",
    638: "oracle_track_record claims verification",
    639: "net_edge_truth score surface",
    640: "oracle_track_record public accuracy ledger",
    641: "decision_certificate institutional DD export",
    642: "batch01 AI output provenance spine",
    644: "batch01 capacity/load evidence spine",
    645: "security_posture verification evidence",
    646: "institutional chaos resilience handler",
}

EXTERNAL_CONTRACTS: dict[int, dict[str, Any]] = {
    647: {
        "local_behavior": "fail_closed provider contract",
        "dependency_status": "blocked_without_credentials",
        "expected_ok": False,
        "required_keys": {"classification", "blocker_type", "reason", "provider"},
    },
    648: {
        "local_behavior": "fail_closed warehouse contract",
        "dependency_status": "blocked_without_warehouse_agreement",
        "expected_ok": False,
        "required_keys": {"classification", "blocker_type", "reason", "provider"},
    },
    649: {
        "local_behavior": "fail_closed dbt deployment contract",
        "dependency_status": "blocked_without_external_dbt",
        "expected_ok": False,
        "required_keys": {"classification", "blocker_type", "reason", "provider"},
    },
    650: {
        "local_behavior": "fail_closed BI connector contract",
        "dependency_status": "blocked_without_connector_license",
        "expected_ok": False,
        "required_keys": {"classification", "blocker_type", "reason", "provider"},
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
            "consumer_path": "batch13_operational_intelligence_layer + cap646 gateway",
            "expected_ok": True,
            "required_keys": {spec["rule"], "semantic_rule", "feature", "formula_visible"},
        }
    if cap_id == 613:
        return {
            "capability_id": cap_id,
            "classification": classification,
            "canonical_reuse_of": 88,
            "consumer_path": "facade to cap646.batch02_production.cap_088",
            "expected_ok": True,
            "required_keys": {"canonical_reuse_of", "surface", "liquidation", "liquidation_screener"},
        }
    if cap_id in outside_shared_core_ids():
        keys = {"capability_id"}
        if cap_id in {637, 638, 639, 640, 641, 645}:
            keys.add("surface")
        if cap_id in {642, 644}:
            keys.add("backend_module")
        return {
            "capability_id": cap_id,
            "classification": classification,
            "consumer_path": OUTSIDE_CONSUMER_PATHS.get(cap_id, "canonical binding module"),
            "expected_ok": True,
            "required_keys": keys,
        }
    if cap_id in external_dependency_ids():
        return {
            "capability_id": cap_id,
            "classification": classification,
            **EXTERNAL_CONTRACTS[cap_id],
        }
    return {"capability_id": cap_id, "classification": classification}


def all_contracts() -> dict[int, dict[str, Any]]:
    return {cid: contract_for(cid) for cid in BATCH13_IDS}
