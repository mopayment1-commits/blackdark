"""Launch-57 Phase 3 Decision Batch 2 — conviction + cross-market."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.decision_batch2 import (
    LAUNCH57_DECISION_BATCH2_CAP_IDS,
    cross_market_decision_engine,
    execute_launch57_decision_batch2,
    smart_money_conviction_engine,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {"price": 50000.0, "change_24h": 2.0, "freshness_state": FreshnessState.LIVE.value, "presented_as_live": True},
        "freshness": {"freshness_state": FreshnessState.LIVE.value},
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 2.0,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices", "phase1_batch2": "launch57.data_batch2:freshness_update_assurance"},
    }


@pytest.mark.asyncio
async def test_conviction_engine_live(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **k: {"alert_fired": True, "tier": k.get("user_tier")},
    )
    out = await smart_money_conviction_engine(symbol="BTC", params={"opportunity_level": 8.0})
    assert out["launch_item_id"] == 12
    assert out["conviction_score"] > 0
    assert out["price_source"] == "launch57.data_batch1"
    assert out["evidence_display"]["visible"] is True


@pytest.mark.asyncio
async def test_cross_market_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.UNKNOWN.value,
            "live_eligible": False,
            "presented_as_live": False,
            "data_spine": {},
        }

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    out = await cross_market_decision_engine(symbol="BTC", params={})
    assert out["launch_item_id"] == 37
    assert out["success"] is False
    assert out["presented_as_live"] is False


@pytest.mark.asyncio
async def test_cross_market_live_path(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.build_multi_dim_analysis_73",
        lambda asset: {
            "ok": True,
            "composite_score": 72,
            "asset": asset,
            "dimensions": {"technical": {"score": 72, "weight": 1.0, "source": "ta_engine"}},
        },
    )
    monkeypatch.setattr(
        "bd_platform.institutional_delivery_intelligence_layer.cross_market_decision_intelligence_567",
        lambda symbol: {"cross_market": True, "symbol": symbol},
    )
    out = await cross_market_decision_engine(symbol="ETH", params={})
    assert out["success"] is True
    assert out["decision_engine"]["composite_score"] == 72
    assert out["binding_source"] == "launch57_phase3_decision_batch2"


@pytest.mark.asyncio
async def test_kill_switch_batch2(monkeypatch):
    import launch57.decision_batch2 as mod

    async def broken(*a, **k):
        raise RuntimeError("kill_switch_batch2")

    monkeypatch.setattr(mod, "cross_market_decision_engine", broken)
    with pytest.raises(RuntimeError, match="kill_switch_batch2"):
        await execute_launch57_decision_batch2(29, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_execute_dispatch_batch2_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.build_multi_dim_analysis_73",
        lambda asset: {
            "ok": True,
            "composite_score": 50,
            "dimensions": {"technical": {"score": 50, "weight": 1.0, "source": "ta_engine"}},
        },
    )
    monkeypatch.setattr(
        "bd_platform.institutional_delivery_intelligence_layer.cross_market_decision_intelligence_567",
        lambda symbol: {},
    )
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **k: {"alert_fired": False},
    )
    for cap_id in LAUNCH57_DECISION_BATCH2_CAP_IDS:
        out = await execute_launch57_decision_batch2(cap_id, params={"symbol": "BTC"})
        assert out["binding_source"] == "launch57_phase3_decision_batch2"
