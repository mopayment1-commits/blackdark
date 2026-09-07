"""Production-path tests for 826-completion Batch 01 (50 capabilities)."""

from __future__ import annotations

import pytest

from cap646.batch01_production import BATCH01_IDS, batch01_entrypoint
from cap646.ui_pages import user_surface_for
from cap646.waves import USER_FACING

PDF_REGISTRY_BATCH01_OVERRIDE_IDS = frozenset({584})
BATCH01_SPINE_IDS = sorted(BATCH01_IDS - PDF_REGISTRY_BATCH01_OVERRIDE_IDS)


@pytest.mark.parametrize("capability_id", BATCH01_SPINE_IDS)
@pytest.mark.asyncio
async def test_batch01_runtime_production_path(capability_id: int):
    from cap646.runtime import execute_capability

    params = {
        "symbol": "BTC",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "email": "batch01-test@blackdark.local",
    }
    result = await execute_capability(capability_id, skip_entitlement=True, params=params)
    assert result["success"] is True, result
    assert result["binding_source"] == "explicit_option_a"
    assert result["production_spine"] == "batch01"
    assert result["backend_module"] == "cap646.batch01_production"
    assert result["backend_entrypoint"] == batch01_entrypoint(capability_id)
    assert result.get("compliance_footer")


@pytest.mark.parametrize("capability_id", BATCH01_SPINE_IDS)
def test_batch01_backend_registry_binding(capability_id: int):
    from cap646.backend_registry import binding_for

    binding = binding_for(capability_id)
    assert binding["binding_source"] == "explicit_option_a"
    assert binding["backend_module"] == "cap646.batch01_production"
    assert binding["backend_entrypoint"] == batch01_entrypoint(capability_id)


@pytest.mark.parametrize("capability_id", sorted(BATCH01_IDS & USER_FACING))
def test_batch01_user_facing_surface(capability_id: int):
    surface = user_surface_for(capability_id)
    assert surface is not None
    assert surface.get("api_path")
    assert surface.get("ui_path")


@pytest.mark.asyncio
async def test_batch01_245_freshness_not_lake():
    from cap646.runtime import execute_capability

    result = await execute_capability(245, skip_entitlement=True, params={"symbol": "BTC"})
    assert result["success"] is True
    assert "freshness_chip" in result or "executable_fresh" in result


@pytest.mark.asyncio
async def test_batch01_642_ai_provenance():
    from cap646.runtime import execute_capability

    result = await execute_capability(642, skip_entitlement=True, params={"symbol": "BTC"})
    assert result["success"] is True
    assert result.get("certificate") or result.get("provenance")
    assert result["surface"] == "ai_output_provenance_compliance_footer"


@pytest.mark.asyncio
async def test_batch01_584_canonical_risk_shield_binding():
    from cap646.backend_registry import binding_for
    from cap646.runtime import execute_capability

    binding = binding_for(584)
    assert binding["binding_source"] == "canonical_catalog_semantics"
    assert binding["backend_module"] == "bd_platform.institutional_delivery_intelligence_layer"
    assert binding["backend_entrypoint"] == "risk_management_shield_584"

    result = await execute_capability(584, skip_entitlement=True, params={"symbol": "BTC"})
    assert result["success"] is True, result
    assert result["backend_module"] == "bd_platform.institutional_delivery_intelligence_layer"
    assert result["backend_entrypoint"] == "risk_management_shield_584"
    payload = result.get("result") or result
    assert payload.get("surface") == "risk_management_shield"
    risk = payload.get("risk_shield") or payload.get("risk") or {}
    assert "trading_frozen" in risk
