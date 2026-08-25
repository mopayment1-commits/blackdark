"""Tests — #272 Social Signal & Mindshare Module merged into Intelligence Ledger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import mindshare_intelligence as mi


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "mindshare_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "provider_config": {
                "name": "LunarCrush",
                "monthly_cost_cap_usd": 500,
                "current_spend_usd": 320,
                "paused_on_exceed": False,
            },
            "universe": {
                "version": "1.2",
                "asset_count": 250,
                "sources": ["LunarCrush API"],
            },
            "bot_filtering": {
                "false_positive_rate_pct": 2.1,
                "monthly_audit_sample": 500,
            },
            "gainers_losers": {
                "period": "7D",
                "gainers": [{"symbol": "SOL", "mindshare_change_pct": 2.4}],
                "losers": [{"symbol": "DOGE", "mindshare_change_pct": -1.2}],
            },
            "assets": {
                "BTC": {
                    "mindshare_pct": 28.5,
                    "mentions_weekly": 125000,
                    "trend": "rising",
                    "mapping_confidence_pct": 99.5,
                    "mapping_verified": True,
                },
                "ALT": {
                    "mindshare_pct": 0.02,
                    "mentions_weekly": 45,
                    "trend": "flat",
                    "mapping_confidence_pct": 72.0,
                    "mapping_verified": False,
                    "community_submitted": True,
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(mi, "_SEED_PATH", seed)
    return seed


def test_no_raw_social_pipeline(isolated_seed):
    gate = mi.build_provider_gate()
    assert gate["no_raw_scraper"] is True
    assert "LunarCrush" in gate["display"]
    assert "Cost cap" in gate["display"]


def test_bot_spam_filtering(isolated_seed):
    filt = mi.build_bot_spam_filtering()
    assert filt["methodology_documented"] is True
    assert filt["spam_excluded_from_universe"] is True
    assert filt["no_filtering_no_data"] is True


def test_universe_documented(isolated_seed):
    universe = mi.build_universe_documentation()
    assert universe["universe_documented"] is True
    assert "250 assets" in universe["display"]
    assert "warmup: 7 days" in universe["display"]


def test_low_volume_greyed_out(isolated_seed):
    panel = mi.build_mindshare_panel("ALT")
    assert panel["ok"] is True
    assert panel["mindshare"]["greyed_out"] is True
    assert panel["mindshare"]["confidence"] == "insufficient"
    assert "Insufficient data" in panel["mindshare"]["display"]


def test_high_volume_confidence(isolated_seed):
    panel = mi.build_mindshare_panel("BTC")
    assert panel["mindshare"]["confidence"] == "high"
    assert panel["mindshare"]["trend_calculated"] is True
    assert panel["mindshare"]["greyed_out"] is False


def test_gainers_losers_feature_not_product(isolated_seed):
    movers = mi.build_gainers_losers()
    assert movers["feature_not_product"] is True
    assert len(movers["gainers"]) >= 1


def test_not_standalone(isolated_seed):
    status = mi.mindshare_intelligence_status()
    assert status["feature_id"] == 272
    assert status["standalone"] is False
    assert status["acceptance_criteria"]["no_raw_social_pipeline"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/mindshare/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/mindshare?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["mindshare"]["confidence"] == "high"


def test_full_seed_exists():
    seed = json.loads(Path("data/mindshare_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 272
    assert seed["provider_config"]["name"] == "LunarCrush"
    assert "BTC" in seed["assets"]
