"""Batch16 canonical duplicate reuse proof."""

from __future__ import annotations

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings


def test_backend_binding_751_facade_distinct_from_canonical_module() -> None:
    b751 = resolve_binding(751)
    b434 = resolve_binding(434)
    assert b751.module == "bd_platform.batch16_market_delivery_facade_layer"
    assert b434.module == "bd_platform.defi_yield_intelligence_layer"


def test_facade_751_preserves_canonical_marker() -> None:
    from bd_platform.batch16_market_delivery_facade_layer import execute_batch16_facade

    facade = execute_batch16_facade(capability_id=751, symbol="ETH")
    assert facade.get("canonical_reuse_of") == 484
    assert facade.get("capability_id") == 751


def test_pdf_registry_facade_binding_present() -> None:
    mod, fn = discover_bindings()[751]
    assert mod == "bd_platform.batch16_market_delivery_facade_layer"
    assert fn == "execute_batch16_facade"
