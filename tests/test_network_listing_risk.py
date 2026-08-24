"""Tests — Network Widget (#120), Large Liquidity (#121), Listing Intelligence (#122+#114), Withdrawal Closure (#123)."""

from __future__ import annotations

import pytest

from bd_platform.large_liquidity_event_alert import (
    build_analysis,
    classify_sell_type,
)
from bd_platform.listing_intelligence_engine import _build_timelines
from bd_platform.transfer_network_utility import (
    _build_widget_summary,
    _short_network_label,
    set_user_network_preference,
    get_user_network_preference,
)
from bd_platform.withdrawal_closure_alert import (
    classify_closure,
    record_withdrawal_closure,
    scan_withdrawal_closures,
)


def test_short_network_labels():
    assert _short_network_label("erc20") == "ERC20"
    assert _short_network_label("bep20") == "BEP20"


def test_widget_summary_format():
    recs = [
        {"network_id": "erc20", "fee_usd": 5.0},
        {"network_id": "trc20", "fee_usd": 0.5},
        {"network_id": "bep20", "fee_usd": 0.1},
    ]
    summary = _build_widget_summary(recs)
    assert "ERC20 ($5.0 gas)" in summary
    assert "TRC20 ($0.5 gas)" in summary
    assert "BEP20 ($0.1 gas)" in summary
    assert "Cheapest: BEP20" in summary


@pytest.mark.asyncio
async def test_transfer_deposit_widget():
    from bd_platform.transfer_network_utility import transfer_deposit_widget

    result = await transfer_deposit_widget("USDT", amount_usd=1000, surface="deposit")
    assert result["ok"] is True
    assert result["feature"] == "#120"
    assert result["sla_met"] is True
    assert "widget" in result
    assert "Cheapest:" in result["widget"]["summary"]
    assert "#108" in result["widget"]["integrated_features"]
    assert "summary_ar" in result["widget"]
    assert "الأرخص" in result["widget"]["summary_ar"]


def test_user_network_pref_in_widget(tmp_path, monkeypatch):
    prefs = tmp_path / "prefs.json"
    monkeypatch.setattr("bd_platform.transfer_network_utility._PREFS_PATH", prefs)
    set_user_network_preference("u1", "USDT", "bep20")
    pref = get_user_network_preference("u1", "USDT")
    assert pref["network_id"] == "bep20"


def test_classify_sell_type_cascade():
    st = classify_sell_type(drop_pct=15, volume_spike=5, funding_rate=0)
    assert st == "stop_loss_cascade"
    analysis = build_analysis(st, drop_pct=15)
    assert "cascade" in analysis.lower()
    assert "buy" not in analysis.lower() or "rebound" in analysis.lower()


def test_listing_timeline_builder():
    events = [
        {"symbol": "NEW", "exchange": "binance", "signal": "deposit_opened", "timeline_stage": 1, "headline": "a"},
        {"symbol": "NEW", "exchange": "binance", "signal": "listing_announced", "timeline_stage": 2, "headline": "b"},
    ]
    timelines = _build_timelines(events)
    assert len(timelines) == 1
    assert "Deposit Opened" in timelines[0]["timeline"]
    assert "Listing Announced" in timelines[0]["timeline"]


def test_classify_closure_maintenance_vs_danger():
    maint = classify_closure(
        exchange_id="binance",
        asset="TOKEN",
        withdrawal_score=50,
        health_score=80,
        badge="ok",
        duration_minutes=30,
    )
    assert maint["classification"] == "likely_maintenance"

    danger = classify_closure(
        exchange_id="ftx",
        asset="FTT",
        withdrawal_score=10,
        health_score=25,
        badge="fraud",
    )
    assert danger["classification"] == "dangerous_closure"
    assert danger["alert_level"] == "critical"


def test_record_withdrawal_closure(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.withdrawal_closure_alert._KNOWN_PATH", tmp_path / "known.json")
    monkeypatch.setattr("bd_platform.withdrawal_closure_alert._SNAPSHOT_PATH", tmp_path / "snap.jsonl")
    monkeypatch.setattr("bd_platform.withdrawal_closure_alert._ALERTS_PATH", tmp_path / "alerts.jsonl")

    result = record_withdrawal_closure(
        exchange_id="binance",
        asset="XYZ",
        withdrawal_score=15,
        health_score=35,
        badge="caution",
    )
    assert result["ok"] is True
    assert result["feature_id"] == 123
    assert result["sla_met"] is True
    assert result["portfolio_risk"]["feature"] == "#109"
    assert "buy" not in result["headline"].lower()


def test_scan_withdrawal_closures_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.withdrawal_closure_alert._ALERTS_PATH", tmp_path / "missing.jsonl")
    monkeypatch.setattr("bd_platform.withdrawal_closure_alert._CACHE_PATH", tmp_path / "cache.json")
    out = scan_withdrawal_closures()
    assert out["ok"] is True
    assert out["feature_id"] == 123
    assert out["sla_met"] is True
