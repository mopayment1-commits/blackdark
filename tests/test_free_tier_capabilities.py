"""Free-tier CAP closure tests (DeFiLlama / Blockchair / Pyth)."""

from __future__ import annotations

import pytest

FREE_TIER_IDS = [
    1, 2, 3, 4, 10, 21, 38, 39, 45, 196, 331, 332, 337,
    647, 648, 652, 672, 673, 674, 675, 676, 690, 691, 702, 703, 704, 705,
]


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", FREE_TIER_IDS)
async def test_free_tier_execute(capability_id: int):
    if capability_id == 648:
        try:
            from bigquery_export import bigquery_live_ready

            if not bigquery_live_ready():
                pytest.skip("BigQuery export not configured in this environment")
        except Exception:
            pytest.skip("BigQuery export not available in this environment")

    from bd_platform.free_tier_capabilities import execute_free_tier_capability

    result = await execute_free_tier_capability(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x000000000000000000000000000000000000dead",
            "tier": "whale",
        },
    )
    assert result["capability_id"] == capability_id
    assert result["free_tier"] is True
    assert result["success"] is True
    assert result.get("surface")
    assert result.get("data")


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", [1, 21, 647, 674, 704])
async def test_free_tier_verify(capability_id: int):
    from cap978.unified import verify_unified

    report = await verify_unified(
        capability_id,
        user={"email": "free-tier-test@blackdark.local", "tier": "elite"},
    )
    assert report["verdict"] == "VERIFIED_COMPLETE", report


@pytest.mark.asyncio
async def test_external_still_blocked():
    from cap646.functional_dod import verify_functional

    report = await verify_functional(645)
    assert report["verdict"] == "EXTERNAL_EVIDENCE_REQUIRED"
