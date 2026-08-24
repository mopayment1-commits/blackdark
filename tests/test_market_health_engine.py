"""Tests — Market Health Dashboard (#151)."""

from __future__ import annotations

import pytest

from bd_platform.market_health_engine import (
    _pillar_liquidity,
    _pillar_macro,
    _pillar_onchain,
    _pillar_sentiment,
    _portfolio_risk_hook_109,
    _score_to_status,
    build_market_health_dashboard,
    market_health_status,
)


def test_score_to_status_bands():
    assert _score_to_status(75) == "healthy"
    assert _score_to_status(55) == "cautious"
    assert _score_to_status(30) == "unhealthy"


def test_pillar_onchain_healthy():
    p = _pillar_onchain(
        {"n_transactions": 300_000, "hash_rate": 500_000_000},
        {"total_tvl_usd": 80_000_000_000},
    )
    assert p["pillar"] == "on_chain_health"
    assert p["status"] == "healthy"
    assert p["emoji"] == "🟢"


def test_pillar_sentiment_extreme_unhealthy():
    p = _pillar_sentiment({"value": 90, "label": "Extreme Greed"})
    assert p["status"] == "unhealthy"
    assert p["emoji"] == "🔴"
    assert "Extreme Greed" in p["reason"]


def test_pillar_liquidity_with_outliers():
    p = _pillar_liquidity(
        {
            "source_metadata": {"connectors_ok": 6},
            "outlier_count": 2,
            "validation": {"price_verified": True},
        },
        {"total_tvl_usd": 50_000_000_000},
    )
    assert p["pillar"] == "liquidity_health"
    assert "outlier" in p["reason"].lower()


def test_pillar_macro_risk_off():
    p = _pillar_macro({"macro_regime": "Risk-Off", "overall_expected_impact": "negative", "relationships": []})
    assert p["status"] == "unhealthy"
    assert "headwind" in p["reason"].lower() or "risk-off" in p["reason"].lower()


def test_portfolio_risk_hook_109_unhealthy():
    hook = _portfolio_risk_hook_109("unhealthy", 35.0, asset="BTC")
    assert hook["feature"] == "#109"
    assert hook["recommended_action"] == "reduce_exposure"
    assert hook["urgency"] == "high"


def test_market_health_status():
    status = market_health_status()
    assert status["ok"] is True
    assert status["feature_id"] == 151
    assert len(status["pillars"]) == 4
    assert "#109" in status["integrated_with"]


@pytest.mark.asyncio
async def test_build_market_health_dashboard_mocked(monkeypatch):
    async def fake_chain():
        return {"n_transactions": 280_000, "hash_rate": 400_000_000}

    async def fake_tvl():
        return {"total_tvl_usd": 70_000_000_000, "chain_count": 50}

    async def fake_fg():
        return {"value": 52, "label": "Neutral"}

    async def fake_price(asset, use_cache=True):
        return {
            "ok": True,
            "source_metadata": {"connectors_ok": 7, "connectors_polled": 8},
            "outlier_count": 0,
            "validation": {"price_verified": True},
            "user_badge": "✓ Price Verified",
        }

    async def fake_macro(asset):
        return {
            "ok": True,
            "macro_regime": "Risk-On",
            "overall_expected_impact": "positive",
            "relationships": [{"relationship": "SPX rose 0.5% → historically BTC rises ~2.2% → expected impact: positive"}],
        }

    monkeypatch.setattr("bd_platform.market_health_engine._fetch_blockchain_stats", fake_chain)
    monkeypatch.setattr("bd_platform.market_health_engine._fetch_defillama_tvl", fake_tvl)
    monkeypatch.setattr("bd_platform.market_health_engine._fetch_fear_greed", fake_fg)
    monkeypatch.setattr("bd_platform.price_aggregation_engine.aggregate_prices", fake_price)
    monkeypatch.setattr("bd_platform.macro_context_engine.build_macro_relationships", fake_macro)
    monkeypatch.setattr("bd_platform.market_health_engine._SNAPSHOT_PATH", __import__("pathlib").Path("/tmp/mh_test.jsonl"))
    monkeypatch.setattr("bd_platform.market_health_engine._CACHE", {})

    out = await build_market_health_dashboard("BTC")
    assert out["ok"] is True
    assert out["feature_id"] == 151
    assert out["pillar_count"] == 4
    assert out["overall_status"] in {"healthy", "cautious", "unhealthy"}
    assert out["overall_emoji"] in {"🟢", "🟡", "🔴"}
    assert out["classification_reason"]
    assert out["portfolio_risk_109"]["feature"] == "#109"
    assert out["sla_met"] is True
    assert out["price_verified_badge"] == "✓ Price Verified"
