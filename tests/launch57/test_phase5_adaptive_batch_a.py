"""Launch-57 Phase 5 Adaptive Batch A — builder verification tests (#25→#29)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.derivatives_batch1 import (
    derivatives_sentiment_composite,
    estimated_leverage_ratio,
    funding_rate_intelligence,
    futures_open_interest_intelligence,
    liquidation_intelligence_light,
    taker_buy_sell_pressure,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.5,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices"},
    }


@pytest.mark.asyncio
async def test_capability_25_oi_contradiction_surfaces_in_semantics(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {
            "free_tier": {
                "available": True,
                "open_interest_usd": 2_000_000_000,
                "open_interest_contracts": 40_000,
                "change_24h_pct": 2.5,
                "funding_rate": 0.001,
                "taker_buy_sell_ratio": 0.8,
            }
        }

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)

    out = await futures_open_interest_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 25
    assert out["derivatives_contract"]["evidence_class"] == "direct"
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "QUALIFIED_OI_CONTRADICTION"
    assert out["derivatives_contract"]["material_contradiction"]["type"] == "funding_taker_divergence"
    assert out["adaptive_disclosure"]["open_interest_derivatives_disclosure"]["material_contradiction_visible"] is True


@pytest.mark.asyncio
async def test_capability_26_funding_direction_and_contradiction(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {
            "free_tier": {
                "available": True,
                "funding_rate": 0.002,
                "funding_rate_pct": 0.2,
                "taker_buy_sell_ratio": 0.7,
            }
        }

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)

    out = await funding_rate_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 26
    assert out["funding_direction"] == "long_crowded"
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "QUALIFIED_FUNDING_CONTRADICTION"
    assert out["derivatives_contract"]["direction"] == "long_crowded"
    assert out["adaptive_disclosure"]["funding_rate_derivatives_disclosure"]["evidence_class"] == "direct"


@pytest.mark.asyncio
async def test_capability_27_empty_liquidation_not_promoted(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_radar(asset):
        return {"alerts": [], "metrics": {}, "data_source": "binance"}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.liquidation_radar.liquidation_radar", fake_radar)

    out = await liquidation_intelligence_light(symbol="BTC", params={})
    assert out["launch_item_id"] == 27
    assert out["success"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "NO_QUALIFYING_LIQUIDATION_CLUSTER"
    assert out["adaptive_disclosure"]["liquidation_derivatives_disclosure"]["light_heatmap_not_global_coverage"] is True
    assert out["derivatives_contract"]["material_limitation"]["global_liquidation_coverage_claim"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_capability_28_taker_leverage_disagreement_visible(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {"free_tier": {"available": True, "taker_buy_sell_ratio": 1.4, "funding_rate": 0.0001}}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)
    monkeypatch.setattr(
        "bd_platform.heroes_capability_layer.leverage_ratio_overhang_197",
        lambda symbol: {"fragility": "red", "overhang_factor": 3.5, "leverage_ratio": 12.0},
    )

    out = await estimated_leverage_ratio(symbol="BTC", params={})
    assert out["launch_item_id"] == 28
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "COMPONENT_DISAGREEMENT"
    assert out["derivatives_semantics"]["material_disagreements"]
    assert out["adaptive_disclosure"]["taker_leverage_derivatives_disclosure"]["component_disagreement_visible"] is True
    assert out["derivatives_contract"]["evidence_class"] == "composite"


@pytest.mark.asyncio
async def test_capability_28_taker_only_semantics_without_leverage(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {"free_tier": {"available": True, "taker_buy_ratio": 0.62}}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)

    out = await taker_buy_sell_pressure(symbol="BTC", params={})
    assert out["taker_direction"] == "buy_pressure"
    assert out["derivatives_contract"]["direction"] == "buy_pressure"
    assert out["adaptive_disclosure"]["level_1"]["freshness_state"] == FreshnessState.LIVE.value


@pytest.mark.asyncio
async def test_capability_29_composite_suppresses_unified_score_on_disagreement(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {
            "free_tier": {
                "available": True,
                "funding_rate": -0.001,
                "taker_buy_sell_ratio": 0.75,
            }
        }

    async def fake_sentiment(symbol):
        return {"score": 0.7, "bias": "bullish"}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)
    monkeypatch.setattr("sentiment_engine.build_sentiment_context_safe", fake_sentiment)

    out = await derivatives_sentiment_composite(symbol="BTC", params={})
    assert out["launch_item_id"] == 29
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "COMPONENT_DISAGREEMENT"
    assert out["composite_score"] is None
    assert out["observable_sentiment_score"] == 0.7
    assert out["material_disagreements"]
    assert (
        out["adaptive_disclosure"]["derivatives_composite_disclosure"][
            "decision_driving_composite_suppressed_on_disagreement"
        ]
        is True
    )


@pytest.mark.asyncio
async def test_capability_29_aligned_composite_preserves_decision_score(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_overview(symbol):
        return {
            "free_tier": {
                "available": True,
                "funding_rate": 0.001,
                "taker_buy_sell_ratio": 1.2,
            }
        }

    async def fake_sentiment(symbol):
        return {"score": 0.65, "bias": "bullish"}

    monkeypatch.setattr("launch57.derivatives_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.derivatives_hub.derivatives_overview", fake_overview)
    monkeypatch.setattr("sentiment_engine.build_sentiment_context_safe", fake_sentiment)

    out = await derivatives_sentiment_composite(symbol="BTC", params={})
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "ALIGNED_COMPOSITE"
    assert out["composite_score"] == 0.65
    assert not out["material_disagreements"]
