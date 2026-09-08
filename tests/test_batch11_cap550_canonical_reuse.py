"""Batch11 #550 canonical reuse proof against #205 Open Interest Intelligence."""

from __future__ import annotations

import pytest

from cap646.backend_registry import resolve_binding
from cap646.catalog import canonical_id
from cap646.handlers.derivatives import handle_derivatives_capability
from cap646.runtime import execute_capability as cap646_execute
from pdf_capability_registry import discover_bindings


def test_catalog_canonical_id_is_205():
    assert canonical_id(550) == 205


def test_no_batch11_semantic_rule_for_550():
    from bd_platform.batch11_semantic_engine import CAPABILITY_SEMANTIC_SPECS

    assert 550 not in CAPABILITY_SEMANTIC_SPECS


def test_resolve_binding_matches_canonical_205():
    b550 = resolve_binding(550)
    b205 = resolve_binding(205)
    assert b550.module == b205.module
    assert b550.entrypoint == b205.entrypoint
    assert b550.source == "canonical_duplicate_reuse_205"


@pytest.mark.asyncio
async def test_cap646_runtime_duplicate_reuse_of_205():
    result = await cap646_execute(550, skip_entitlement=True, params={"symbol": "ETH"})
    assert result.get("success") is True, result
    assert result.get("classification") == "DUPLICATE/ALREADY_COVERED"
    assert result.get("duplicate_of") == 205
    assert result.get("requested_capability_id") == 550
    assert result.get("backend_module") == "cap646.handlers.derivatives"
    payload = result.get("result") or result
    assert payload.get("surface") == "open_interest_intelligence"
    assert payload.get("capability_id") == 205


@pytest.mark.asyncio
async def test_pdf_facade_delegates_to_canonical_205_semantics():
    from bd_platform.institutional_delivery_intelligence_layer import open_interest_intelligence_550

    facade = await open_interest_intelligence_550(symbol="ETH")
    canonical = await handle_derivatives_capability(205, params={"symbol": "ETH"})
    assert facade.get("canonical_reuse_of") == 205
    assert facade.get("capability_id") == 550
    assert facade.get("surface") == canonical.get("surface")
    assert (facade.get("overview") or {}).get("asset") == (canonical.get("overview") or {}).get("asset")


def test_pdf_registry_facade_binding_present():
    mod, fn = discover_bindings()[550]
    assert mod == "bd_platform.institutional_delivery_intelligence_layer"
    assert fn == "open_interest_intelligence_550"
