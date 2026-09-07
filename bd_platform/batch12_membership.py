"""Canonical Batch12 (551–600) shared-core membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch12_semantic_engine import shared_core_ids

BATCH12_IDS = list(range(551, 601))
CUSTOM_IMPLEMENTATION_IDS: list[int] = []
OUTSIDE_SHARED_CORE_IDS = [551, 578, 584]
CANONICAL_DUPLICATE_REUSE_ID = 551


def parameterized_ids() -> list[int]:
    return shared_core_ids()


def shared_core_47_ids() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(BATCH12_IDS) - set(shared_core_47_ids()))


def custom_implementation_ids() -> list[int]:
    return list(CUSTOM_IMPLEMENTATION_IDS)


def membership_ranges() -> dict[str, str]:
    return {
        "shared_core_47": "552–577, 579–583, 585–600",
        "outside_shared_core": "551, 578, 584",
        "parameterized_47": "552–577, 579–583, 585–600",
        "custom_0": "(none)",
    }


def verify_membership() -> dict[str, object]:
    batch = set(BATCH12_IDS)
    param = set(parameterized_ids())
    shared = set(shared_core_47_ids())
    outside = set(outside_shared_core_ids())
    bindings = discover_bindings()
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if len(shared) != 47:
        errors.append("shared_not_47")
    if len(outside) != 3:
        errors.append("outside_not_3")
    if len(param) != 47:
        errors.append("parameterized_not_47")
    if shared | outside != batch:
        errors.append("union_not_batch")
    if shared & outside:
        errors.append("shared_outside_overlap")
    if outside != {551, 578, 584}:
        errors.append("outside_set_wrong")
    if 551 not in outside:
        errors.append("551_not_outside")
    if 578 not in outside:
        errors.append("578_not_outside")
    if 584 not in outside:
        errors.append("584_not_outside")
    if bindings[551][0] != "bd_platform.institutional_delivery_intelligence_layer":
        errors.append("551_binding_wrong")
    if bindings[551][1] != "liquidation_intelligence_551":
        errors.append("551_entrypoint_wrong")
    if bindings[578][0] != "bd_platform.heroes_capability_layer":
        errors.append("578_binding_wrong")
    if bindings[584][0] != "bd_platform.heroes_capability_layer":
        errors.append("584_binding_wrong")
    missing = sorted(batch - shared - outside)
    return {
        "batch12_total_ids_exact": len(batch),
        "shared_core_count_exact": len(shared),
        "outside_shared_core_count_exact": len(outside),
        "parameterized_count_exact": len(param),
        "custom_count_exact": len(CUSTOM_IMPLEMENTATION_IDS),
        "A_shared_core_47_ids": shared_core_47_ids(),
        "B_outside_shared_core_ids": outside_shared_core_ids(),
        "C_parameterized_47_ids": parameterized_ids(),
        "D_custom_implementation_ids": custom_implementation_ids(),
        "ranges": membership_ranges(),
        "membership_overlap_errors": errors,
        "membership_missing_ids": missing,
        "shared_core_membership_unambiguous": not errors and not missing,
        "551_canonical_duplicate_outside_shared_core": 551 in outside,
    }
