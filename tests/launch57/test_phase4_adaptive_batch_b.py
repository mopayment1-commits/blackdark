"""Launch-57 Phase 4 Adaptive Batch B — builder verification tests (#15→#18→#19→#53→#54)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.smart_money_batch2 import (
    entity_aware_wallet_intelligence,
    instant_token_due_diligence,
    instant_wallet_due_diligence,
    inter_entity_flow_intelligence,
    whale_accumulation_distribution_intelligence,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {
            "price": 50000.0,
            "change_24h": 1.5,
            "freshness_state": FreshnessState.LIVE.value,
            "presented_as_live": True,
        },
        "freshness": {"freshness_state": FreshnessState.LIVE.value},
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.5,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices"},
    }


@pytest.mark.asyncio
async def test_capability_15_entity_interpretation_changes_with_attribution(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_attributed(address, chain="ethereum"):
        return {
            "ok": True,
            "entity_label": "fund_alpha",
            "labels": {"labels": [{"label": "fund_alpha"}]},
            "total_usd": 5_000_000,
            "data_state": "LIVE",
        }

    async def fake_unattributed(address, chain="ethereum"):
        return {
            "ok": True,
            "entity_label": None,
            "labels": {"labels": []},
            "total_usd": 5_000_000,
            "data_state": "LIVE",
        }

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_attributed)
    attributed = await entity_aware_wallet_intelligence(symbol="BTC", params={"address": "0xabc"})
    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_unattributed)
    unattributed = await entity_aware_wallet_intelligence(symbol="BTC", params={"address": "0xabc"})

    assert attributed["total_usd"] == unattributed["total_usd"]
    assert attributed["adaptive_disclosure"]["level_1"]["answer_state"] == "ATTRIBUTED"
    assert unattributed["adaptive_disclosure"]["level_1"]["answer_state"] == "UNATTRIBUTED"
    assert attributed["entity_wallet_disclosure"]["certainty_not_implied"] is False
    assert unattributed["entity_wallet_disclosure"]["certainty_not_implied"] is True


@pytest.mark.asyncio
async def test_capability_18_whale_alert_runtime_qualification_filter(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    noise_alert = {
        "symbol": "BTC",
        "direction": "in",
        "detail": "internal custody rebalance to cold wallet",
        "amount_usd": 10_000_000,
    }
    signal_alert = {
        "symbol": "BTC",
        "direction": "accumulation in",
        "detail": "large spot accumulation",
        "amount_usd": 10_000_000,
    }

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)

    async def fake_noise_alerts(limit=20):
        return [noise_alert]

    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_noise_alerts)
    noise_out = await whale_accumulation_distribution_intelligence(symbol="BTC", params={})
    assert noise_out["whale_alert_qualification"]["alert_worthy_count"] == 0
    assert noise_out["adaptive_disclosure"]["level_1"]["answer_state"] == "NO_QUALIFYING_ALERT"
    assert noise_out["whale_alert_disclosure"]["movement_presence_not_sufficient"] is True

    async def fake_signal_alerts(limit=20):
        return [signal_alert]

    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_signal_alerts)
    signal_out = await whale_accumulation_distribution_intelligence(symbol="BTC", params={})
    assert signal_out["whale_alert_qualification"]["alert_worthy_count"] == 1
    assert signal_out["adaptive_disclosure"]["level_1"]["answer_state"] == "ALERT_WORTHY"


@pytest.mark.asyncio
async def test_capability_19_inter_entity_internal_flow_runtime_filter(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_ctx():
        return {"flows": [{"entity": "a", "entity_b": "b", "amount_usd": 1e6}]}

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_ctx)

    def _classify_internal(**kw):
        return {"classification": "INTERNAL_CONFIRMED", "confidence": 0.95}

    def _classify_economic(**kw):
        return {"classification": "ECONOMIC_FLOW", "confidence": 0.95}

    monkeypatch.setattr("exchange_internal_flow_filter.classify_flow", _classify_internal)
    internal_out = await inter_entity_flow_intelligence(symbol="BTC", params={})
    monkeypatch.setattr("exchange_internal_flow_filter.classify_flow", _classify_economic)
    economic_out = await inter_entity_flow_intelligence(symbol="BTC", params={})

    assert internal_out["inter_entity_flow_filter"]["inter_entity_eligible_count"] == 0
    assert economic_out["inter_entity_flow_filter"]["inter_entity_eligible_count"] == 1
    assert internal_out["adaptive_disclosure"]["level_1"]["answer_state"] == "INTERNAL_EXCLUDED"
    assert economic_out["adaptive_disclosure"]["level_1"]["answer_state"] == "INTER_ENTITY_ELIGIBLE"
    assert internal_out["inter_entity_flow_disclosure"]["runtime_filter_applied"] is True


@pytest.mark.asyncio
async def test_capability_53_unapproved_input_cannot_change_verdict(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_search(address, chain="ethereum"):
        return {"ok": True, "entity_label": "clean", "data_state": "LIVE", "total_usd": 1000}

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_search)
    monkeypatch.setattr(
        "bd_platform.whales_institutional_layer.analyze_wallet_surveillance_79",
        lambda wallet: {"surveillance_detected": False},
    )

    baseline = await instant_wallet_due_diligence(symbol="BTC", params={"address": "0x1"})
    with_probe = await instant_wallet_due_diligence(
        symbol="BTC",
        params={
            "address": "0x1",
            "unapproved_risk_probe": {"risk_flags": ["synthetic_unapproved_critical"]},
        },
    )

    assert baseline["due_diligence"]["verdict"] == "clear"
    assert with_probe["due_diligence"]["verdict"] == "clear"
    assert "synthetic_unapproved_critical" in with_probe["due_diligence"]["unapproved_observable_only"]["risk_flags"]
    assert "synthetic_unapproved_critical" not in with_probe["due_diligence"]["risk_flags"]


@pytest.mark.asyncio
async def test_capability_54_unapproved_financial_model_cannot_change_verdict(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_holders(symbol):
        return {"available": True, "metrics": {"locked_supply_pct": 10}}

    async def fake_models_ok(symbol, notional=10000):
        return {"ok": True}

    async def fake_models_error(symbol, notional=10000):
        return {"error": "model_unavailable"}

    monkeypatch.setattr("launch57.smart_money_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.free_integrations.holder_analytics", fake_holders)

    monkeypatch.setattr("research_lab.compute_financial_models", fake_models_ok)
    baseline = await instant_token_due_diligence(symbol="BTC", params={})

    monkeypatch.setattr("research_lab.compute_financial_models", fake_models_error)
    with_error = await instant_token_due_diligence(symbol="BTC", params={})

    assert baseline["token_due_diligence"]["verdict"] == "clear"
    assert with_error["token_due_diligence"]["verdict"] == "clear"
    assert "financial_model_gap" in with_error["token_due_diligence"]["unapproved_observable_only"]["risk_flags"]
    assert "financial_model_gap" not in with_error["token_due_diligence"]["risk_flags"]
