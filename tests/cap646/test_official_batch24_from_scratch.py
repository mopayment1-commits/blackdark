"""From-scratch tests — official batch24 (IDs 576–600)."""

from __future__ import annotations

import pytest

from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH_IDS = [576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch24_from_scratch(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch24_execute(capability_id: int):
    from cap646.official_batch_production import execute

    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result["success"] is True, result
    assert result.get("latency_ms") is not None or result.get("performance_gate")
