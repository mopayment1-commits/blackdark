"""Tests — #287 merged into #272 Community Pulse cluster."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import community_pulse as cp


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "community_pulse_seed.json"
    seed.write_text(
        json.dumps({
            "provider": {
                "name": "LunarCrush",
                "fallback": "Kaito",
                "monthly_cost_cap_usd": 500,
                "current_spend_usd": 100,
                "paused_on_exceed": False,
            },
            "assets": {
                "BTC": {
                    "mindshare_pct": 42.5,
                    "mentions_weekly": 125000,
                    "trend": "rising",
                    "sentiment": {
                        "label": "positive",
                        "score": 0.72,
                        "model": "lunarcrush-v3",
                        "model_version": "3.1",
                        "source_coverage_pct": 94,
                        "sarcasm_detected": False,
                    },
                    "social_dominance": {"dominance_pct": 38.2, "rank": 1},
                    "social_volume": {"volume_24h": 2850000, "volume_change_pct": 12.5},
                },
                "DOGE": {
                    "mindshare_pct": 0.5,
                    "mentions_weekly": 150,
                    "sentiment": {
                        "label": "negative",
                        "score": 0.35,
                        "model": "lunarcrush-v3",
                        "model_version": "3.1",
                        "source_coverage_pct": 35,
                        "sarcasm_detected": True,
                    },
                    "social_dominance": {"dominance_pct": 0.1, "rank": 99},
                    "social_volume": {"volume_24h": 5000, "volume_change_pct": -5},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(cp, "_SEED_PATH", seed)
    return seed


def test_287_rejected_standalone(isolated_seed):
    status = cp.community_pulse_status()
    assert 287 in status["absorbed_ids"]
    assert 287 in status["rejected_standalone_tickets"]
    assert status["no_nlp_team"] is True


def test_nlp_sentiment_sub_task(isolated_seed):
    panel = cp.build_community_pulse_panel("BTC")
    sentiment = panel["sentiment"]
    assert sentiment["sub_task"] == "#287"
    assert sentiment["model_version_visible"] is True
    assert sentiment["source_coverage_visible"] is True
    assert sentiment["not_a_signal"] is True


def test_sarcasm_low_volume_handling(isolated_seed):
    panel = cp.build_community_pulse_panel("DOGE")
    sentiment = panel["sentiment"]
    assert sentiment["sarcasm_detected"] is True
    assert sentiment["confidence"] == "low"
    assert sentiment["greyed_out"] is True


def test_purchased_feed_no_nlp_team(isolated_seed):
    gate = cp.build_provider_gate()
    assert gate["no_nlp_team"] is True
    assert gate["purchased_feed"] is True
    assert gate["no_raw_scraper"] is True


def test_absorbs_272_290_292(isolated_seed):
    panel = cp.build_community_pulse_panel("BTC")
    assert panel["mindshare"]["sub_task"] == "#272"
    assert panel["social_dominance"]["sub_task"] == "#290"
    assert panel["social_volume"]["sub_task"] == "#292"
    assert 290 in panel["feature_ids"]
    assert 292 in panel["feature_ids"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/community-pulse/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/community-pulse?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["sentiment"]["sub_task"] == "#287"


def test_full_seed_exists():
    seed = json.loads(Path("data/community_pulse_seed.json").read_text(encoding="utf-8"))
    assert 287 in seed["feature_ids"]
    assert 272 in seed["feature_ids"]
    assert seed["provider"]["name"] == "LunarCrush"
