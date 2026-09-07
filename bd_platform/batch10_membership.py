"""Canonical Batch10 (451–500) shared-core membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch10_semantic_engine import shared_core_ids

BATCH10_IDS = list(range(451, 501))
CUSTOM_IMPLEMENTATION_IDS: list[int] = []
OUTSIDE_SHARED_CORE_IDS = [458]
HERO_DELEGATE_ID = 458


def parameterized_ids() -> list[int]:
    return shared_core_ids()


def shared_core_49_ids() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(BATCH10_IDS) - set(shared_core_49_ids()))


def custom_implementation_ids() -> list[int]:
    return list(CUSTOM_IMPLEMENTATION_IDS)


def membership_ranges() -> dict[str, str]:
    return {
        "shared_core_49": "451–457, 459–500",
        "outside_shared_core": "458",
        "parameterized_49": "451–457, 459–500",
        "custom_0": "(none)",
    }


def verify_membership() -> dict[str, object]:
    batch = set(BATCH10_IDS)
    param = set(parameterized_ids())
    shared = set(shared_core_49_ids())
    outside = set(outside_shared_core_ids())
    bindings = discover_bindings()
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if len(shared) != 49:
        errors.append("shared_not_49")
    if len(outside) != 1:
        errors.append("outside_not_1")
    if len(param) != 49:
        errors.append("parameterized_not_49")
    if shared | outside != batch:
        errors.append("union_not_batch")
    if shared & outside:
        errors.append("shared_outside_overlap")
    if 458 not in outside:
        errors.append("458_not_outside")
    if bindings[458][0] != "bd_platform.heroes_capability_layer":
        errors.append("458_binding_wrong")
    missing = sorted(batch - shared - outside)
    return {
        "batch10_total_ids_exact": len(batch),
        "shared_core_count_exact": len(shared),
        "outside_shared_core_count_exact": len(outside),
        "parameterized_count_exact": len(param),
        "custom_count_exact": len(CUSTOM_IMPLEMENTATION_IDS),
        "A_shared_core_49_ids": shared_core_49_ids(),
        "B_outside_shared_core_ids": outside_shared_core_ids(),
        "C_parameterized_49_ids": parameterized_ids(),
        "D_custom_implementation_ids": custom_implementation_ids(),
        "ranges": membership_ranges(),
        "membership_overlap_errors": errors,
        "membership_missing_ids": missing,
        "shared_core_membership_unambiguous": not errors and not missing,
        "458_hero_delegate_outside_shared_core": 458 in outside,
    }
