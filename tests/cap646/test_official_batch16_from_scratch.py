"""From-scratch tests — official batch16 (IDs 376–400)."""

from __future__ import annotations

import pytest

from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH_IDS = [376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 394, 395, 396, 398, 400]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch16_from_scratch(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch16_execute(capability_id: int):
    from cap646.official_batch_production import execute

    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result["success"] is True, result
    assert result.get("latency_ms") is not None or result.get("performance_gate")
