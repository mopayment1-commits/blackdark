"""Substantive v6 tests — official batch11 (IDs 251–275)."""

from __future__ import annotations

import pytest

from cap646.official_batch_production import execute

BATCH_IDS = [252, 253, 254, 258, 259, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 273, 274]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch11_substantive_execute(capability_id: int):
    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result.get("success") is True, result
    assert result.get("backend_module") == "cap646.official_batch_production"
    assert result.get("data_provenance") or result.get("provenance")
    assert result.get("latency_ms") is not None or result.get("performance_gate")
