"""Build Batch 26 — capability IDs 626–650 runtime proof (v6 build executor)."""

from __future__ import annotations

import pytest

BUILD_BATCH_26_IDS = list(range(626, 651))


@pytest.mark.parametrize("capability_id", BUILD_BATCH_26_IDS)
@pytest.mark.asyncio
async def test_build_batch26_runtime_success(capability_id: int):
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


@pytest.mark.parametrize("capability_id", BUILD_BATCH_26_IDS)
@pytest.mark.asyncio
async def test_build_batch26_bcbs_provenance_fields(capability_id: int):
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
    assert result.get("data_source") or result.get("source"), result
    assert result.get("timestamp"), result


@pytest.mark.parametrize("capability_id", BUILD_BATCH_26_IDS)
def test_build_batch26_hero_binding(capability_id: int):
    from cap646.build826_heroes import hero_binding_for

    binding = hero_binding_for(capability_id)
    assert binding["hero_binding_status"] == "BOUND", binding
    assert binding["primary_hero"], binding
