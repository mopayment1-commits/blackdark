"""Dedicated-backend tests for batch03_prep capabilities (IDs 101–150)."""

from __future__ import annotations

import pytest

from cap646.batch03_dedicated import BATCH03_DEDICATED_IDS, BATCH03_OVERLAP_BATCH01_IDS, EXPECTED_SURFACE, GENERIC_SURFACES
from cap646.batch03_production import BATCH03_IDS

BATCH03_OVERLAP_BATCH01 = BATCH03_OVERLAP_BATCH01_IDS
FORMERLY_GENERIC_SAMPLE = frozenset({101, 102, 109, 110, 111, 116, 144})


@pytest.mark.parametrize("capability_id", sorted(BATCH03_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_batch03_prep_dedicated_surface_and_success(capability_id: int):
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
    if capability_id in BATCH03_OVERLAP_BATCH01:
        assert result["production_spine"] == "batch01"
    else:
        assert result["production_spine"] in {"batch03", "batch03_prep"}
        assert result["backend_module"] == "cap646.batch03_production"


@pytest.mark.parametrize("capability_id", sorted(BATCH03_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_batch03_prep_dedicated_direct_execute(capability_id: int):
    from cap646.batch03_dedicated import execute

    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        },
    )
    assert result["success"] is True
    assert result["surface"] == EXPECTED_SURFACE[capability_id]


@pytest.mark.parametrize("capability_id", sorted(FORMERLY_GENERIC_SAMPLE))
@pytest.mark.asyncio
async def test_batch03_prep_formerly_generic_have_domain_payload(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert result["surface"] not in GENERIC_SURFACES
    assert result["success"] is True


def test_batch03_prep_manifest_count():
    assert len(BATCH03_IDS) == 50


@pytest.mark.parametrize("capability_id", sorted(BATCH03_OVERLAP_BATCH01))
@pytest.mark.asyncio
async def test_batch03_prep_overlap_reserved_in_dedicated_spine(capability_id: int):
    from cap646.batch03_dedicated import execute

    with pytest.raises(ValueError, match="batch01 overlap"):
        await execute(capability_id, params={"symbol": "BTC"})
