"""Batch17 canonical duplicate reuse proof."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings


def test_backend_binding_801_facade_distinct_from_canonical_module() -> None:
    b801 = resolve_binding(801)
    b534 = resolve_binding(534)
    assert b801.module == "bd_platform.batch17_final_program_facade_layer"
    assert b534.module == "bd_platform.institutional_delivery_intelligence_layer"


def test_facade_801_preserves_canonical_marker() -> None:
    from bd_platform.batch17_final_program_facade_layer import execute_batch17_facade

    facade = execute_batch17_facade(capability_id=801, symbol="ETH")
    assert facade.get("canonical_reuse_of") == 534
    assert facade.get("capability_id") == 801


def test_pdf_registry_facade_binding_present() -> None:
    mod, fn = discover_bindings()[801]
    assert mod == "bd_platform.batch17_final_program_facade_layer"
    assert fn == "execute_batch17_facade"
