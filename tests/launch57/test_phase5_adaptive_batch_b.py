"""Launch-57 Phase 5 Adaptive Batch B — builder verification tests (#30→#33)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.derivatives_batch2 import (
    general_market_token_screener,
    limited_watchlists,
    order_book_intelligence,
    smart_alerts_composite,
)


def _live_spine(symbol: str = "BTC", change_24h: float = 1.0):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": change_24h,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices"},
    }


@pytest.mark.asyncio
async def test_capability_30_order_book_contradiction_surfaces(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol, change_24h=-2.5)

    async def fake_book(symbol):
        return {"bid": 100.0, "ask": 101.0, "bid_qty": 5.0, "ask_qty": 1.0}

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("cap646.fallbacks.resolve_order_book", fake_book)
    monkeypatch.setattr("live_book_hub.hub_stats", lambda: {"venues": 1})

    out = await order_book_intelligence(symbol="BTC", params={})
    assert out["launch_item_id"] == 30
    assert out["derivatives_contract"]["evidence_class"] == "direct"
    assert out["book_direction"] == "buy_pressure"
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "QUALIFIED_BOOK_CONTRADICTION"
    assert out["derivatives_contract"]["material_contradiction"]["type"] == "book_price_divergence"
    assert out["adaptive_disclosure"]["order_book_intelligence_disclosure"]["l1_minimum_met"] is True


@pytest.mark.asyncio
async def test_capability_31_unsupported_screener_scope_rejected(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_rankings():
        return {"rankings": [{"symbol": "BTC", "rank": 1}, {"symbol": "ETH", "rank": 2}]}

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.market_rankings.market_rankings", fake_rankings)

    approved = await general_market_token_screener(symbol="BTC", params={})
    rejected = await general_market_token_screener(
        symbol="BTC",
        params={"filter_scope": "institutional_mesh", "smart_money_only": True},
    )

    assert approved["launch_item_id"] == 31
    assert approved["success"] is True
    assert approved["adaptive_disclosure"]["level_1"]["answer_state"] == "GENERAL_MARKET_SCREENED"
    assert rejected["success"] is False
    assert rejected["screener"] == []
    assert rejected["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_SCOPE_REJECTED"
    assert rejected["adaptive_disclosure"]["general_market_screener_disclosure"]["unsupported_scope_rejected"] is True


@pytest.mark.asyncio
async def test_capability_32_unsupported_watchlist_domain_rejected(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.security_trust_data_layer.list_etherscan_watchlist_246",
        lambda: {"ok": True, "watches": [{"address": "0x1"}]},
    )

    approved = await limited_watchlists(symbol="BTC", params={})
    rejected = await limited_watchlists(symbol="BTC", params={"watchlist_domain": "cross_chain_all", "multi_venue_mesh": True})

    assert approved["launch_item_id"] == 32
    assert approved["success"] is True
    assert rejected["success"] is False
    assert rejected["wallet_watchlists"] == []
    assert rejected["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_DOMAIN_REJECTED"
    assert rejected["adaptive_disclosure"]["limited_watchlist_disclosure"]["unsupported_domain_rejected"] is True


@pytest.mark.asyncio
async def test_capability_33_unsupported_alert_class_rejected(monkeypatch):
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

    out = await smart_alerts_composite(symbol="BTC", params={"alert_classes": ["sentiment", "price"]})
    assert out["launch_item_id"] == 33
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_ALERT_CLASS_REJECTED"
    assert out["adaptive_disclosure"]["smart_alerts_disclosure"]["unsupported_class_rejected"] is True


@pytest.mark.asyncio
async def test_capability_33_stale_evidence_not_presented_as_live(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr("cap646.dedicated_common.exchange_netflow_probe", lambda p, s: ("binance", {"netflow_usd": 0}))
    async def fake_whale(limit=10):
        return []

    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_whale)
    monkeypatch.setattr("instant_alert_engine.engine_stats", lambda: {"enabled": True})
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.evaluate_flexible_alert_75",
        lambda user_tier, trigger: {"ok": True, "alert_fired": True, "trigger_age_ms": 120_000},
    )
    monkeypatch.setattr(
        "bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65",
        lambda **kw: {"alert_fired": False},
    )

    out = await smart_alerts_composite(symbol="BTC", params={})
    price_eval = out["smart_alerts"]["evaluations"]["price"]
    assert price_eval["evidence_state"] == "DELAYED"
    assert price_eval["presented_as_live"] is False
    assert "timestamp" in price_eval
    assert price_eval["target"] == "BTC"
    assert price_eval["user_action_path"] == "in_app_evaluation_and_api_response"
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "STALE_EVIDENCE_NOT_LIVE"
    assert out["success"] is False


@pytest.mark.asyncio
async def test_capability_33_approved_alerts_stamp_required_fields(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.derivatives_batch2.load_decision_spine", fake_spine)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr("cap646.dedicated_common.exchange_netflow_probe", lambda p, s: ("binance", {"netflow_usd": 2e6}))
    async def fake_whale(limit=10):
        return [{"symbol": "BTC"}]

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
    assert out["smart_alerts"]["fired_channels"]
    for channel in ("price", "flow", "whale", "decision"):
        row = out["smart_alerts"]["evaluations"][channel]
        assert row["timestamp"]
        assert row["freshness_state"] == FreshnessState.LIVE.value
        assert row["evidence_state"] == "LIVE"
        assert row["reason"]
        assert row["target"] == "BTC"
        assert row["user_action_path"] == "in_app_evaluation_and_api_response"
