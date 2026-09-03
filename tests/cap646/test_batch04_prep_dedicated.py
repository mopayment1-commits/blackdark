"""Dedicated-backend tests for batch04 capabilities (IDs 151–200)."""

from __future__ import annotations

import pytest

from cap646.batch04_dedicated import (
    BATCH04_DEDICATED_IDS,
    BATCH04_OVERLAP_BATCH01_IDS,
    EXPECTED_SURFACE,
    GENERIC_SURFACES,
)
from cap646.batch04_production import BATCH04_IDS

CATALOG_ALIGNED_SAMPLE = frozenset({151, 153, 156, 159, 161, 183, 189, 194, 200})


@pytest.mark.parametrize("capability_id", sorted(BATCH04_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_batch04_dedicated_surface_and_success(capability_id: int):
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
    assert result["production_spine"] == "batch04"
    assert result["backend_module"] == "cap646.batch04_production"


@pytest.mark.parametrize("capability_id", sorted(BATCH04_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_batch04_dedicated_direct_execute(capability_id: int):
    from cap646.batch04_dedicated import execute

    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        },
    )
    assert result["success"] is True
    assert result["surface"] == EXPECTED_SURFACE[capability_id]


@pytest.mark.parametrize("capability_id", sorted(CATALOG_ALIGNED_SAMPLE))
@pytest.mark.asyncio
async def test_batch04_catalog_aligned_have_domain_payload(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    root = EXPECTED_SURFACE[capability_id]
    if capability_id == 183:
        assert "whale_transaction" in result
        assert result["whale_transaction"]["risk_score"] >= 0
    elif capability_id == 159:
        assert result.get("catalog_link", {}).get("duplicate_of") == 103
    else:
        assert root in result
        assert result[root]["feature_ref"] == capability_id


def test_batch04_manifest_count():
    assert len(BATCH04_IDS) == 50
    assert len(BATCH04_DEDICATED_IDS) == 49


@pytest.mark.parametrize("capability_id", sorted(BATCH04_OVERLAP_BATCH01_IDS))
@pytest.mark.asyncio
async def test_batch04_overlap_routes_batch01(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert result["success"] is True
    assert result["production_spine"] == "batch01"


@pytest.mark.parametrize("capability_id", sorted(BATCH04_OVERLAP_BATCH01_IDS))
@pytest.mark.asyncio
async def test_batch04_overlap_reserved_in_dedicated_spine(capability_id: int):
    from cap646.batch04_dedicated import execute

    with pytest.raises(ValueError, match="batch01 overlap"):
        await execute(capability_id, params={"symbol": "BTC"})
