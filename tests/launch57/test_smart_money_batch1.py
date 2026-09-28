"""Launch-57 Phase 4 Smart Money Batch 1 — stale gate, live path, kill-switch."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.smart_money_batch1 import (
    LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS,
    address_labels_cohorts,
    execute_launch57_smart_money_batch1,
    exchange_flow_intelligence,
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
        "data_spine": {},
    }


def _stale_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {"freshness_state": FreshnessState.STALE.value},
        "freshness": {"freshness_state": FreshnessState.STALE.value},
        "freshness_state": FreshnessState.STALE.value,
        "live_eligible": False,
        "presented_as_live": False,
        "price": None,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_address_labels_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    out = await address_labels_cohorts(symbol="BTC", params={"address": "0xabc"})
    assert out["launch_item_id"] == 20
    assert out["success"] is False
    assert out["presented_as_live"] is False
    assert out["smart_money_layer"]["phase"] == "4_SMART_MONEY_INSTANT"


@pytest.mark.asyncio
async def test_exchange_flow_live_path(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "cap646.dedicated_common.exchange_netflow_probe",
        lambda p, s: ("binance", {"inflow_usd": 1e6, "outflow_usd": 0.5e6, "netflow_usd": 0.5e6}),
    )
    out = await exchange_flow_intelligence(symbol="BTC", params={})
    assert out["success"] is True
    assert out["exchange_flow"]["netflow_usd"] == 0.5e6
    assert out["binding_source"] == "launch57_phase4_smart_money_batch1"
    assert out["evidence_class_visible"] is True


@pytest.mark.asyncio
async def test_token_screener_live(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_board(limit=25):
        return {"leaderboard": [{"symbol": "BTC", "amount_usd": 1e6, "entity": "fund_a"}]}

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.free_tier_capabilities.smart_money_leaderboard", fake_board)
    out = await smart_money_token_screener(symbol="BTC", params={})
    assert out["launch_item_id"] == 14
    assert out["success"] is True
    assert out["screener"]


@pytest.mark.asyncio
async def test_kill_switch_raises(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_test")

    import launch57.smart_money_batch1 as mod

    monkeypatch.setattr(mod, "address_labels_cohorts", broken)
    with pytest.raises(RuntimeError, match="kill_switch_test"):
        await execute_launch57_smart_money_batch1(92, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch1_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.onchain_platform_layer.b2b_relationships_status_137", lambda seed=0: {"labels": []})
    monkeypatch.setattr(
        "cap646.dedicated_common.exchange_netflow_probe",
        lambda p, s: ("binance", {"inflow_usd": 1, "outflow_usd": 0, "netflow_usd": 1}),
    )
    monkeypatch.setattr(
        "bd_platform.heroes_capability_layer.exchange_netflow_intelligence_48",
        lambda exchange, asset: {"net": 1},
    )
    monkeypatch.setattr("bd_platform.market_analysis_layer.compute_whale_ls_ratio_114", lambda seed=0: {"whale_filtered_ratio": 0.5})
    monkeypatch.setattr(
        "exchange_internal_flow_filter.classify_flow",
        lambda **kw: {"internal": False},
    )
    async def fake_narratives(limit=10):
        return {"narratives": []}

    monkeypatch.setattr("whale_signal_classifier.enrich_whale_narratives", fake_narratives)
    async def fake_leaderboard(limit=25):
        return {"leaderboard": []}

    monkeypatch.setattr("bd_platform.free_tier_capabilities.smart_money_leaderboard", fake_leaderboard)
    for cap_id in LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS:
        out = await execute_launch57_smart_money_batch1(cap_id, params={"symbol": "BTC"})
        assert out["binding_source"] == "launch57_phase4_smart_money_batch1"
        assert out["backend_module"] == "launch57.smart_money_batch1"
