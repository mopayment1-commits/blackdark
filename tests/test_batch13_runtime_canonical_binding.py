"""Batch13 runtime canonical binding tests."""

from __future__ import annotations

from pdf_capability_registry import discover_bindings

from bd_platform.batch13_membership import (
    BATCH13_IDS,
    CANONICAL_CATALOG_SEMANTICS_IDS,
    external_dependency_ids,
    verify_membership,
)


def test_membership_partition() -> None:
    result = verify_membership()
    assert result["ok"] is True


def test_all_batch13_ids_bound() -> None:
    bindings = discover_bindings()
    missing = [cid for cid in BATCH13_IDS if cid not in bindings]
    assert missing == []


def test_catalog_semantics_bindings() -> None:
    bindings = discover_bindings()
    for cid in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, fn = bindings[cid]
        assert mod == "bd_platform.batch13_operational_intelligence_layer"


def test_external_ids_bound() -> None:
    bindings = discover_bindings()
    for cid in external_dependency_ids():
        mod, _ = bindings[cid]
        assert mod == "bd_platform.batch13_operational_intelligence_layer"
