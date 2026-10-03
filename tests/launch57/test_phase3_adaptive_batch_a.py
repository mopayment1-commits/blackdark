"""Launch-57 Phase 3 Adaptive Batch A — builder verification tests (#7→#8→#9→#10→#11)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.decision_batch1 import (
    beginner_decision_mode,
    contradiction_detection,
    cross_signal_confirmation,
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


@pytest.mark.asyncio
async def test_capability_7_market_context_no_trade_instruction(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_ctx():
        return {"macro_regime": "Risk-On"}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_ctx)
    out = await market_regime_compass(symbol="BTC", params={})
    ctx = out["market_context_disclosure"]
    assert out["launch_item_id"] == 7
    assert ctx["context_only"] is True
    assert ctx["standalone_trade_instruction"] is False
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 7


@pytest.mark.asyncio
async def test_capability_8_beginner_material_risk_visible(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    out = await beginner_decision_mode(symbol="BTC", params={"verdict": "Risk", "risk_score": 8.5})
    simp = out["beginner_simplification_disclosure"]
    assert out["launch_item_id"] == 8
    assert simp["material_risk_visible"] is True
    assert simp["risk_score"] == 8.5
    assert out["adaptive_disclosure"]["level_1"]["critical_limitation"]


@pytest.mark.asyncio
async def test_capability_9_duplicated_evidence_not_independent(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_sentiment(sym):
        return {"bias": "bullish", "signals": ["bullish", "bullish"]}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("sentiment_gate.fetch_asset_sentiment", fake_sentiment)
    monkeypatch.setattr("signal_registry.registry_stats", lambda: {"total": 2})
    out = await cross_signal_confirmation(symbol="BTC", params={})
    dep = out["cross_signal_confirmation"]["dependence_aware_confirmation"]
    assert out["launch_item_id"] == 9
    assert dep["duplicated_evidence_not_independent"] is True
    assert dep["independent_confirmation"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNCONFIRMED"


@pytest.mark.asyncio
async def test_capability_10_material_contradiction_impact(monkeypatch):
    async def fake_spine(symbol, params=None):
        spine = _live_spine(symbol)
        spine["change_24h"] = 3.5
        return spine

    async def fake_sentiment(sym):
        return {"bias": "bearish", "signals": ["bearish"]}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("sentiment_gate.fetch_asset_sentiment", fake_sentiment)
    out = await contradiction_detection(symbol="BTC", params={})
    impact = out["contradiction_detection"]["material_contradiction_impact"]
    assert out["launch_item_id"] == 10
    assert impact["decision_impact"] == "WAIT"
    assert impact["material_contradiction"] is not None
    assert out["adaptive_disclosure"]["level_1"]["critical_contradiction"]


@pytest.mark.asyncio
async def test_capability_11_actionability_without_unsupported_precision(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_alerts(limit=10):
        return [{"id": 1}, {"id": 2}]

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_alerts)
    out = await smart_money_actionability_score(symbol="BTC", params={})
    action = out["actionability_disclosure"]
    assert out["launch_item_id"] == 11
    assert action["unsupported_precision_blocked"] is True
    assert action["qualitative_band"] in {"low_watch", "moderate_watch", "high_watch"}
    assert action["actionability_not_trade_instruction"] is True
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 11
