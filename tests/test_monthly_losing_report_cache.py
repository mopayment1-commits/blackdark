"""Monthly losing report response cache."""

from __future__ import annotations

import asyncio

import monthly_losing_report as mlr


def test_monthly_losing_report_cached(monkeypatch):
    calls = 0

    async def fake_uncached(*, limit: int = 25):
        nonlocal calls
        calls += 1
        return {"month": "2026-10", "sample": [], "months": []}

    monkeypatch.setattr(mlr, "_MLR_CACHE", {})
    monkeypatch.setattr(mlr, "_MLR_CACHE_TTL_SEC", 60.0)
    monkeypatch.setattr(mlr, "_build_monthly_losing_report_uncached", fake_uncached)

    async def run():
        await mlr.build_monthly_losing_report(limit=12)
        await mlr.build_monthly_losing_report(limit=12)

    asyncio.run(run())
    assert calls == 1
