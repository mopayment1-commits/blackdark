"""Substantive v6 tests — official batch17 (IDs 401–425)."""

from __future__ import annotations

import pytest

from cap646.official_batch_production import execute

BATCH_IDS = [401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425]


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch17_substantive_execute(capability_id: int):
    result = await execute(
        capability_id,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    assert result.get("success") is True, result
    assert result.get("backend_module") == "cap646.official_batch_production"
    assert result.get("data_provenance") or result.get("provenance")
    assert result.get("latency_ms") is not None or result.get("performance_gate")
