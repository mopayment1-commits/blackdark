"""Tests for cap646.batch_spine Template Method."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_execute_and_enrich_batch_stamps_classification():
    from cap646.batch_spine import execute_and_enrich_batch

    async def handler(capability_id: int, *, params: dict):
        return {"success": True, "surface": "demo"}

    row = {"capability": "Demo", "track": "T04"}
    out = await execute_and_enrich_batch(handler, 47, row=row, params={"symbol": "BTC"})
    assert out["classification"] == "PRODUCTION-ALIGNED"
    assert out["capability_id"] == 47
