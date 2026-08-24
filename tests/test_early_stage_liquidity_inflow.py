"""Tests — Early Stage Token Scanner (#115) + Liquidity Inflow Alert (#116)."""

from __future__ import annotations

import pytest

from bd_platform.smart_contract_scanner import scan_contract_from_pair
from bd_platform.early_stage_token_scanner import (
    _contract_verified,
    _evaluate_pair,
    _holder_distribution_healthy,
    _liquidity_lock_proxy,
)
from bd_platform.liquidity_inflow_alert import compute_confidence_score, _analyze_pair


def _sample_pair(**overrides) -> dict:
    base = {
        "chainId": "ethereum",
        "dexId": "uniswap",
        "pairAddress": "0xabc",
        "marketCap": 5_000_000,
        "fdv": 5_000_000,
        "liquidity": {"usd": 250_000},
        "labels": ["verified"],
        "info": {"imageUrl": "x"},
        "pairCreatedAt": 1700000000000,
        "baseToken": {"symbol": "TEST", "address": "0x1234"},
        "txns": {"h24": {"buys": 500, "sells": 400}},
        "url": "https://dexscreener.com",
    }
    base.update(overrides)
    return base


def test_contract_scanner_verified():
    out = scan_contract_from_pair(_sample_pair())
    assert out["ok"] is True
    assert out["feature_id"] == 193
    assert out["contract_verified"] is True
    assert out["sla_met"] is True


def test_contract_scanner_malicious_label():
    out = scan_contract_from_pair(_sample_pair(labels=["honeypot"]))
    assert out["risk_level"] == "critical"
    assert any("critical" in r.get("level", "") for r in out["risks"])


def test_holder_distribution_healthy():
    ok, reason = _holder_distribution_healthy(_sample_pair())
    assert ok is True
    assert reason == "balanced_flow"


def test_liquidity_lock_proxy_label():
    ok, reason = _liquidity_lock_proxy(_sample_pair(labels=["verified", "locked"]))
    assert ok is True
    assert "lock" in reason


def test_evaluate_pair_passes_filters():
    row = _evaluate_pair(_sample_pair())
    assert row is not None
    assert row["filters_pass_count"] >= 3
    assert row["mode"] == "filter_only"
    assert "security_scan" in row


def test_evaluate_pair_rejects_high_mcap():
    assert _evaluate_pair(_sample_pair(marketCap=50_000_000)) is None


def test_confidence_score_three_signals():
    signals = [
        {"code": "A", "fired": True, "strength": 2.0},
        {"code": "B", "fired": True, "strength": 1.5},
        {"code": "C", "fired": True, "strength": 1.0},
    ]
    conf = compute_confidence_score(signals)
    assert conf["feature_id"] == 149
    assert conf["score"] >= 75
    assert conf["label"] == "high"


def test_liquidity_inflow_volume_spike(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.liquidity_inflow_alert._SNAPSHOT_PATH", tmp_path / "snap.jsonl")
    monkeypatch.setattr("bd_platform.liquidity_inflow_alert._ALERTS_PATH", tmp_path / "alerts.jsonl")

    pair = _sample_pair(
        volume={"h1": 300_000, "h6": 100_000, "h24": 500_000},
        txns={"h1": {"buys": 150, "sells": 20}, "h24": {"buys": 500, "sells": 400}},
    )
    alert = _analyze_pair(pair)
    assert alert is not None
    assert alert["event_type"] == "liquidity_inflow"
    assert alert["signals_fired_count"] >= 1
    assert alert["confidence_score"]["score"] > 0
    assert "Liquidity Inflow Alert" in alert["headline"]
    assert alert["mode"] == "alert_only"


@pytest.mark.asyncio
async def test_early_stage_scanner_mock(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.early_stage_token_scanner._CACHE_PATH", tmp_path / "cache.json")

    async def fake_pairs(session, query="USDT"):
        return [_sample_pair()]

    monkeypatch.setattr("bd_platform.early_stage_token_scanner._fetch_pairs", fake_pairs)

    from bd_platform.early_stage_token_scanner import scan_early_stage_tokens

    out = await scan_early_stage_tokens(limit=5)
    assert out["ok"] is True
    assert out["feature_id"] == 115
    assert out["product_name"] == "Early Stage Token Scanner"
    assert "not investment" in out["disclaimer"].lower()
    assert out["mode"] == "filter_only"
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_liquidity_inflow_scan_mock(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.liquidity_inflow_alert._CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr("bd_platform.liquidity_inflow_alert._SNAPSHOT_PATH", tmp_path / "snap.jsonl")
    monkeypatch.setattr("bd_platform.liquidity_inflow_alert._ALERTS_PATH", tmp_path / "alerts.jsonl")

    spike_pair = _sample_pair(
        volume={"h1": 500_000, "h6": 50_000, "h24": 200_000},
        txns={"h1": {"buys": 200, "sells": 10}, "h24": {"buys": 500, "sells": 400}},
    )

    async def fake_trending(session):
        return [spike_pair]

    monkeypatch.setattr("bd_platform.liquidity_inflow_alert._fetch_trending_pairs", fake_trending)

    from bd_platform.liquidity_inflow_alert import scan_liquidity_inflow

    out = await scan_liquidity_inflow(limit=5)
    assert out["ok"] is True
    assert out["feature_id"] == 116
    assert out["product_name"] == "Liquidity Inflow Alert"
    assert out["mode"] == "alert_only"
    assert "opportunity" not in out["disclaimer"].lower() or "not" in out["disclaimer"].lower()
    assert out["sla_met"] is True
