"""From-scratch institutional tests — official batch02 (IDs 26–50)."""

from __future__ import annotations

import pytest

from cap646.batch02_closure_spec import expected_surface
from cap646.batch_institutional_closure import verify_batch02_institutional

BATCH02_OFFICIAL_IDS = list(range(26, 51))


@pytest.mark.parametrize("capability_id", BATCH02_OFFICIAL_IDS)
@pytest.mark.asyncio
async def test_batch02_institutional_closure(capability_id: int):
    report = await verify_batch02_institutional(capability_id)
    assert report["PASS_INSTITUTIONAL"] is True, report
    assert report["official_batch"] == "batch02"


@pytest.mark.parametrize("capability_id", BATCH02_OFFICIAL_IDS)
@pytest.mark.asyncio
async def test_batch02_dedicated_execute(capability_id: int):
    from cap646.batch02_official_production import execute

    result = await execute(capability_id, params={
        "symbol": "BTC",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "tier": "pro",
    })
    assert result["success"] is True, result
    assert result["surface"] == expected_surface(capability_id)
    assert result.get("data_provenance") or result.get("provenance")
