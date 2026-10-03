"""Launch-57 Phase 5 Derivatives Batch 2 — order book L1, watchlists, smart alerts."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.derivatives_batch2 import (
    LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS,
    execute_launch57_derivatives_batch2,
    limited_watchlists,
    order_book_intelligence,
    smart_alerts_composite,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 5.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_order_book_l1_depth_declaration(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_book(symbol):
        return {"bid": 49999, "ask": 50001}

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("cap646.fallbacks.resolve_order_book", fake_book)
    monkeypatch.setattr("live_book_hub.hub_stats", lambda: {"venues": 1})
    out = await order_book_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 30
    assert out["depth_level"] == "L1"
    assert out["deeper_than_l1"] is False
    assert out["order_book_depth"]["l1_minimum_met"] is True


@pytest.mark.asyncio
async def test_limited_watchlists_scope(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.security_trust_data_layer.list_etherscan_watchlist_246",
        lambda: {"ok": True, "watches": [{"address": "0x1"}]},
    )
    out = await limited_watchlists(symbol="BTC", params={})
    assert out["launch_item_id"] == 32
    assert out["limited_watchlist_scope"]["limited_launch_scope"] is True


@pytest.mark.asyncio
async def test_smart_alerts_blocked_external_when_no_telegram(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_whale(limit=10):
        return [{"symbol": "BTC", "amount_usd": 2e6}]

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr("cap646.dedicated_common.exchange_netflow_probe", lambda p, s: ("binance", {"netflow_usd": 2e6}))
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_whale)
    monkeypatch.setattr("instant_alert_engine.engine_stats", lambda: {"enabled": True})
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.evaluate_flexible_alert_75",
        lambda user_tier, trigger: {"ok": True, "alert_fired": True},
    )
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **kw: {"alert_fired": True},
    )
    out = await smart_alerts_composite(symbol="BTC", params={})
    assert out["launch_item_id"] == 33
    assert out["delivery_status"] == "BLOCKED_EXTERNAL"
    assert out["blocked_external"] is True
    assert out["external_delivery"]["local_evaluation"] is True
    assert out["smart_alerts"]["fired_channels"]


@pytest.mark.asyncio
async def test_kill_switch_batch2(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_derivatives_batch2")

    import launch57.derivatives_batch2 as mod

    monkeypatch.setattr(mod, "order_book_intelligence", broken)
    with pytest.raises(RuntimeError, match="kill_switch_derivatives_batch2"):
        await execute_launch57_derivatives_batch2(50, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch2_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_book(symbol):
        return {"bid": 1, "ask": 2}

    async def fake_rankings():
        return {"rankings": [{"symbol": "BTC"}]}

    async def fake_whale(limit=10):
        return []

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("cap646.fallbacks.resolve_order_book", fake_book)
    monkeypatch.setattr("live_book_hub.hub_stats", lambda: {})
    monkeypatch.setattr("bd_platform.market_rankings.market_rankings", fake_rankings)
    monkeypatch.setattr(
        "bd_platform.security_trust_data_layer.list_etherscan_watchlist_246",
        lambda: {"ok": True, "watches": []},
    )
    monkeypatch.setattr("cap646.dedicated_common.exchange_netflow_probe", lambda p, s: ("binance", {"netflow_usd": 0}))
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_whale)
    monkeypatch.setattr("instant_alert_engine.engine_stats", lambda: {})
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.evaluate_flexible_alert_75",
        lambda user_tier, trigger: {"ok": False, "alert_fired": False},
    )
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **kw: {"alert_fired": False},
    )
    for cap_id in LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS:
        out = await execute_launch57_derivatives_batch2(cap_id, params={"symbol": "BTC"})
        assert out["binding_source"] == "launch57_phase5_derivatives_batch2"
