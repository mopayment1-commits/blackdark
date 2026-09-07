"""Batch13 (601–650) pre-build classification — categories A–H only."""

from __future__ import annotations

from typing import Any

# Allowed categories (exactly one per ID):
# A. EXISTING_VERIFIED
# B. EXISTING_NEEDS_EXTENSION
# C. PARTIAL_IMPLEMENTATION
# D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE
# E. CANONICAL_DUPLICATE_REUSE
# F. NEW_BUILD_REQUIRED
# G. EXTERNAL_DEPENDENCY_BLOCKED
# H. NOT_APPLICABLE_WITH_EVIDENCE

PREBUILD_CLASSIFICATION: dict[int, str] = {
    601: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    602: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    603: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    604: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    605: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    606: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    607: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    608: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    609: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    610: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    611: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    612: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    613: "E. CANONICAL_DUPLICATE_REUSE",
    614: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    615: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    616: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    617: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    618: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    619: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    620: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    621: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    622: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    623: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    624: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    625: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    626: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    627: "B. EXISTING_NEEDS_EXTENSION",
    628: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    629: "A. EXISTING_VERIFIED",
    630: "B. EXISTING_NEEDS_EXTENSION",
    631: "A. EXISTING_VERIFIED",
    632: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    633: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    634: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    635: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    636: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    637: "B. EXISTING_NEEDS_EXTENSION",
    638: "B. EXISTING_NEEDS_EXTENSION",
    639: "B. EXISTING_NEEDS_EXTENSION",
    640: "B. EXISTING_NEEDS_EXTENSION",
    641: "B. EXISTING_NEEDS_EXTENSION",
    642: "A. EXISTING_VERIFIED",
    643: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    644: "A. EXISTING_VERIFIED",
    645: "B. EXISTING_NEEDS_EXTENSION",
    646: "A. EXISTING_VERIFIED",
    647: "G. EXTERNAL_DEPENDENCY_BLOCKED",
    648: "G. EXTERNAL_DEPENDENCY_BLOCKED",
    649: "G. EXTERNAL_DEPENDENCY_BLOCKED",
    650: "G. EXTERNAL_DEPENDENCY_BLOCKED",
}

CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {613: 88}

PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {
    613: {
        "canonical_capability_id": 88,
        "canonical_implementation": "cap646.batch02_production.cap_088",
        "facade_binding": "bd_platform.batch13_operational_intelligence_layer.liquidation_screener_613",
        "evidence": "Liquidation Screener delegates to canonical liquidation radar #88 semantics",
    },
    627: {
        "binding_module": "comparison_engine",
        "binding_function": "run_comparison_engine",
        "evidence": "Custom Institutional Data Terminal uses comparison_engine manual binding",
    },
    647: {"blocker": "vendor SLA feed", "local_contract": "bd_platform.extension_providers.real_time_feed"},
    648: {"blocker": "datashare warehouse agreement", "local_contract": "bd_platform.extension_providers.datashare"},
    649: {"blocker": "external dbt deployment", "local_contract": "bd_platform.extension_providers.dbt_connector"},
    650: {"blocker": "BI connector licenses", "local_contract": "bd_platform.extension_providers.bi_connectors"},
}


def verify_prebuild_classification() -> dict[str, Any]:
    ids = sorted(PREBUILD_CLASSIFICATION)
    categories = set(PREBUILD_CLASSIFICATION.values())
    allowed = {
        "A. EXISTING_VERIFIED",
        "B. EXISTING_NEEDS_EXTENSION",
        "C. PARTIAL_IMPLEMENTATION",
        "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
        "E. CANONICAL_DUPLICATE_REUSE",
        "F. NEW_BUILD_REQUIRED",
        "G. EXTERNAL_DEPENDENCY_BLOCKED",
        "H. NOT_APPLICABLE_WITH_EVIDENCE",
    }
    double = [cid for cid in ids if list(PREBUILD_CLASSIFICATION.keys()).count(cid) > 1]
    return {
        "expected_ids": 50,
        "actual_unique_ids": len(set(ids)),
        "missing_ids": [i for i in range(601, 651) if i not in PREBUILD_CLASSIFICATION],
        "extra_ids": [i for i in PREBUILD_CLASSIFICATION if i < 601 or i > 650],
        "duplicate_ids": double,
        "invalid_categories": [c for c in categories if c not in allowed],
        "double_classifications": double,
        "ok": len(ids) == 50 and not double and categories <= allowed,
    }
