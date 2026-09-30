"""Launch-57 Phase 3 Decision Batch 1 — runtime, stale gate, net-edge gate, kill-switch."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.decision_batch1 import (
    LAUNCH57_DECISION_BATCH1_CAP_IDS,
    cross_signal_confirmation,
    execute_launch57_decision_batch1,
    market_regime_compass,
    smart_money_actionability_score,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {"price": 50000.0, "change_24h": 1.5, "freshness_state": FreshnessState.LIVE.value, "presented_as_live": True},
        "freshness": {"freshness_state": FreshnessState.LIVE.value, "presented_as_live": True},
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.5,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices", "phase1_batch2": "launch57.data_batch2:freshness_update_assurance"},
    }


def _stale_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {"freshness_state": FreshnessState.STALE.value, "presented_as_live": False},
        "freshness": {"freshness_state": FreshnessState.STALE.value},
        "freshness_state": FreshnessState.STALE.value,
        "live_eligible": False,
        "presented_as_live": False,
        "price": None,
        "change_24h": None,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices", "phase1_batch2": "launch57.data_batch2:freshness_update_assurance"},
    }


@pytest.mark.asyncio
async def test_market_regime_blocks_stale_not_live(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    out = await market_regime_compass(symbol="BTC", params={})
    assert out["launch_item_id"] == 7
    assert out["success"] is False
    assert out["presented_as_live"] is False
    assert out["error"] == "decision_blocked_stale_or_unknown_data"
    assert out["evidence_display"]["visible"] is True


@pytest.mark.asyncio
async def test_market_regime_live_path(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_ctx():
        return {"macro_regime": "Risk-On"}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_ctx)
    out = await market_regime_compass(symbol="BTC", params={})
    assert out["success"] is True
    assert out["market_compass"]["regime"]
    assert out["presented_as_live"] is True
    assert out["binding_source"] == "launch57_phase3_decision_batch1"
    assert out["evidence_class_visible"] is True


@pytest.mark.asyncio
async def test_cross_signal_confirmation_uses_spine_price(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_sentiment(sym):
        return {"bias": "bullish", "signals": ["bullish"]}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("sentiment_gate.fetch_asset_sentiment", fake_sentiment)
    monkeypatch.setattr("signal_registry.registry_stats", lambda: {"total": 1})
    out = await cross_signal_confirmation(symbol="BTC", params={})
    assert out["launch_item_id"] == 9
    assert out["cross_signal_confirmation"]["price_change_24h"] == 1.5
    assert out["cross_signal_confirmation"]["price_source"] == "launch57.data_batch1"


@pytest.mark.asyncio
async def test_actionability_blocks_cost_claim_without_net_edge(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", lambda limit=10: [])
    out = await smart_money_actionability_score(symbol="BTC", params={"cost_claim": True})
    assert out["launch_item_id"] == 11
    assert out["success"] is False
    assert out["cost_claim_blocked"] is True
    assert "net_edge" in str(out.get("error", "")).lower() or "opportunity" in str(out.get("error", "")).lower()


@pytest.mark.asyncio
async def test_kill_switch_raises_runtime_error(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_test")

    import launch57.decision_batch1 as mod

    monkeypatch.setattr(mod, "market_regime_compass", broken)
    with pytest.raises(RuntimeError, match="kill_switch_test"):
        await execute_launch57_decision_batch1(35, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_execute_dispatch_all_batch1_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    for cap_id in LAUNCH57_DECISION_BATCH1_CAP_IDS:
        out = await execute_launch57_decision_batch1(cap_id, params={"symbol": "BTC", "verdict": "Neutral"})
        assert out["binding_source"] == "launch57_phase3_decision_batch1"
