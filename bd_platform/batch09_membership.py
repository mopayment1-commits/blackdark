"""Canonical Batch09 (401–450) shared-core membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch09_semantic_engine import shared_core_ids

BATCH09_IDS = list(range(401, 451))
CUSTOM_IMPLEMENTATION_IDS = [437, 441]
OUTSIDE_SHARED_CORE_IDS = [409, 441]
QUICKTAKE_ID = 409


def parameterized_ids() -> list[int]:
    return shared_core_ids()


def shared_core_48_ids() -> list[int]:
    """Shared-core-48 = parameterized-47 + custom #437 inside shared core."""
    return sorted(set(parameterized_ids()) | {437})


def outside_shared_core_ids() -> list[int]:
    return sorted(set(BATCH09_IDS) - set(shared_core_48_ids()))


def custom_implementation_ids() -> list[int]:
    return list(CUSTOM_IMPLEMENTATION_IDS)


def membership_ranges() -> dict[str, str]:
    """Human-readable ranges matching exact ID lists."""
    return {
        "shared_core_48": "401–408, 410–440, 442–450",
        "outside_shared_core": "409, 441",
        "parameterized_47": "401–408, 410–436, 438–440, 442–450",
        "custom_2": "437, 441",
    }


def verify_membership() -> dict[str, object]:
    batch = set(BATCH09_IDS)
    param = set(parameterized_ids())
    shared = set(shared_core_48_ids())
    outside = set(outside_shared_core_ids())
    custom = set(custom_implementation_ids())
    bindings = discover_bindings()
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if len(shared) != 48:
        errors.append("shared_not_48")
    if len(outside) != 2:
        errors.append("outside_not_2")
    if len(param) != 47:
        errors.append("parameterized_not_47")
    if len(custom) != 2:
        errors.append("custom_not_2")
    if shared | outside != batch:
        errors.append("union_not_batch")
    if shared & outside:
        errors.append("shared_outside_overlap")
    if param & custom:
        errors.append("parameterized_custom_overlap")
    if shared - param != {437}:
        errors.append("shared_minus_param_not_437")
    if param - shared:
        errors.append("param_not_subset_shared")
    if 437 not in shared or 437 in param:
        errors.append("437_membership_wrong")
    if 441 not in outside or 441 in shared:
        errors.append("441_membership_wrong")
    if 409 not in outside:
        errors.append("409_not_outside")
    if bindings[409][0] != "bd_platform.quicktake_feed":
        errors.append("409_binding_wrong")
    if bindings[437][1] != "defi_risk_radar_437":
        errors.append("437_binding_wrong")
    if bindings[441][1] != "oracle_risk_441":
        errors.append("441_binding_wrong")
    missing = sorted(batch - shared - outside)
    return {
        "batch09_total_ids_exact": len(batch),
        "shared_core_count_exact": len(shared),
        "outside_shared_core_count_exact": len(outside),
        "parameterized_count_exact": len(param),
        "custom_count_exact": len(custom),
        "A_shared_core_48_ids": shared_core_48_ids(),
        "B_outside_shared_core_ids": outside_shared_core_ids(),
        "C_parameterized_47_ids": parameterized_ids(),
        "D_custom_implementation_ids": custom_implementation_ids(),
        "ranges": membership_ranges(),
        "membership_overlap_errors": errors,
        "membership_missing_ids": missing,
        "shared_core_membership_unambiguous": not errors and not missing,
        "437_custom_inside_shared_core": 437 in shared and 437 not in param,
        "441_custom_outside_shared_core": 441 in outside and 441 in custom,
    }
