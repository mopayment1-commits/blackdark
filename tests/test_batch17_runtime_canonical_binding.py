"""Batch17 runtime canonical binding tests."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings

from bd_platform.batch17_membership import BATCH17_IDS, verify_membership


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True


def test_all_batch17_ids_bound() -> None:
    bindings = discover_bindings()
    missing = [cid for cid in BATCH17_IDS if cid not in bindings]
    assert missing == []


def test_batch17_facade_bindings_use_batch17_layer() -> None:
    bindings = discover_bindings()
    for cid in BATCH17_IDS:
        mod, fn = bindings[cid]
        assert mod == "bd_platform.batch17_final_program_facade_layer"
        assert fn == "execute_batch17_facade"


def test_backend_registry_resolves_batch17_layer() -> None:
    binding = resolve_binding(801)
    assert binding.module == "bd_platform.batch17_final_program_facade_layer"
    assert binding.entrypoint == "execute_batch17_facade"
