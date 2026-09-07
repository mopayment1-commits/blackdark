"""Batch14 runtime canonical binding tests."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings

from bd_platform.batch14_membership import (
    BATCH14_IDS,
    CANONICAL_CATALOG_SEMANTICS_IDS,
    canonical_duplicate_ids,
    verify_membership,
)


def test_membership_partition() -> None:
    result = verify_membership()
    assert result["ok"] is True


def test_all_batch14_ids_bound() -> None:
    bindings = discover_bindings()
    missing = [cid for cid in BATCH14_IDS if cid not in bindings]
    assert missing == []


def test_catalog_semantics_bindings() -> None:
    bindings = discover_bindings()
    for cid in CANONICAL_CATALOG_SEMANTICS_IDS:
        mod, fn = bindings[cid]
        assert mod == "bd_platform.batch14_extension_analytics_layer"


def test_canonical_duplicate_backend_bindings() -> None:
    b660 = resolve_binding(660)
    b354 = resolve_binding(354)
    assert b660.module == b354.module
    assert b660.entrypoint == b354.entrypoint
    b661 = resolve_binding(661)
    b394 = resolve_binding(394)
    assert b661.module == b394.module
    assert b661.entrypoint == b394.entrypoint
