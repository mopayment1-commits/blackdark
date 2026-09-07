"""Batch15 canonical duplicate reuse proof."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings


def test_backend_binding_701_facade_distinct_from_canonical_module() -> None:
    b701 = resolve_binding(701)
    b434 = resolve_binding(434)
    assert b701.module == "bd_platform.batch15_defi_risk_data_facade_layer"
    assert b434.module == "bd_platform.defi_yield_intelligence_layer"


def test_facade_701_preserves_canonical_marker() -> None:
    from bd_platform.batch15_defi_risk_data_facade_layer import execute_batch15_facade

    facade = execute_batch15_facade(capability_id=701, symbol="ETH")
    assert facade.get("canonical_reuse_of") == 434
    assert facade.get("capability_id") == 701


def test_pdf_registry_facade_binding_present() -> None:
    mod, fn = discover_bindings()[701]
    assert mod == "bd_platform.batch15_defi_risk_data_facade_layer"
    assert fn == "execute_batch15_facade"
