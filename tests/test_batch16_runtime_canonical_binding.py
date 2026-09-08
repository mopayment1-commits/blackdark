"""Batch16 runtime canonical binding tests."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings

from bd_platform.batch16_membership import BATCH16_IDS, verify_membership


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True


def test_all_batch16_ids_bound() -> None:
    bindings = discover_bindings()
    missing = [cid for cid in BATCH16_IDS if cid not in bindings]
    assert missing == []


def test_batch16_facade_bindings_use_batch16_layer() -> None:
    bindings = discover_bindings()
    for cid in BATCH16_IDS:
        mod, fn = bindings[cid]
        assert mod == "bd_platform.batch16_market_delivery_facade_layer"
        assert fn == "execute_batch16_facade"


def test_backend_registry_resolves_batch16_layer() -> None:
    binding = resolve_binding(751)
    assert binding.module == "bd_platform.batch16_market_delivery_facade_layer"
    assert binding.entrypoint == "execute_batch16_facade"
