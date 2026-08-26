"""Tests — #300 Trending Assets Module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import trending_assets as ta


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    trending_seed = tmp_path / "trending_assets_seed.json"
    cp_seed = tmp_path / "community_pulse_seed.json"
    trending_seed.write_text(
        json.dumps({
            "as_of_timestamp_utc": "2026-08-26T00:00:00+00:00",
            "alias_rules": {"BTC": ["Bitcoin"], "PEPE": ["Pepe"]},
            "assets": [
                {"symbol": "PEPE", "mentions_daily": 5000, "mentions_current": 8000, "mentions_baseline": 2000},
                {"symbol": "SHIB", "mentions_daily": 50, "mentions_current": 55, "mentions_baseline": 10},
            ],
        }),
        encoding="utf-8",
    )
    cp_seed.write_text(
        json.dumps({
            "methodology_version": "1.0",
            "provider": {"name": "LunarCrush", "paused_on_exceed": False},
            "assets": {"BTC": {"mentions_weekly": 1000}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ta, "_SEED_PATH", trending_seed)
    monkeypatch.setattr(ta, "_COMMUNITY_PULSE_SEED", cp_seed)
    return trending_seed


def test_dependency_gate_272(isolated_seed):
    dep = ta.check_community_pulse_dependency()
    assert dep["stable"] is True
    assert dep["dependency_feature_id"] == 272


def test_alias_collision_protection(isolated_seed):
    alias = ta.resolve_alias("BTC")
    assert "Bitcoin" in alias["canonical_names"]
    assert alias["alias_rules_documented"] is True


def test_low_volume_excluded(isolated_seed):
    entry = ta.build_trending_asset_entry(
        {"symbol": "SHIB", "mentions_daily": 50, "mentions_current": 55, "mentions_baseline": 10},
        alias_rules={}, as_of="2026-08-26T00:00:00+00:00",
    )
    assert entry is None


def test_deterministic_rank(isolated_seed):
    asset = {"symbol": "PEPE", "mentions_daily": 5000, "mentions_current": 8000, "mentions_baseline": 2000}
    score1 = ta.compute_deterministic_rank_score(
        {**asset, "trend_acceleration": 1.5}, as_of="2026-08-26T00:00:00+00:00",
    )
    score2 = ta.compute_deterministic_rank_score(
        {**asset, "trend_acceleration": 1.5}, as_of="2026-08-26T00:00:00+00:00",
    )
    assert score1 == score2


def test_leaderboard(isolated_seed):
    board = ta.build_trending_leaderboard()
    assert board["ok"] is True
    assert board["data_source"] == "#272 Community Pulse"
    symbols = [e["symbol"] for e in board["leaderboard"]]
    assert "SHIB" not in symbols


def test_status(isolated_seed):
    status = ta.trending_assets_status()
    assert status["feature_id"] == 300
    assert status["acceptance_criteria"]["deterministic_rank"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/trending-assets/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/trending-assets").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/trending_assets_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 300
    assert seed["dependency_feature_id"] == 272
