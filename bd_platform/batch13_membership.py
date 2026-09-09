"""Canonical Batch13 (601–650) membership derived from registry + semantic engine."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch13_semantic_engine import shared_core_ids

BATCH13_IDS = list(range(601, 651))
SHARED_CORE_PARAMETERIZED = shared_core_ids()
OUTSIDE_SHARED_CORE_IDS = [627, 629, 630, 631, 637, 638, 639, 640, 641, 642, 644, 645, 646]
EXTERNAL_DEPENDENCY_IDS = [647, 648, 649, 650]
CANONICAL_CATALOG_SEMANTICS_IDS = frozenset({637, 638, 639, 640, 641, 645})


def parameterized_ids() -> list[int]:
    return list(SHARED_CORE_PARAMETERIZED)


def shared_core_ids_list() -> list[int]:
    return sorted(set(parameterized_ids()))


def outside_shared_core_ids() -> list[int]:
    return sorted(set(OUTSIDE_SHARED_CORE_IDS))


def external_dependency_ids() -> list[int]:
    return sorted(set(EXTERNAL_DEPENDENCY_IDS))


def verify_membership() -> dict[str, object]:
    batch = set(BATCH13_IDS)
    shared = set(shared_core_ids_list())
    outside = set(outside_shared_core_ids())
    external = set(external_dependency_ids())
    bindings = discover_bindings()
    errors: list[str] = []
    if len(batch) != 50:
        errors.append("batch_not_50")
    if shared | outside | external != batch:
        errors.append("partition_not_batch")
    if shared & outside or shared & external or outside & external:
        errors.append("partition_overlap")
    for cid in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, fn = bindings.get(cid, ("", ""))
        if mod != "bd_platform.batch13_operational_intelligence_layer":
            errors.append(f"catalog_semantics_binding_{cid}")
    return {"ok": not errors, "errors": errors, "shared_count": len(shared), "outside_count": len(outside), "external_count": len(external)}
