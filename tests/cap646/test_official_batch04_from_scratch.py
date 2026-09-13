"""Substantive v6 tests — official batch04 (IDs 76–100)."""

from __future__ import annotations

import pytest

from cap646.official_batch_production import execute

BATCH_IDS = [76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch04_substantive_execute(capability_id: int):
    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result.get("success") is True, result
    assert result.get("backend_module") == "cap646.official_batch_production"
    assert result.get("data_provenance") or result.get("provenance")
    assert result.get("latency_ms") is not None or result.get("performance_gate")
