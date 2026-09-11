"""From-scratch tests — official batch10 (IDs 226–250)."""

from __future__ import annotations

import pytest

from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH_IDS = [227, 229, 230, 231, 234, 235, 236, 237, 238, 239, 240, 242, 243, 244, 245, 246, 247, 248, 249, 250]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch10_from_scratch(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch10_execute(capability_id: int):
    from cap646.official_batch_production import execute

    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result["success"] is True, result
    assert result.get("latency_ms") is not None or result.get("performance_gate")
