"""Emerging fund terminal pack cache."""

from __future__ import annotations

import asyncio

import emerging_fund_terminal as eft


def test_fund_terminal_pack_cached(monkeypatch):
    calls = 0

    async def fake_build(*, recent_limit: int = 8):
        nonlocal calls
        calls += 1
        return {"oracle": {}, "proof_chain": {"verify": {"valid": True}}}

    monkeypatch.setattr(eft, "_FUND_PACK_CACHE", {})
    monkeypatch.setattr(eft, "_FUND_PACK_CACHE_TTL_SEC", 60.0)
    monkeypatch.setattr(
        "ml.public_accuracy.build_public_accuracy_payload",
        fake_build,
    )

    async def run():
        await eft.build_fund_terminal_pack(fund_name="Test Fund")
        await eft.build_fund_terminal_pack(fund_name="Test Fund")

    asyncio.run(run())
    assert calls == 1
