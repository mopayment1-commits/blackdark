"""Launch-57 Phase 4 Adaptive Batch A — builder verification tests (#20→#16→#17→#13→#14)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.smart_money_batch1 import (
    accumulation_distribution_detection,
    address_labels_cohorts,
    exchange_flow_intelligence,
    exchange_whale_ratio,
    internal_flow_filter,
    smart_money_token_screener,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {"price": 50000.0, "change_24h": 1.5, "freshness_state": FreshnessState.LIVE.value, "presented_as_live": True},
        "freshness": {"freshness_state": FreshnessState.LIVE.value},
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.5,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices"},
    }


@pytest.mark.asyncio
async def test_capability_20_attribution_distinct_from_raw_movement(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.onchain_platform_layer.b2b_relationships_status_137",
        lambda seed=0: {"labels": [{"address": "0xabc", "label": "fund"}]},
    )
    out = await address_labels_cohorts(symbol="BTC", params={"address": "0xabc"})
    disc = out["attribution_cohort_disclosure"]
    assert out["launch_item_id"] == 20
    assert disc["attribution_distinct_from_raw_movement"] is True
    assert disc["cohort_interpretation_not_raw_flow"] is True
    assert disc["coverage_limits_visible"] is True
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 20


@pytest.mark.asyncio
async def test_capability_16_exchange_flow_not_generic_movement(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "cap646.dedicated_common.exchange_netflow_probe",
        lambda p, s: ("binance", {"inflow_usd": 1e6, "outflow_usd": 0.5e6, "netflow_usd": 0.5e6}),
    )
    out = await exchange_flow_intelligence(symbol="BTC", params={})
    disc = out["exchange_flow_disclosure"]
    assert out["launch_item_id"] == 16
    assert disc["exchange_flow_not_generic_movement"] is True
    assert disc["certainty_not_implied"] is True
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "NET_INFLOW"


@pytest.mark.asyncio
async def test_capability_17_whale_ratio_preserves_internal_flow_filter(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.market_analysis_layer.compute_whale_ls_ratio_114",
        lambda seed=0: {"whale_filtered_ratio": 1.5, "whale_bias": "long", "noise_filter_usd": 50000},
    )
    out = await exchange_whale_ratio(symbol="BTC", params={})
    disc = out["whale_ratio_internal_flow_disclosure"]
    assert out["launch_item_id"] == 17
    assert disc["internal_flow_filter_preserved"] is True
    assert disc["misclassification_guard_active"] is True


@pytest.mark.asyncio
async def test_capability_17_internal_flow_not_external(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "exchange_internal_flow_filter.classify_flow",
        lambda **kw: {"classification": "INTERNAL_CONFIRMED", "confidence": 0.95},
    )
    out = await internal_flow_filter(symbol="BTC", params={})
    disc = out["internal_flow_filter_disclosure"]
    assert out["launch_item_id"] == 17
    assert disc["internal_not_external_flow"] is True
    assert disc["misclassification_guard"] is True


@pytest.mark.asyncio
async def test_capability_13_accumulation_is_inference_with_uncertainty(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_narratives(limit=10):
        return {"narratives": [{"symbol": "BTC", "type": "accumulation"}]}

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("whale_signal_classifier.enrich_whale_narratives", fake_narratives)
    out = await accumulation_distribution_detection(symbol="BTC", params={})
    disc = out["accumulation_distribution_disclosure"]
    assert out["launch_item_id"] == 13
    assert disc["inference_not_raw_flow_fact"] is True
    assert disc["supporting_evidence_visible"] is True
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "INFERRED"


@pytest.mark.asyncio
async def test_capability_14_screener_from_approved_launch57_evidence(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_board(limit=25):
        return {"leaderboard": [{"symbol": "BTC", "amount_usd": 1e6, "entity": "fund_a"}]}

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.free_tier_capabilities.smart_money_leaderboard", fake_board)
    out = await smart_money_token_screener(symbol="BTC", params={})
    disc = out["smart_money_screener_disclosure"]
    assert out["launch_item_id"] == 14
    assert disc["screening_from_approved_launch57_evidence"] is True
    assert disc["raw_movement_not_collapsed_to_certainty"] is True
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "SCREENED"
