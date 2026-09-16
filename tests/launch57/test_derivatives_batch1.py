"""Launch-57 Phase 5 Derivatives Batch 1 — stale gate, special rules, kill-switch."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.derivatives_batch1 import (
    LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS,
    execute_launch57_derivatives_batch1,
    funding_rate_intelligence,
    liquidation_intelligence_light,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.5,
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
async def test_funding_rate_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    out = await funding_rate_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 26
    assert out["success"] is False
    assert out["presented_as_live"] is False
    assert out["derivatives_habits_layer"]["phase"] == "5_DERIVATIVES_HABITS"


@pytest.mark.asyncio
async def test_liquidation_light_heatmap_disclaimer(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_radar(asset):
        return {"alerts": [{"type": "cluster"}], "metrics": {}, "data_source": "binance"}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.liquidation_radar.liquidation_radar", fake_radar)
    out = await liquidation_intelligence_light(symbol="BTC", params={})
    assert out["launch_item_id"] == 27
    assert out["liquidation_heatmap_light"]["global_coverage_claim"] == "FORBIDDEN"
    assert out["liquidation_heatmap_light"]["light_heatmap_scope"]["heatmap_scope"] == "light_preview_only"


@pytest.mark.asyncio
async def test_kill_switch_batch1(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_derivatives_batch1")

    import launch57.derivatives_batch1 as mod

    monkeypatch.setattr(mod, "futures_open_interest_intelligence", broken)
    with pytest.raises(RuntimeError, match="kill_switch_derivatives_batch1"):
        await execute_launch57_derivatives_batch1(85, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch1_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {"free_tier": {"open_interest_usd": 1e9, "funding_rate": 0.01, "taker_buy_ratio": 0.55}}

    async def fake_radar(asset):
        return {"alerts": [], "metrics": {}}

    async def fake_sentiment(symbol):
        return {"score": 0.6, "bias": "neutral"}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)
    monkeypatch.setattr("bd_platform.liquidation_radar.liquidation_radar", fake_radar)
    monkeypatch.setattr("bd_platform.heroes_capability_layer.leverage_ratio_overhang_197", lambda symbol: {"leverage_ratio": 1.2})
    monkeypatch.setattr("sentiment_engine.build_sentiment_context_safe", fake_sentiment)
    for cap_id in LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS:
        out = await execute_launch57_derivatives_batch1(cap_id, params={"symbol": "BTC"})
        assert out["binding_source"] == "launch57_phase5_derivatives_batch1"
        assert out["backend_module"] == "launch57.derivatives_batch1"
