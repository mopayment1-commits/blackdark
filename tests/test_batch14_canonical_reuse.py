"""Batch14 canonical duplicate reuse proof."""

from __future__ import annotations

import pytest

from cap646.backend_registry import resolve_binding
from pdf_capability_registry import discover_bindings


def test_backend_binding_660_matches_354() -> None:
    b660 = resolve_binding(660)
    b354 = resolve_binding(354)
    assert b660.module == b354.module
    assert b660.entrypoint == b354.entrypoint


def test_facade_660_preserves_canonical_marker() -> None:
    from bd_platform.batch14_extension_analytics_layer import tvl_intelligence_660

    facade = tvl_intelligence_660(symbol="ETH")
    assert facade.get("canonical_reuse_of") == 354
    assert facade.get("capability_id") == 660


def test_pdf_registry_facade_binding_present() -> None:
    mod, fn = discover_bindings()[660]
    assert mod == "bd_platform.batch14_extension_analytics_layer"
    assert fn == "tvl_intelligence_660"
