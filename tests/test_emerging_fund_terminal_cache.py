"""Emerging fund terminal pack cache."""

from __future__ import annotations

import asyncio

import emerging_fund_terminal as eft


def test_fund_terminal_pack_cached(monkeypatch):
    calls = 0

    def fake_proof():
        nonlocal calls
        calls += 1
        return {
            "summary": {"recent_hit_rate_percent": 50.0, "total_records": 10},
            "verify": {"valid": True},
        }

    monkeypatch.setattr(eft, "_FUND_PACK_CACHE", {})
    monkeypatch.setattr(eft, "_FUND_PACK_CACHE_TTL_SEC", 60.0)
    monkeypatch.setattr("ml.public_accuracy._proof_chain_block", fake_proof)

    async def run():
        await eft.build_fund_terminal_pack(fund_name="Test Fund")
        await eft.build_fund_terminal_pack(fund_name="Test Fund")

    asyncio.run(run())
    assert calls == 1
