"""Launch-57 Phase 5 — institutional intercept for derivatives caps."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute
from failure.freshness import FreshnessState


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_institutional_intercepts_cap85_batch1(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {"free_tier": {"open_interest_usd": 1e9}}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)
    out = await execute(85, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.derivatives_batch1"


@pytest.mark.asyncio
async def test_institutional_intercepts_cap50_batch2(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_book(symbol):
        return {"bid": 1, "ask": 2}

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("cap646.fallbacks.resolve_order_book", fake_book)
    monkeypatch.setattr("live_book_hub.hub_stats", lambda: {})
    out = await execute(50, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.derivatives_batch2"


@pytest.mark.asyncio
async def test_institutional_intercepts_cap508_batch2(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_book(symbol):
        return {"bid": 1, "ask": 2}

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("cap646.fallbacks.resolve_order_book", fake_book)
    out = await execute(508, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.derivatives_batch2"
