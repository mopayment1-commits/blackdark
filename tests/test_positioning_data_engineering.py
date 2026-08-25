"""Tests — #221 Positioning Intelligence + #223 Data Engineering Stack."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bd_platform import data_engineering_stack as des
from bd_platform import positioning_intelligence as pi


@pytest.fixture
def isolated_positioning_seed(tmp_path, monkeypatch):
    seed = tmp_path / "positioning_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "providers": {
                "binance": {
                    "name": "Binance Top Traders",
                    "definition": "Top 10% by volume",
                    "update_cadence": "hourly",
                },
            },
            "assets": {
                "BTC": {
                    "venues": {
                        "binance": {
                            "top_long_ratio_pct": 70.0,
                            "global_long_ratio_pct": 52.0,
                            "volume_weight": 1.0,
                        },
                    },
                    "retail_long_ratio_pct": 30.0,
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pi, "_SEED_PATH", seed)
    return seed


def test_provider_semantics_visible(isolated_positioning_seed):
    result = pi.get_top_trader_positioning("BTC")
    assert result["ok"] is True
    venue = result["venues"][0]
    assert "Source: Binance Top Traders" in venue["provider_semantics"]
    assert "Top 10% by volume" in venue["provider_semantics"]
    assert "hourly" in venue["provider_semantics"]


def test_not_copy_trade_language(isolated_positioning_seed):
    result = pi.get_top_trader_positioning("BTC")
    assert result["not_copy_trade"] is True
    assert result["not_a_recommendation"] is True
    assert "Top Trader Long Ratio:" in result["panel_display"]
    assert "Copy Trade" not in result["panel_display"]


def test_divergence_alert(isolated_positioning_seed):
    result = pi.get_top_trader_positioning("BTC")
    div = result["divergence"]
    assert "Top Traders:" in div["divergence_display"]
    assert "Retail:" in div["divergence_display"]
    assert div["level"] == "high"


def test_cross_venue_aggregation(isolated_positioning_seed):
    result = pi.get_top_trader_positioning("BTC")
    assert "Aggregated across" in result["cross_venue_display"]
    assert "Weighted by volume" in result["cross_venue_display"]


def test_mandatory_disclaimer(isolated_positioning_seed):
    result = pi.get_top_trader_positioning("BTC")
    assert result["disclaimer_hideable"] is False
    assert "does not predict" in result["disclaimer"].lower()


def test_not_standalone(isolated_positioning_seed):
    status = pi.positioning_intelligence_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 221
    assert "Sentiment Panel" in status["merged_into"]


@pytest.mark.asyncio
async def test_sentiment_panel_integration(isolated_positioning_seed, monkeypatch):
    async def fake_ctx(assets):
        return {"sentiment_compound_index": {"BTC": 0.1}}

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

    from bd_platform.sentiment_intelligence import analyze_asset_sentiment

    result = await analyze_asset_sentiment("BTC")
    assert result.get("positioning_intelligence") is not None
    assert 221 in [int(x.replace("#", "")) for x in result.get("integrated_features", []) if "#" in str(x)]


# ── #223 Data Engineering Stack ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_not_standalone_dbt():
    status = await des.data_engineering_stack_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 223
    assert status["dbt"]["not_standalone"] is True


def test_model_lineage():
    lineage = des.get_model_lineage()
    assert "stg_ingestion_snapshots" in lineage["lineage_display"]
    assert "mart_ingestion_daily" in lineage["lineage_display"]
    assert len(lineage["lineage"]["sources"]) >= 1


def test_model_tests():
    tests = des.get_model_tests()
    assert tests["model_tests_required"] is True
    assert len(tests["tests"]) >= 2
    assert any("not_null" in t["tests"][0] for t in tests["tests"])


def test_api_routes(isolated_positioning_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/sentiment/positioning/status").status_code == 200
    pos = c.get("/api/platform/market-radar/sentiment/positioning?asset=BTC")
    assert pos.status_code == 200
    assert pos.json()["feature_id"] == 221
    assert c.get("/api/platform/data-engineering/status").status_code == 200
    assert c.get("/api/platform/data-engineering/lineage").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/positioning_intelligence_seed.json").read_text(encoding="utf-8"))
    assert "BTC" in seed["assets"]
    assert len(seed["providers"]) >= 5
