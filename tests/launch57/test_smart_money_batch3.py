"""Launch-57 Phase 4 Smart Money Batch 3 — pump/dump, mini AML, exchange caution."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.smart_money_batch3 import (
    LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS,
    exchange_transparency_risk_indicators,
    execute_launch57_smart_money_batch3,
    pump_dump_manipulation_alerts,
    suspicious_activity_flags,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_pump_dump_detects_phrases(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_alerts(limit=15):
        return []

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_alerts)
    out = await pump_dump_manipulation_alerts(
        symbol="BTC",
        params={"text": "guaranteed 100x pump to the moon gem alert"},
    )
    assert out["launch_item_id"] == 55
    assert out["pump_dump_detection"]["pattern_alert_fired"] is True


@pytest.mark.asyncio
async def test_suspicious_flags_mini_aml_not_full_platform(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.derivatives_onchain_intelligence_layer.fraud_suspicious_activity_297",
        lambda seed=None: {"flags": [{"type": "wash_trading_pattern"}]},
    )
    out = await suspicious_activity_flags(symbol="BTC", params={})
    assert out["launch_item_id"] == 56
    assert out["mini_aml_scope"]["full_aml_platform"] is False
    assert out["full_aml_platform"] is False


@pytest.mark.asyncio
async def test_exchange_transparency_forbids_solvency_claim(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.institutional_b2b_layer.build_exchange_health_with_counterparty_92",
        lambda exchange="binance", withdrawal_latency_hours=12.0, seed=None: {
            "exchange": exchange,
            "health_score": 7.5,
            "counterparty_risk": {"withdrawal_latency_status": "green", "abnormal_flow_pattern": False},
        },
    )
    out = await exchange_transparency_risk_indicators(symbol="BTC", params={"exchange": "binance"})
    assert out["launch_item_id"] == 57
    assert out["exchange_risk_indicators"]["solvency_certificate_claim"] == "FORBIDDEN"
    assert out["exchange_risk_indicators"]["reserve_guarantee_claim"] == "FORBIDDEN"
    assert out["exchange_risk_indicators"]["indicators_only"] is True


@pytest.mark.asyncio
async def test_kill_switch_batch3(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_batch3")

    import launch57.smart_money_batch3 as mod

    monkeypatch.setattr(mod, "pump_dump_manipulation_alerts", broken)
    with pytest.raises(RuntimeError, match="kill_switch_batch3"):
        await execute_launch57_smart_money_batch3(238, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch3_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_alerts(limit=15):
        return []

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_alerts)
    monkeypatch.setattr(
        "bd_platform.derivatives_onchain_intelligence_layer.fraud_suspicious_activity_297",
        lambda seed=None: {"flags": [{"type": "mixer_proximity"}]},
    )
    monkeypatch.setattr(
        "bd_platform.institutional_b2b_layer.build_exchange_health_with_counterparty_92",
        lambda exchange="binance", withdrawal_latency_hours=12.0, seed=None: {
            "exchange": exchange,
            "counterparty_risk": {},
        },
    )
    for cap_id in LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS:
        out = await execute_launch57_smart_money_batch3(cap_id, params={"symbol": "BTC"})
        assert out["binding_source"] == "launch57_phase4_smart_money_batch3"
