"""Launch-57 Phase 4 — institutional intercept for smart money caps."""

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
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_institutional_intercepts_cap92_batch1(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.onchain_platform_layer.b2b_relationships_status_137",
        lambda seed=0: {"labels": ["exchange"]},
    )
    out = await execute(92, params={"symbol": "BTC", "address": "0x1"})
    assert out["handler_module"] == "launch57.smart_money_batch1"


@pytest.mark.asyncio
async def test_institutional_intercepts_cap14_batch2(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    async def fake_search(address, chain="ethereum"):
        return {"ok": True, "labels": []}

    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_search)
    out = await execute(14, params={"symbol": "BTC", "address": "0x1"})
    assert out["handler_module"] == "launch57.smart_money_batch2"


@pytest.mark.asyncio
async def test_runtime_intercepts_cap916_batch3(monkeypatch):
    from cap646.runtime import execute_capability

    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.institutional_b2b_layer.build_exchange_health_with_counterparty_92",
        lambda exchange="binance", withdrawal_latency_hours=12.0, seed=None: {"exchange": exchange},
    )
    out = await execute_capability(916, params={"symbol": "BTC", "exchange": "binance"}, skip_entitlement=True)
    assert out["handler_module"] == "launch57.smart_money_batch3"
