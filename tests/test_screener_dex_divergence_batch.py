"""Tests — #533 Custom Market Data Screener, #535 DEX Intelligence, #537 Dev-Market Divergence."""

from __future__ import annotations

import json

import pytest

from bd_platform import custom_market_data_screener as cmds
from bd_platform import dev_market_divergence_detector as dmdd
from bd_platform import dex_intelligence_layer as dil


# --- #533 fixtures ---

@pytest.fixture
def screener_seed(tmp_path, monkeypatch):
    p = tmp_path / "custom_market_data_screener_seed.json"
    p.write_text(json.dumps({
        "assets": [
            {"symbol": "BTC", "risk_score": 25, "whale_activity_score": 72, "onchain_signal": 0.65,
             "funding_rate": -0.0002, "sentiment_score": 0.55, "rsi_14": 58},
            {"symbol": "SOL", "risk_score": 55, "whale_activity_score": 40, "onchain_signal": 0.35,
             "funding_rate": 0.0008, "sentiment_score": 0.30, "rsi_14": 72},
        ],
        "saved_screeners": {
            "test_screener": {
                "name": "Test",
                "filters": {"whale_activity_min": {"min": 70}, "risk_score_max": {"max": 40}},
                "alert_enabled": True,
            },
        },
        "delivery_log": [],
    }), encoding="utf-8")
    monkeypatch.setattr(cmds, "_SEED_PATH", p)
    return p


# --- #535 fixtures ---

