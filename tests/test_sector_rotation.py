"""Tests — #286 Sector Rotation & Flow Module (Sprint 2 Intelligence Ledger)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import sector_rotation as sr


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "sector_rotation_seed.json"
    seed.write_text(
        json.dumps({
            "taxonomy": {
                "version": "1.0",
                "base_sources": ["Messari", "The Block"],
                "sector_count": 2,
                "custom_sectors": [{"name": "AI Agents", "custom": True}],
            },
            "survivorship": {
                "delisted_count": 3,
                "universe_version": "2026.08.1",
            },
            "universe": {"version": "2026.08.1", "versioned": True},
            "sectors": {
                "Layer 1": {
                    "relative_strength": 0.72,
                    "flow_rotation_score": 0.65,
                    "return_7d_pct": 3.2,
                    "return_30d_pct": 12.5,
                    "assets": [
                        {"symbol": "BTC", "above_ma50": True, "return_30d": 0.15},
                        {"symbol": "ETH", "above_ma50": True, "return_30d": 0.08},
                        {"symbol": "SOL", "above_ma50": False, "return_30d": -0.05},
                    ],
                },
                "DeFi": {
                    "relative_strength": 0.45,
                    "flow_rotation_score": 0.38,
                    "return_7d_pct": -1.8,
                    "assets": [
                        {"symbol": "UNI", "above_ma50": False, "return_30d": -0.12},
                        {"symbol": "AAVE", "above_ma50": False, "return_30d": -0.08},
                    ],
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(sr, "_SEED_PATH", seed)
    return seed


def test_sector_taxonomy_versioned(isolated_seed):
    tax = sr.build_sector_taxonomy()
    assert tax["version"] == "1.0"
    assert "Messari" in tax["base_sources"]
    assert tax["reclassification_versioned"] is True
    assert "AI Agents" in tax["custom_sectors_flagged"]


def test_survivorship_control(isolated_seed):
    surv = sr.build_survivorship_controls()
    assert surv["delisted_return"] == -1.0
    assert surv["no_look_ahead_bias"] is True
    assert surv["universe_at_time_t_known"] is True
    assert surv["delisted_included_in_historical"] is True


def test_breadth_metrics(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    breadth = sr.build_breadth_metrics(seed["sectors"]["Layer 1"])
    assert breadth["pct_above_ma50"] == pytest.approx(66.7, rel=0.1)
    assert "formula_ma50" in breadth
    assert breadth["breadth_documented"] is True


def test_rotation_leaderboard(isolated_seed):
    lb = sr.build_rotation_leaderboard()
    assert lb["top_sector"] == "Layer 1"
    assert len(lb["leaderboard"]) == 2
    assert lb["leaderboard"][0]["rank"] == 1


def test_rotation_matrix(isolated_seed):
    matrix = sr.build_rotation_matrix()
    assert matrix["sector_count"] == 2
    assert len(matrix["matrix"]) == 2


def test_panel_ok(isolated_seed):
    panel = sr.build_sector_rotation_panel()
    assert panel["ok"] is True
    assert panel["feature_id"] == 286
    assert panel["universe"]["versioned"] is True


def test_acceptance_criteria(isolated_seed):
    status = sr.sector_rotation_status()
    assert status["acceptance_criteria"]["universe_versioned"] is True
    assert status["acceptance_criteria"]["survivorship_controlled"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/sector-rotation/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/sector-rotation").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/sector_rotation_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 286
    assert seed["universe"]["versioned"] is True
    assert len(seed["sectors"]) >= 3
