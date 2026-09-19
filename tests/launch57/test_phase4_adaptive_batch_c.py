"""Launch-57 Phase 4 Adaptive Batch C — builder verification tests (#55→#56→#57)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.smart_money_batch3 import (
    exchange_transparency_risk_indicators,
    pump_dump_manipulation_alerts,
    suspicious_activity_flags,
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
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices"},
    }


@pytest.mark.asyncio
async def test_capability_55_manipulation_requires_pattern_evidence(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_alerts(limit=15):
        return [{"symbol": "BTC", "amount_usd": 5_000_000, "direction": "in"}]

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr("whale_tracker.get_latest_whale_alerts", fake_alerts)

    noise_out = await pump_dump_manipulation_alerts(
        symbol="BTC",
        params={"text": "BTC steady volume with normal market activity"},
    )
    signal_out = await pump_dump_manipulation_alerts(
        symbol="BTC",
        params={"text": "guaranteed 100x pump to the moon gem alert"},
    )

    assert noise_out["pump_dump_detection"]["pattern_alert_fired"] is False
    assert signal_out["pump_dump_detection"]["pattern_alert_fired"] is True
    assert noise_out["adaptive_disclosure"]["level_1"]["answer_state"] == "NO_QUALIFYING_PATTERN"
    assert signal_out["adaptive_disclosure"]["level_1"]["answer_state"] == "MANIPULATION_ALERT"
    assert signal_out["manipulation_alert_disclosure"]["no_legal_or_criminal_conclusion"] is True


@pytest.mark.asyncio
async def test_capability_56_weak_evidence_not_promoted(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.derivatives_onchain_intelligence_layer.fraud_suspicious_activity_297",
        lambda seed=None: {
            "flags": [
                {"type": "ambiguous_signal", "severity": "low", "confidence": 0.2},
                {"type": "mixer_proximity", "severity": "high", "confidence": 0.71},
            ]
        },
    )

    out = await suspicious_activity_flags(symbol="BTC", params={})
    assert out["launch_item_id"] == 56
    assert len(out["suspicious_activity_flags"]) == 1
    assert out["suspicious_activity_observable"]
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "SUSPICION_FLAGGED"
    assert out["suspicious_activity_disclosure"]["no_criminal_or_legal_conclusion"] is True
    assert out["suspicious_activity_disclosure"]["no_aml_classification_assertion"] is True


@pytest.mark.asyncio
async def test_capability_56_insufficient_evidence_when_all_weak(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.derivatives_onchain_intelligence_layer.fraud_suspicious_activity_297",
        lambda seed=None: {"flags": [{"type": "ambiguous_signal", "severity": "low", "confidence": 0.15}]},
    )
    out = await suspicious_activity_flags(symbol="BTC", params={})
    assert out["success"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.asyncio
async def test_capability_57_no_solvency_certification_from_health_score(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.smart_money_batch3.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.institutional_b2b_layer.build_exchange_health_with_counterparty_92",
        lambda exchange="binance", withdrawal_latency_hours=12.0, seed=None: {
            "exchange": exchange,
            "health_score": 9.9,
            "counterparty_risk": {
                "withdrawal_latency_status": "green",
                "abnormal_flow_pattern": True,
                "reserve_transparency_score": 9.5,
            },
            "alert_trigger": {"fired": True, "reason": "counterparty_threshold_exceeded"},
        },
    )
    out = await exchange_transparency_risk_indicators(symbol="BTC", params={"exchange": "binance"})
    indicators = out["exchange_risk_indicators"]
    guard = out["exchange_transparency_guard"]
    disc = out["exchange_transparency_disclosure"]

    assert out["launch_item_id"] == 57
    assert indicators["solvency_certificate_claim"] == "FORBIDDEN"
    assert indicators["decision_driving_solvency_assurance"] is False
    assert guard["conflicting_evidence_visible"] is True
    assert disc["transparency_risk_indicators_only"] is True
    assert disc["decision_driving_solvency_assurance"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "RISK_INDICATORS_ONLY"
