"""Mandatory v6 strict institutional tests — batch32 (IDs 776–800)."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute, expected_surface
from cap646.v6_strict_closure import verify_strict_institutional

BATCH_IDS = [776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_institutional_strict_closure(capability_id: int):
    report = await verify_strict_institutional(capability_id)
    assert report.get("PASS_INSTITUTIONAL_STRICT") is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_institutional_execute_surface(capability_id: int):
    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result["success"] is True, result
    assert result["surface"] == expected_surface(capability_id)
    assert result.get("compliance_footer")
