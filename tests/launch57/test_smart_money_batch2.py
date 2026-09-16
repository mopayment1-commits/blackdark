"""Launch-57 Phase 4 Smart Money Batch 2 — entity, whale alerts, instant DD."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.smart_money_batch2 import (
    LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS,
    execute_launch57_smart_money_batch2,
    inter_entity_flow_intelligence,
    instant_token_due_diligence,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "data_spine": {},
    }


def _stale_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.STALE.value,
        "live_eligible": False,
        "presented_as_live": False,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_inter_entity_limited_scope(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_ctx():
        return {"flows": [{"entity": "a", "entity_b": "b"}]}

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_ctx)
    out = await inter_entity_flow_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 19
    assert out["limited_launch_scope"]["paid_leaderboard_full"] is False
    assert out["limited_launch_scope"]["limited_launch_scope"] is True


@pytest.mark.asyncio
async def test_instant_token_dd_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    out = await instant_token_due_diligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 54
    assert out["success"] is False
    assert out["presented_as_live"] is False


@pytest.mark.asyncio
async def test_kill_switch_batch2(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_batch2")

    import launch57.smart_money_batch2 as mod

    monkeypatch.setattr(mod, "entity_aware_wallet_intelligence", broken)
    with pytest.raises(RuntimeError, match="kill_switch_batch2"):
        await execute_launch57_smart_money_batch2(14, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch2_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    async def fake_search(address, chain="ethereum"):
        return {"ok": True, "entity_label": "test", "labels": []}

    async def fake_alerts(limit=20):
        return [{"symbol": "BTC"}]

    async def fake_ctx():
        return {"flows": []}

    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_search)
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_alerts)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_ctx)
    monkeypatch.setattr(
        "bd_platform.whales_institutional_layer.analyze_wallet_surveillance_79",
        lambda wallet: {"surveillance_detected": False},
    )
    async def fake_holders(symbol):
        return {"available": True, "metrics": {"locked_supply_pct": 10}}

    async def fake_models(symbol, notional=10000):
        return {"ok": True}

    monkeypatch.setattr("bd_platform.free_integrations.holder_analytics", fake_holders)
    monkeypatch.setattr("research_lab.compute_financial_models", fake_models)
    for cap_id in LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS:
        out = await execute_launch57_smart_money_batch2(cap_id, params={"symbol": "BTC", "address": "0x1"})
        assert out["binding_source"] == "launch57_phase4_smart_money_batch2"
