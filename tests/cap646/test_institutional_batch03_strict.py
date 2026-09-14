"""Mandatory v6 strict institutional tests — batch03 (IDs 51–75)."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute, expected_surface
from cap646.v6_strict_closure import verify_strict_institutional

BATCH_IDS = [51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 67, 68, 70, 71, 72, 73, 74, 75]


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
