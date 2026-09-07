"""Batch15 runtime canonical binding tests."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings

from bd_platform.batch15_membership import BATCH15_IDS, verify_membership


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True


def test_all_batch15_ids_bound() -> None:
    bindings = discover_bindings()
    missing = [cid for cid in BATCH15_IDS if cid not in bindings]
    assert missing == []


def test_batch15_facade_bindings_use_batch15_layer() -> None:
    bindings = discover_bindings()
    for cid in BATCH15_IDS:
        mod, fn = bindings[cid]
        assert mod == "bd_platform.batch15_defi_risk_data_facade_layer"
        assert fn.endswith(f"_{cid}")


def test_backend_registry_resolves_batch15_layer() -> None:
    binding = resolve_binding(701)
    assert binding.module == "bd_platform.batch15_defi_risk_data_facade_layer"
    assert binding.entrypoint == "revenue_fees_economic_activity_701"
