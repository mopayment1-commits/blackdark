"""Batch12 #551 canonical reuse proof against #88 Liquidation Intelligence."""

from __future__ import annotations

import pytest

from cap646.backend_registry import resolve_binding
from cap646.catalog import canonical_id
from cap646.handlers.batch02 import handle_batch02_capability
from cap646.runtime import execute_capability as cap646_execute
from pdf_capability_registry import discover_bindings


def test_catalog_canonical_id_is_88():
    assert canonical_id(551) == 88


def test_no_batch12_semantic_rule_for_551():
    from bd_platform.batch12_semantic_engine import CAPABILITY_SEMANTIC_SPECS

    assert 551 not in CAPABILITY_SEMANTIC_SPECS


def test_resolve_binding_matches_canonical_88():
    b551 = resolve_binding(551)
    b88 = resolve_binding(88)
    assert b551.module == b88.module
    assert b551.entrypoint == b88.entrypoint
    assert b551.source == "canonical_duplicate_reuse_88"


@pytest.mark.asyncio
async def test_cap646_runtime_duplicate_reuse_of_88():
    result = await cap646_execute(551, skip_entitlement=True, params={"symbol": "ETH"})
    assert result.get("success") is True, result
    assert result.get("classification") == "DUPLICATE/ALREADY_COVERED"
    assert result.get("duplicate_of") == 88
    assert result.get("requested_capability_id") == 551
    assert result.get("backend_module") == "cap646.batch02_production"
    assert result.get("backend_entrypoint") == "cap_088"
    payload = result.get("result") or result
    assert payload.get("surface") == "liquidation_intelligence"
    assert payload.get("capability_id") == 88


@pytest.mark.asyncio
async def test_pdf_facade_delegates_to_canonical_88_semantics():
    from bd_platform.institutional_delivery_intelligence_layer import liquidation_intelligence_551
    from cap646.handlers.batch02 import handle_batch02_capability

    facade = await liquidation_intelligence_551(symbol="ETH")
    canonical = await handle_batch02_capability(88, params={"symbol": "ETH"})
    assert facade.get("canonical_reuse_of") == 88
    assert facade.get("capability_id") == 551
    assert facade.get("surface") == canonical.get("surface")
    assert (facade.get("liquidation") or {}).get("asset") == (canonical.get("liquidation") or {}).get("asset")


def test_pdf_registry_facade_binding_present():
    mod, fn = discover_bindings()[551]
    assert mod == "bd_platform.institutional_delivery_intelligence_layer"
    assert fn == "liquidation_intelligence_551"
