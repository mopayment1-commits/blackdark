"""From-scratch tests — official batch14 (IDs 326–350)."""

from __future__ import annotations

import pytest

from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH_IDS = [326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch14_from_scratch(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch14_execute(capability_id: int):
    from cap646.official_batch_production import execute

    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result["success"] is True, result
    assert result.get("latency_ms") is not None or result.get("performance_gate")
