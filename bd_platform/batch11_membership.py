"""Canonical Batch11 (501–550) shared-core membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch11_semantic_engine import shared_core_ids

BATCH11_IDS = list(range(501, 551))
CUSTOM_IMPLEMENTATION_IDS: list[int] = []
OUTSIDE_SHARED_CORE_IDS = [517, 525, 528]
HERO_DELEGATE_ID = 525


def parameterized_ids() -> list[int]:
    return shared_core_ids()


def shared_core_47_ids() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(BATCH11_IDS) - set(shared_core_47_ids()))


def custom_implementation_ids() -> list[int]:
    return list(CUSTOM_IMPLEMENTATION_IDS)


def membership_ranges() -> dict[str, str]:
    return {
        "shared_core_47": "501–516, 518–524, 526–527, 529–550",
        "outside_shared_core": "517, 525, 528",
        "parameterized_47": "501–516, 518–524, 526–527, 529–550",
        "custom_0": "(none)",
    }


def verify_membership() -> dict[str, object]:
    batch = set(BATCH11_IDS)
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
    if outside != {517, 525, 528}:
        errors.append("outside_set_wrong")
    if 517 not in outside:
        errors.append("517_not_outside")
    if 525 not in outside:
        errors.append("525_not_outside")
    if 528 not in outside:
        errors.append("528_not_outside")
    if bindings[517][0] != "comparison_engine":
        errors.append("517_binding_wrong")
    if bindings[525][0] != "bd_platform.heroes_capability_layer":
        errors.append("525_binding_wrong")
    if bindings[528][0] != "bd_platform.market_rankings":
        errors.append("528_binding_wrong")
    missing = sorted(batch - shared - outside)
    return {
        "batch11_total_ids_exact": len(batch),
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
        "525_hero_delegate_outside_shared_core": 525 in outside,
    }
