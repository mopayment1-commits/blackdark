"""Launch-57 Phase 3 Adaptive Batch B — builder verification tests (#12→#37)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.decision_batch2 import cross_market_decision_engine, smart_money_conviction_engine


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
        "data_spine": {
            "phase1_batch1": "launch57.data_batch1:real_time_prices",
            "phase1_batch2": "launch57.data_batch2:freshness_update_assurance",
        },
    }


@pytest.mark.asyncio
async def test_capability_12_structured_conviction_with_disagreement_visible(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **k: {"alert_fired": False, "tier": k.get("user_tier")},
    )
    out = await smart_money_conviction_engine(
        symbol="BTC",
        params={"opportunity_level": 8.0, "volume_zscore": 2.5},
    )
    disc = out["structured_conviction_disclosure"]
    assert out["launch_item_id"] == 12
    assert disc["material_disagreement_visible"] is True
    assert disc["disagreement_count"] >= 1
    assert any(d["type"] == "high_opportunity_no_alert" for d in disc["material_disagreements"])
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 12
    assert out["adaptive_disclosure"]["level_1"]["uncertainty"] == "qualified"


@pytest.mark.asyncio
async def test_capability_12_high_conviction_when_alert_fires(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **k: {"alert_fired": True, "tier": k.get("user_tier")},
    )
    out = await smart_money_conviction_engine(symbol="BTC", params={"opportunity_level": 8.0})
    disc = out["structured_conviction_disclosure"]
    assert out["conviction_score"] >= 75
    assert disc["structured_conviction"]["band"] == "high_conviction"
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "high_conviction"


@pytest.mark.asyncio
async def test_capability_37_flags_unapproved_evidence_composition(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.build_multi_dim_analysis_73",
        lambda asset: {
            "ok": True,
            "composite_score": 72,
            "asset": asset,
            "dimensions": {
                "technical": {"score": 7, "weight": 0.3, "source": "ta_engine"},
                "macro": {"score": 4, "weight": 0.25, "source": "external_macro"},
            },
        },
    )
    monkeypatch.setattr(
        "bd_platform.institutional_delivery_intelligence_layer.cross_market_decision_intelligence_567",
        lambda symbol: {"cross_market": True, "symbol": symbol},
    )
    out = await cross_market_decision_engine(symbol="ETH", params={})
    comp = out["approved_evidence_composition"]
    assert out["launch_item_id"] == 37
    assert comp["approved_launch57_evidence_only"] is False
    assert any(c.get("source") == "external_macro" for c in comp["unapproved_components"])
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNAPPROVED_EVIDENCE_PRESENT"


@pytest.mark.asyncio
async def test_capability_37_approved_launch57_only_composition(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.build_multi_dim_analysis_73",
        lambda asset: {
            "ok": True,
            "composite_score": 70,
            "asset": asset,
            "dimensions": {
                "technical": {"score": 7, "weight": 0.3, "source": "ta_engine"},
                "on_chain": {"score": 6, "weight": 0.25, "source": "on_chain_extension"},
                "sentiment": {"score": 5, "weight": 0.2, "source": "sentiment_layer"},
            },
        },
    )
    monkeypatch.setattr(
        "bd_platform.institutional_delivery_intelligence_layer.cross_market_decision_intelligence_567",
        lambda symbol: {"cross_market": True, "symbol": symbol},
    )
    out = await cross_market_decision_engine(symbol="BTC", params={})
    comp = out["approved_evidence_composition"]
    assert comp["approved_launch57_evidence_only"] is True
    assert comp["unapproved_components"] == []
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "APPROVED_LAUNCH57_ONLY"
