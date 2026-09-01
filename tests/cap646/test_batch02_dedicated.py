"""Dedicated-backend tests for official Batch 02 capabilities (IDs 51–100)."""

from __future__ import annotations

import pytest

from cap646.batch02_dedicated import BATCH02_DEDICATED_IDS, BATCH02_OVERLAP_BATCH01_IDS, EXPECTED_SURFACE, GENERIC_SURFACES
from cap646.batch02_production import OFFICIAL_BATCH02_IDS

BATCH02_OVERLAP_BATCH01 = BATCH02_OVERLAP_BATCH01_IDS
KEY_SAMPLE = frozenset({51, 53, 63, 69, 85, 98})


@pytest.mark.parametrize("capability_id", sorted(BATCH02_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_official_batch02_dedicated_surface_and_success(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )
    assert result["success"] is True, result
    assert result["surface"] == EXPECTED_SURFACE[capability_id], result
    assert result["surface"] not in GENERIC_SURFACES
    assert result["production_spine"] == "batch02"
    assert result["backend_module"] == "cap646.batch02_production"


@pytest.mark.parametrize("capability_id", sorted(BATCH02_OVERLAP_BATCH01))
@pytest.mark.asyncio
async def test_official_batch02_overlap_batch01(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert result["success"] is True
    assert result["production_spine"] == "batch01"


@pytest.mark.parametrize("capability_id", sorted(KEY_SAMPLE))
@pytest.mark.asyncio
async def test_official_batch02_key_sample_domain_payload(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert result["surface"] not in GENERIC_SURFACES
    assert result["success"] is True


def test_official_batch02_manifest_count():
    assert len(OFFICIAL_BATCH02_IDS) == 50
    assert len(BATCH02_DEDICATED_IDS) == 46


@pytest.mark.parametrize("capability_id", sorted(BATCH02_OVERLAP_BATCH01))
@pytest.mark.asyncio
async def test_official_batch02_overlap_reserved_in_dedicated_spine(capability_id: int):
    from cap646.batch02_dedicated import execute

    with pytest.raises(ValueError, match="batch01 overlap"):
        await execute(capability_id, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_canonical_69_cross_domain_not_generic_onchain():
    from cap646.runtime import execute_capability

    result = await execute_capability(69, skip_entitlement=True, params={"symbol": "BTC"})
    assert result["surface"] == "cross_domain_decision_intelligence_layer"
    assert result["surface"] != "onchain_intelligence"
    assert result.get("cross_domain_decision") or result.get("cross_domain_decision_intelligence_layer")
