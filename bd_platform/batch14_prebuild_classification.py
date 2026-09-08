"""Batch14 (651–700) pre-build classification — categories A–H only."""

from __future__ import annotations

from typing import Any

PREBUILD_CLASSIFICATION: dict[int, str] = {
    651: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    652: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    653: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    654: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    655: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    656: "B. EXISTING_NEEDS_EXTENSION",
    657: "B. EXISTING_NEEDS_EXTENSION",
    658: "B. EXISTING_NEEDS_EXTENSION",
    659: "B. EXISTING_NEEDS_EXTENSION",
    660: "E. CANONICAL_DUPLICATE_REUSE",
    661: "E. CANONICAL_DUPLICATE_REUSE",
    662: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    663: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    664: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    665: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    666: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    667: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    668: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    669: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    670: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    671: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    672: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    673: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    674: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    675: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    676: "E. CANONICAL_DUPLICATE_REUSE",
    677: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    678: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    679: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    680: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    681: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    682: "B. EXISTING_NEEDS_EXTENSION",
    683: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    684: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    685: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    686: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    687: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    688: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    689: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    690: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    691: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    692: "B. EXISTING_NEEDS_EXTENSION",
    693: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    694: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    695: "B. EXISTING_NEEDS_EXTENSION",
    696: "B. EXISTING_NEEDS_EXTENSION",
    697: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    698: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    699: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
    700: "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE",
}

CANONICAL_DUPLICATE_TARGETS: dict[int, int] = {660: 354, 661: 394, 676: 604}

PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {
    660: {"canonical_capability_id": 354, "evidence": "TVL Intelligence delegates to charting layer #354"},
    661: {"canonical_capability_id": 394, "evidence": "Chain TVL Comparison delegates to charting layer #394"},
    676: {"canonical_capability_id": 604, "evidence": "Unlocks facade delegates to token unlock forecaster #604"},
    656: {"binding_module": "batch14_three_spec_foundations", "evidence": "Data lineage via three-spec foundation layer"},
    659: {"binding_module": "batch14_three_spec_foundations", "evidence": "Cross-domain decision via adaptive foundation"},
    692: {"binding_module": "bd_platform.adaptive_intelligence", "evidence": "AI Analyst integrates adaptive spine"},
}


def verify_prebuild_classification() -> dict[str, Any]:
    ids = sorted(PREBUILD_CLASSIFICATION)
    allowed = {
        "A. EXISTING_VERIFIED", "B. EXISTING_NEEDS_EXTENSION", "C. PARTIAL_IMPLEMENTATION",
        "D. KEEP_DISTINCT_BUT_REUSE_SHARED_CORE", "E. CANONICAL_DUPLICATE_REUSE",
        "F. NEW_BUILD_REQUIRED", "G. EXTERNAL_DEPENDENCY_BLOCKED", "H. NOT_APPLICABLE_WITH_EVIDENCE",
    }
    categories = set(PREBUILD_CLASSIFICATION.values())
    double = [cid for cid in ids if list(PREBUILD_CLASSIFICATION.keys()).count(cid) > 1]
    return {
        "expected_ids": 50,
        "actual_unique_ids": len(set(ids)),
        "missing_ids": [i for i in range(651, 701) if i not in PREBUILD_CLASSIFICATION],
        "extra_ids": [i for i in PREBUILD_CLASSIFICATION if i < 651 or i > 700],
        "duplicate_ids": double,
        "invalid_categories": [c for c in categories if c not in allowed],
        "double_classifications": double,
        "ok": len(ids) == 50 and not double and categories <= allowed,
    }

