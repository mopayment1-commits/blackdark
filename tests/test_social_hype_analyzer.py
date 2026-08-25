"""Tests — #293 Social Hype Analyzer (replaces #758)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bd_platform import social_hype_analyzer as sha


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "social_hype_analyzer_seed.json"
    seed.write_text(
        json.dumps({
            "analyzer_version": "2.1",
            "baseline_method": "Rolling Median",
            "burst_threshold_sigma": 3,
            "last_calibrated": "2026-08-25T00:00:00+00:00",
            "bot_filters": {"min_account_age_days": 30, "min_followers": 100},
            "alert_precision_history": {
                "total_alerts": 100,
                "true_positives": 82,
                "false_positives": 18,
                "precision_pct": 82.0,
                "display": "Alert History: 100 alerts | 82 True Positive | 18 False Positive | Precision: 82%",
            },
            "assets": {
                "BTC": {
                    "baseline_30d_avg_mentions": 12500,
                    "baseline_7d_avg_mentions": 13200,
                    "baseline_90d_avg_mentions": 11800,
                    "current_mentions": 72000,
                    "baseline_last_updated": "2026-08-25T13:00:00+00:00",
                    "engagement_quality_score": 8.2,
                    "bot_score_filtered_pct": 34.5,
                    "sources": {
                        "twitter": {"mentions": 45000, "baseline": 8200, "pct_change": 448.8, "available": True},
                        "reddit": {"mentions": 18000, "baseline": 3800, "pct_change": 373.7, "available": True},
                        "telegram": {"mentions": 6000, "baseline": 2800, "pct_change": 114.3, "available": True},
                        "discord": {"mentions": 2000, "baseline": 900, "pct_change": 122.2, "available": True},
                        "news": {"mentions": 1000, "baseline": 800, "pct_change": 25.0, "available": True},
                    },
                    "hype_spike_detected": True,
                    "confidence_pct": 87.0,
                },
                "ETH": {
                    "baseline_30d_avg_mentions": 8200,
                    "current_mentions": 9800,
                    "baseline_last_updated": "2026-08-25T13:00:00+00:00",
                    "engagement_quality_score": 7.1,
                    "bot_score_filtered_pct": 22.0,
                    "sources": {
                        "twitter": {"mentions": 4200, "baseline": 4000, "pct_change": 5.0, "available": True},
                        "reddit": {"mentions": 2800, "baseline": 2600, "pct_change": 7.7, "available": True},
                    },
                    "hype_spike_detected": False,
                    "confidence_pct": 42.0,
                },
            },
            "market_scan": {"affected_tokens": ["BTC"]},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(sha, "_SEED_PATH", seed)
    return seed


def test_historical_baseline(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    assert "30-day rolling average" in result["baseline"]["display"]
    assert "7D/30D/90D" in result["baseline"]["display"]
    assert "Last Updated:" in result["baseline"]["display"]


def test_bot_adjustment(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    bot = result["bot_adjustment"]["display"]
    assert "Bot Score:" in bot
    assert "Minimum Account Age: 30 days" in bot
    assert "Minimum Followers: 100" in bot
    assert "Engagement Quality:" in bot


def test_multi_source_confirmation(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    assert result["cross_source_confirmation"] == "Strong"
    assert result["sources_confirmed"] >= 3
    assert "Twitter:" in result["sources_display"]
    assert "Cross-Source Confirmation:" in result["sources_display"]


def test_alert_precision_transparent(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    prec = result["alert_precision"]
    assert prec["true_positives"] == 82
    assert prec["false_positives"] == 18
    assert prec["precision_pct"] == 82.0
    assert prec["errors_not_hidden"] is True
    assert "False Positive" in result["precision_display"]


def test_output_contract(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    assert result["hype_spike"] == "Detected"
    assert "BTC" in result["affected_tokens"]
    assert result["acceleration_pct"] > 0
    assert result["confidence_pct"] > 0
    assert "Sources Confirmed:" in result["sources_confirmed_display"]
    assert result["disclaimer_hideable"] is False


def test_three_reasons_per_alert(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    reasons = result["alert_reasons"]
    assert len(reasons) == 3
    assert "30D baseline" in reasons[0]["display"]
    assert "sources" in reasons[1]["display"].lower()
    assert "Engagement quality" in reasons[2]["display"]


def test_not_an_opportunity(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    assert result["not_an_opportunity"] is True
    assert result["not_buy_signal"] is True
    assert "Buy" not in result["analysis_display"]
    assert "Hype Spike Detected" in result["analysis_display"]
    assert "Bot-Filtered: Yes" in result["analysis_display"]


def test_no_hype_when_weak_confirmation(isolated_seed):
    result = sha.analyze_asset_hype("ETH")
    assert result["hype_spike"] == "None"


def test_version_documented(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    assert "Hype Analyzer v2.1" in result["version_display"]
    assert "Rolling Median" in result["version_display"]
    assert "3σ" in result["version_display"]


def test_no_look_ahead(isolated_seed):
    result = sha.analyze_asset_hype("BTC")
    assert result["no_look_ahead"] is True


def test_not_standalone(isolated_seed):
    status = sha.social_hype_analyzer_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 293
    assert status["replaces_feature_id"] == 758


def test_market_scan(isolated_seed):
    scan = sha.scan_market_hype()
    assert scan["hype_spike"] == "Detected"
    assert "BTC" in scan["affected_tokens"]
    assert scan["alert_count"] >= 1


@pytest.mark.asyncio
async def test_sentiment_panel_integration(isolated_seed, monkeypatch):
    async def fake_ctx(assets):
        return {"sentiment_compound_index": {"BTC": 0.2}}

    async def fake_classify(**kwargs):
        return {"headlines": []}

    monkeypatch.setattr("sentiment_engine.build_sentiment_context_safe", fake_ctx)
    monkeypatch.setattr("bd_platform.news_classifier.classify_headlines", fake_classify)
    monkeypatch.setattr("bd_platform.free_integrations.socialtickers_asset", AsyncMock(return_value=None))
    monkeypatch.setattr(
        "bd_platform.weighted_social_sentiment.analyze_weighted_social_sentiment",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "bd_platform.unique_social_volume.analyze_unique_social_volume",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr("market_context.fetch_binance_ticker", AsyncMock(return_value=None))
    monkeypatch.setattr(
        "bd_platform.positioning_intelligence.get_top_trader_positioning",
        lambda asset: {"ok": False},
    )

    from bd_platform.sentiment_intelligence import analyze_asset_sentiment

    result = await analyze_asset_sentiment("BTC")
    assert result.get("social_hype_analyzer") is not None
    assert 293 in [int(x.replace("#", "")) for x in result.get("integrated_features", []) if "#" in str(x)]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/sentiment/hype/status").status_code == 200
    status = c.get("/api/platform/market-radar/sentiment/hype/status").json()
    assert status["feature_id"] == 293
    assert status["replaces_feature_id"] == 758
    hype = c.get("/api/platform/market-radar/sentiment/hype?asset=BTC")
    assert hype.status_code == 200
    assert hype.json()["hype_spike"] == "Detected"
    assert c.get("/api/platform/market-radar/sentiment/hype/scan").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/social_hype_analyzer_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 293
    assert seed["replaces_feature_id"] == 758
    assert seed["standalone"] is False
