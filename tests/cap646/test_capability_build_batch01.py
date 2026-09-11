"""Build Batch 01 — capability IDs 1–25 runtime proof (v6 build executor)."""

from __future__ import annotations

import pytest

BUILD_BATCH_01_IDS = list(range(1, 26))


@pytest.mark.parametrize("capability_id", BUILD_BATCH_01_IDS)
@pytest.mark.asyncio
async def test_build_batch01_runtime_success(capability_id: int):
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
    assert result.get("success") is True, result
    assert result.get("surface"), result


@pytest.mark.parametrize("capability_id", [1, 2, 3, 4, 10, 21])
@pytest.mark.asyncio
async def test_build_batch01_free_tier_dedicated_path_a(capability_id: int):
    from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS, EXPECTED_SURFACE, execute

    assert capability_id in BATCH01_DEDICATED_IDS
    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        },
    )
    assert result.get("success") is True, result
    assert result.get("surface") == EXPECTED_SURFACE[capability_id]
