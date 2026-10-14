"""Public accuracy live_ledger must fail fast without blocking the payload."""

from __future__ import annotations

import asyncio
import time

import pytest


@pytest.mark.asyncio
async def test_live_ledger_query_times_out_quickly(monkeypatch):
    import ml.public_accuracy as pa

    async def slow_stats(*_args, **_kwargs):
        await asyncio.sleep(30)
        return {}

    monkeypatch.setattr(pa, "LIVE_LEDGER_QUERY_TIMEOUT_SEC", 0.05)
    monkeypatch.setattr("database.fetch_oracle_audit_stats", slow_stats)

    t0 = time.perf_counter()
    result = await pa._fetch_live_ledger_stats(20)
    elapsed = time.perf_counter() - t0

    assert result["query_ok"] is False
    assert "timed out" in (result["error"] or "")
    assert elapsed < 1.0
