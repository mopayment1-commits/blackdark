"""Batch12 #578/#584 canonical catalog semantics — portfolio dashboard and risk shield."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cap646.backend_registry import binding_for, resolve_binding
from cap646.runtime import execute_capability as cap646_execute
from pdf_capability_registry import discover_bindings, execute_capability as pdf_execute


def test_pdf_registry_canonical_bindings():
    mod578, fn578 = discover_bindings()[578]
    mod584, fn584 = discover_bindings()[584]
    assert mod578 == "bd_platform.institutional_delivery_intelligence_layer"
    assert fn578 == "unified_portfolio_dashboard_578"
    assert mod584 == "bd_platform.institutional_delivery_intelligence_layer"
    assert fn584 == "risk_management_shield_584"


def test_backend_registry_matches_catalog_semantics():
    b578 = resolve_binding(578)
    b584 = resolve_binding(584)
    assert b578.source == "canonical_catalog_semantics"
    assert b578.entrypoint == "unified_portfolio_dashboard_578"
    assert b584.source == "canonical_catalog_semantics"
    assert b584.entrypoint == "risk_management_shield_584"


@pytest.mark.asyncio
async def test_cap578_portfolio_dashboard_user_outcome():
    result = await cap646_execute(578, skip_entitlement=True, params={"symbol": "ETH"})
    assert result.get("success") is True, result
    assert result.get("backend_entrypoint") == "unified_portfolio_dashboard_578"
    payload = result.get("result") or result
    assert payload.get("surface") == "unified_portfolio_dashboard"
    assert payload.get("feature") == "Unified Portfolio Dashboard"
    assert payload.get("holdings")
    assert payload.get("portfolio_total_usd") is not None


@pytest.mark.asyncio
async def test_cap584_risk_shield_user_outcome():
    result = await cap646_execute(584, skip_entitlement=True, params={"symbol": "BTC"})
    assert result.get("success") is True, result
    assert result.get("backend_entrypoint") == "risk_management_shield_584"
    payload = result.get("result") or result
    assert payload.get("surface") == "risk_management_shield"
    assert payload.get("feature") == "Risk Management Shield"
    risk = payload.get("risk_shield") or payload.get("risk") or {}
    assert "trading_frozen" in risk
    assert "max_slippage_bps" in risk


@pytest.mark.asyncio
async def test_pdf_execute_matches_cap646_runtime():
    pdf578 = await pdf_execute(578)
    pdf584 = await pdf_execute(584)
    rt578 = await cap646_execute(578, skip_entitlement=True, params={"symbol": "ETH"})
    rt584 = await cap646_execute(584, skip_entitlement=True, params={"symbol": "BTC"})
    assert pdf578.get("surface") == (rt578.get("result") or rt578).get("surface")
    assert pdf584.get("surface") == (rt584.get("result") or rt584).get("surface")


def test_http_get_paths():
    from dashboard import app

    client = TestClient(app)
    for cid, entry, surface in (
        (578, "unified_portfolio_dashboard_578", "unified_portfolio_dashboard"),
        (584, "risk_management_shield_584", "risk_management_shield"),
    ):
        response = client.get(f"/api/cap646/{cid}", params={"symbol": "ETH"})
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True, body
        assert body.get("backend_entrypoint") == entry
        payload = body.get("result") or body
        assert payload.get("surface") == surface


def test_hero_functions_do_not_override_pdf_registry():
    """Hero delegates remain available but pdf/_MANUAL canonical bindings win."""
    mod578, fn578 = discover_bindings()[578]
    assert fn578 != "shadow_fork_pre_execution_578"
    mod584, fn584 = discover_bindings()[584]
    assert fn584 != "coindesk_rss_feed_584"
    binding584 = binding_for(584)
    assert binding584["backend_entrypoint"] == "risk_management_shield_584"
