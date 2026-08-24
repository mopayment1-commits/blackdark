"""Tests — Listing Opportunity (#129), Fee Database (#130), Unusual Liquidity (#131)."""

from __future__ import annotations

import pytest

from bd_platform.fee_database_service import (
    calculate_transaction_cost,
    fee_database_status,
    lookup_fee_matrix,
)
from bd_platform.listing_intelligence_engine import analyze_listing_opportunity
from bd_platform.unusual_liquidity_alert_engine import (
    classify_severity,
    scan_unusual_liquidity_events,
)


def test_listing_opportunity_low_liquidity_format():
    event = {
        "signal": "first_trade",
        "symbol": "NEW",
        "exchange": "uniswap",
        "liquidity_usd": 50_000,
        "opening_price_usd": 0.01,
    }
    out = analyze_listing_opportunity(event)
    assert out["feature_id"] == 129
    assert out["risk_level"] == "high_slippage"
    assert "$0.0100" in out["headline"]
    assert "$50K" in out["headline"]
    assert "Low liquidity" in out["analysis"]
    assert "Wait 24 hours" in out["recommendation"]
    assert "تم الإدراج" in out["headline_ar"]
    assert "سيولة منخفضة" in out["analysis_ar"]
    assert "انتظر 24 ساعة" in out["recommendation_ar"]
    assert out["no_profit_promises"] is True
    assert "profit" not in out["recommendation"].lower()


def test_listing_opportunity_deposit_opened_pre_listing():
    event = {"signal": "deposit_opened", "symbol": "TOKEN", "exchange": "binance"}
    out = analyze_listing_opportunity(event)
    assert out["risk_level"] == "pre_listing"
    assert "not live" in out["analysis"].lower() or "Pre-listing" in out["analysis"]


def test_fee_database_status_internal_service():
    status = fee_database_status()
    assert status["ok"] is True
    assert status["feature_id"] == 130
    assert status["user_facing"] is False
    assert status["coverage"]["trading_fees"] is True
    assert status["coverage"]["hidden_spread"] is True


def test_fee_matrix_lookup_known_exchange():
    row = lookup_fee_matrix("binance", symbol="BTC/USDT")
    assert row["ok"] is True
    assert row["taker"] is not None
    assert row["maker"] is not None


@pytest.mark.asyncio
async def test_transaction_cost_breakdown(monkeypatch):
    async def fake_spread(exchange_id: str, symbol: str) -> float:
        return 10.0

    monkeypatch.setattr("bd_platform.fee_database_service._estimate_spread_bps", fake_spread)
    out = await calculate_transaction_cost("binance", "BTC/USDT", 1000.0)
    assert out["ok"] is True
    assert out["user_facing"] is False
    assert out["sla_met"] is True
    assert out["total_cost_usd"] > 0
    assert "fees" in out["display"]
    assert "spread" in out["display"]
    assert "رسوم" in out["display_ar"]
    assert out["accuracy_estimate"] >= 0.99


def test_unusual_liquidity_severity_critical():
    severity, emoji, label = classify_severity(change_pct=75.0, direction="withdraw")
    assert severity == "critical"
    assert emoji == "🔴"
    assert "70%" in label


def test_unusual_liquidity_severity_warning():
    severity, emoji, label = classify_severity(change_pct=35.0, direction="withdraw")
    assert severity == "warning"
    assert emoji == "🟡"
    assert "Unusual" in label


@pytest.mark.asyncio
async def test_scan_unusual_liquidity_empty_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._SNAPSHOT_PATH", tmp_path / "snap.json")
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._ALERTS_PATH", tmp_path / "alerts.jsonl")

    async def fake_dex(session, limit=15):
        return []

    async def fake_cex(session):
        return []

    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._scan_dex_liquidity_changes", fake_dex)
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._scan_cex_depth_changes", fake_cex)

    out = await scan_unusual_liquidity_events(limit=5)
    assert out["ok"] is True
    assert out["feature_id"] == 131
    assert out["sla_met"] is True
    assert out["mode"] == "alert_only"
    assert "🟡" in out["severity_levels"]["warning"]


@pytest.mark.asyncio
async def test_scan_unusual_liquidity_dex_alert(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._ALERTS_PATH", tmp_path / "alerts.jsonl")
    monkeypatch.setattr(
        "bd_platform.unusual_liquidity_alert_engine._load_snapshots",
        lambda: {"ethereum:uniswap:TEST:0xabc": 1_000_000.0},
    )
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._save_snapshots", lambda data: None)

    async def fake_dex(session, limit=15):
        return [
            {
                "event_type": "unusual_liquidity_movement",
                "feature_id": 131,
                "severity": "critical",
                "severity_emoji": "🔴",
                "symbol": "TEST",
                "change_pct": 80.0,
                "headline": "🔴 rug pull warning",
                "headline_ar": "🔴 70% من السيولة سُحبت",
                "mode": "alert_only",
                "timestamp": "2026-08-24T00:00:00+00:00",
            }
        ]

    async def fake_cex(session):
        return []

    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._scan_dex_liquidity_changes", fake_dex)
    monkeypatch.setattr("bd_platform.unusual_liquidity_alert_engine._scan_cex_depth_changes", fake_cex)

    out = await scan_unusual_liquidity_events(limit=5)
    assert out["alert_count"] == 1
    assert out["events"][0]["severity"] == "critical"
