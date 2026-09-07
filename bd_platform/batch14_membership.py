"""Canonical Batch14 (651–700) membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch14_semantic_engine import shared_core_ids

BATCH14_IDS = list(range(651, 701))
SHARED_CORE_PARAMETERIZED = shared_core_ids()
OUTSIDE_SHARED_CORE_IDS = [656, 657, 658, 659, 676, 682, 692, 695, 696]
CANONICAL_DUPLICATE_IDS = [660, 661, 676]
CANONICAL_CATALOG_SEMANTICS_IDS = frozenset({656, 657, 658, 659, 682, 692, 695, 696})


def parameterized_ids() -> list[int]:
    return list(SHARED_CORE_PARAMETERIZED)


def shared_core_ids_list() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(OUTSIDE_SHARED_CORE_IDS))


def canonical_duplicate_ids() -> list[int]:
    return sorted(set(CANONICAL_DUPLICATE_IDS))


def verify_membership() -> dict[str, object]:
    batch = set(BATCH14_IDS)
    shared = set(shared_core_ids_list())
    outside = set(outside_shared_core_ids())
    canonical = set(canonical_duplicate_ids())
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if not shared <= batch:
        errors.append("shared_not_subset")
    for cid in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, fn = discover_bindings().get(cid, ("", ""))
        if mod != "bd_platform.batch14_extension_analytics_layer":
            errors.append(f"catalog_semantics_binding_{cid}")
    return {
        "ok": not errors,
        "errors": errors,
        "shared_count": len(shared),
        "outside_count": len(outside),
        "canonical_count": len(canonical),
    }
