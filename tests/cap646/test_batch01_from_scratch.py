"""From-scratch institutional tests — official batch01 (IDs 1–25)."""

from __future__ import annotations

import pytest

from cap646.batch01_dedicated import EXPECTED_SURFACE
from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH01_OFFICIAL_IDS = list(range(1, 26))


@pytest.mark.parametrize("capability_id", BATCH01_OFFICIAL_IDS)
@pytest.mark.asyncio
async def test_batch01_from_scratch_closure(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report
    assert report["official_batch"] == "batch01"
    assert report["v6_true"]["PASS_ENGINEERING"] is True


@pytest.mark.parametrize("capability_id", BATCH01_OFFICIAL_IDS)
@pytest.mark.asyncio
async def test_batch01_dedicated_execute(capability_id: int):
    from cap646.batch01_production import execute

    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )
    assert result["success"] is True, result
    assert result["surface"] == EXPECTED_SURFACE[capability_id]
    assert result.get("latency_ms") is not None or result.get("performance_gate")
    assert result.get("data_provenance") or result.get("provenance")
