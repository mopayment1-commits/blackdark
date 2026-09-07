"""Batch13 #613 canonical reuse proof against #88 Liquidation Intelligence."""

from __future__ import annotations

import pytest

from cap646.backend_registry import resolve_binding
from cap646.handlers.batch02 import handle_batch02_capability
from pdf_capability_registry import discover_bindings


def test_backend_binding_matches_canonical_88() -> None:
    b613 = resolve_binding(613)
    b88 = resolve_binding(88)
    assert b613.module == b88.module
    assert b613.entrypoint == b88.entrypoint
    assert b613.source == "canonical_duplicate_reuse_88"


@pytest.mark.asyncio
async def test_facade_delegates_to_canonical_88_semantics() -> None:
    from bd_platform.batch13_operational_intelligence_layer import liquidation_screener_613

    facade = await liquidation_screener_613(symbol="ETH")
    canonical = await handle_batch02_capability(88, params={"symbol": "ETH"})
    assert facade.get("canonical_reuse_of") == 88
    assert facade.get("capability_id") == 613
    assert facade.get("surface") == canonical.get("surface")
    assert (facade.get("liquidation") or {}).get("asset") == (canonical.get("liquidation") or {}).get("asset")


def test_pdf_registry_facade_binding_present() -> None:
    mod, fn = discover_bindings()[613]
    assert mod == "bd_platform.batch13_operational_intelligence_layer"
    assert fn == "liquidation_screener_613"