@pytest.fixture
def dex_seed(tmp_path, monkeypatch):
    p = tmp_path / "dex_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "reorg_handling": {"enabled": True, "confirmation_blocks": 12},
        "pools": [
            {"pool_id": "good", "token_symbol": "ETH", "chain": "ethereum", "dex": "uniswap_v3",
             "liquidity_usd": 1000000, "volume_24h_usd": 500000, "identity_verified": True,
             "token_metadata_verified": True, "scam_flag": False, "spam_flag": False,
             "honeypot_risk": False, "pool_health": "healthy", "reorg_confirmed": True},
            {"pool_id": "scam", "token_symbol": "SCAM", "chain": "ethereum", "dex": "unknown",
             "liquidity_usd": 50000, "identity_verified": False, "scam_flag": True,
             "honeypot_risk": True, "pool_health": "critical"},
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(dil, "_SEED_PATH", p)
    return p


# --- #537 fixtures ---

@pytest.fixture
def divergence_seed(tmp_path, monkeypatch):
    p = tmp_path / "dev_market_divergence_detector_seed.json"
    p.write_text(json.dumps({
        "projects": {
            "uniswap": {
                "name": "Uniswap", "dev_commits_90d": 245, "contributors_90d": 18,
                "dev_activity_trend": 0.35, "price_trend_90d": -0.15, "social_trend_90d": -0.20,
                "onchain_usage_trend_90d": 0.10, "divergence_persistence_days": 21,
                "backtest": {"historical_divergence_count": 4, "mean_reversion_rate": 0.45,
                             "false_positive_rate": 0.30, "window": "90D"},
            },
            "low_activity": {
                "name": "LowActivity", "dev_commits_90d": 2, "contributors_90d": 1,
                "dev_activity_trend": 0.0, "price_trend_90d": 0.5, "social_trend_90d": 0.3,
                "onchain_usage_trend_90d": 0.0, "divergence_persistence_days": 0,
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dmdd, "_SEED_PATH", p)
    return p


# --- #533 tests ---

def test_533_renamed_no_ai_ranking(screener_seed):
    status = cmds.custom_market_data_screener_status()
    assert status["renamed_from"] == "Custom Intelligence Screener"
    assert status["no_ai_ranking"] is True
    assert status["user_controlled"] is True


def test_533_explain_each_match(screener_seed):
    seed = json.loads(screener_seed.read_text(encoding="utf-8"))
    asset = seed["assets"][0]
    explanation = cmds.explain_match(asset, {"whale_activity_min": {"min": 70}})
    assert explanation["explain_each_match"] is True
    assert any("Matched because" in e["display"] for e in explanation["explanations"])


def test_533_user_controlled_no_opportunity(screener_seed):
    result = cmds.run_screener({"whale_activity_min": {"min": 70}, "risk_score_max": {"max": 40}})
    assert result["not_opportunities_language"] is True
    assert result["no_ai_ranking"] is True
    assert result["assets_matching_criteria"] == 1
    assert result["results"][0]["match_explanation"]["all_criteria_met"] is True


def test_533_save_and_alert_backend(screener_seed):
    result = cmds.run_screener(saved_screener_id="test_screener")
    assert result["save_and_alert_supported"] is True
    assert result["backend_enforced"] is True
    assert result["alert_rate_limit"]["backend_enforced"] is True


# --- #535 tests ---

def test_535_dex_layer_not_standalone(dex_seed):
    status = dil.dex_intelligence_layer_status()
    assert status["standalone_rejected"] is True
    assert status["renamed_from"] == "DEX_Liquidity_Listener"


def test_535_scam_spam_filters(dex_seed):
    seed = json.loads(dex_seed.read_text(encoding="utf-8"))
    filtered, meta = dil.apply_scam_spam_filters(seed["pools"])
    assert meta["scam_spam_filters_applied"] is True
    assert meta["filtered_count"] == 1
    assert len(filtered) == 1
    assert meta["no_rug_pull_opportunities"] is True


def test_535_pool_identity_verified(dex_seed):
    seed = json.loads(dex_seed.read_text(encoding="utf-8"))
    pool = seed["pools"][0]
    identity = dil.verify_pool_identity(pool)
    assert identity["identity_verified"] is True


def test_535_multi_pool_aggregation(dex_seed):
    panel = dil.build_dex_intelligence_panel(token_symbol="ETH")
    assert panel["aggregation"]["multi_pool_aggregation"] is True
    assert panel["reorg_handling"]["reorg_handling"] is True


def test_535_reconciliation_tests(dex_seed):
    tests = dil.run_reconciliation_tests()
    assert tests["all_passed"] is True


# --- #537 tests ---

def test_537_no_causal_claim(divergence_seed):
    seed = json.loads(divergence_seed.read_text(encoding="utf-8"))
    div = dmdd.detect_divergence(seed["projects"]["uniswap"])
    assert div["no_causal_claim"] is True
    assert div["not_prediction"] is True
    assert div["not_value_signal"] is True
    assert "diverged" in div["observation"].lower()


def test_537_windows_documented(divergence_seed):
    windows = dmdd.build_windows_block()
    assert windows["windows_documented"] is True
    assert windows["rolling_window_days"] == 90


def test_537_sparse_data_handling(divergence_seed):
    seed = json.loads(divergence_seed.read_text(encoding="utf-8"))
    div = dmdd.detect_divergence(seed["projects"]["low_activity"])
    assert div["divergence_type"] == "insufficient_data"
    assert div["sparse_data"]["insufficient_data"] is True


def test_537_backtest(divergence_seed):
    seed = json.loads(divergence_seed.read_text(encoding="utf-8"))
    backtest = dmdd.build_backtest_summary(seed["projects"]["uniswap"])
    assert backtest["backtest_available"] is True
    assert backtest["no_causal_claim_in_backtest"] is True


def test_537_divergence_panel(divergence_seed):
    panel = dmdd.build_divergence_panel("uniswap")
    assert panel["ok"] is True
    assert panel["divergence"]["divergence_detected"] is True
    assert panel["acceptance_criteria"]["descriptive_only"] is True


def test_537_qa_tests(divergence_seed):
    tests = dmdd.run_divergence_qa_tests()
    assert tests["all_passed"] is True


def test_api_routes(screener_seed, dex_seed, divergence_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-data-screener/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-data-screener?whale_activity_min=70").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/dex-intelligence/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/dex-intelligence").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/dev-market-divergence/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/dev-market-divergence?project_id=uniswap").status_code == 200
