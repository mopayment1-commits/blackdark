"""From-scratch tests — official batch03 (IDs 51–75)."""

from __future__ import annotations

import pytest

from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH_IDS = [51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 67, 68, 70, 71, 72, 73, 74, 75]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch03_from_scratch(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch03_execute(capability_id: int):
    from cap646.official_batch_production import execute

    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result["success"] is True, result
    assert result.get("latency_ms") is not None or result.get("performance_gate")
