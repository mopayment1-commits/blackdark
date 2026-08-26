"""Tests — #1008 Asset Screener & Filter Engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import asset_screener as asc


@pytest.fixture
def screener_seed(tmp_path, monkeypatch):
    p = tmp_path / "asset_screener_seed.json"
    p.write_text(json.dumps({
        "assets": [
            {"symbol": "BTC", "market_cap_usd": 1e12, "volume_24h_usd": 1e10,
             "bot_activity_score": 20, "yield_pct": None, "onchain_signal": "accumulation"},
            {"symbol": "ETH", "market_cap_usd": 4e11, "volume_24h_usd": 5e9,
             "bot_activity_score": 50, "yield_pct": 3.0, "onchain_signal": "neutral"},
            {"symbol": "DOGE", "market_cap_usd": 1e10, "volume_24h_usd": 1e9,
             "bot_activity_score": 80, "yield_pct": None, "onchain_signal": None},
            {"symbol": "SOL", "market_cap_usd": 8e10, "volume_24h_usd": 3e9,
             "bot_activity_score": 30, "yield_pct": 5.0, "onchain_signal": "distribution"},
        ],
        "builtin_presets": {
            "low_bot": {
                "name": "Low Bot", "version": "1.0",
                "filters": {"bot_activity_score": {"max": 35}},
                "sort_by": "market_cap_usd", "sort_dir": "desc",
            },
        },
        "user_presets": {
            "my_preset": {
                "name": "My Preset",
                "filters": {"market_cap_usd": {"min": 5e10}},
                "sort_by": "market_cap_usd", "sort_dir": "desc",
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(asc, "_SEED_PATH", p)
    return p


def test_1008_backend_enforcement(screener_seed):
    result = asc.run_asset_screener(
        {"bot_activity_score": {"max": 35}},
        page=1,
        page_size=2,
    )
    assert result["filters_server_side"] is True
    assert result["client_side_only_forbidden"] is True
    assert result["pagination"]["mandatory"] is True
    assert result["pagination"]["max_results_per_query"] == 1000
    assert len(result["results"]) <= 2


def test_1008_deterministic_sorting(screener_seed):
    r1 = asc.run_asset_screener(sort_by="market_cap_usd", sort_dir="desc")
    r2 = asc.run_asset_screener(sort_by="market_cap_usd", sort_dir="desc")
    assert r1["result_checksum"] == r2["result_checksum"]
    assert r1["sort"]["logic"]["tie_breaker"] == "market_cap_usd desc"
    symbols = [r["symbol"] for r in r1["results"]]
    assert symbols[0] == "BTC"


def test_1008_missing_data_excluded(screener_seed):
    excluded = asc.run_asset_screener(
        {"yield_pct": {"min": 2.0}},
        include_missing=False,
    )
    symbols_excluded = {r["symbol"] for r in excluded["results"]}
    assert "BTC" not in symbols_excluded
    assert "ETH" in symbols_excluded

    included = asc.run_asset_screener(
        {},
        include_missing=True,
    )
    btc_row = next(r for r in included["results"] if r["symbol"] == "BTC")
    assert btc_row["yield_pct"] == "N/A"
    assert included["no_fabricated_zeros"] is True


def test_1008_presets_versioned(screener_seed):
    presets = asc.list_presets()
    assert presets["presets_versioned"] is True
    builtin = presets["builtin_presets"][0]
    assert builtin["version"] == "1.0"
    assert builtin["versioned"] is True

    result = asc.run_asset_screener(preset_id="low_bot")
    assert result["preset_id"] == "low_bot"
    assert all(r["bot_activity_score"] != "N/A" and (r["bot_activity_score"] or 0) <= 35
               for r in result["results"] if r["bot_activity_score"] != "N/A")


def test_1008_pagination(screener_seed):
    p1 = asc.run_asset_screener(page=1, page_size=2)
    p2 = asc.run_asset_screener(page=2, page_size=2)
    assert p1["pagination"]["has_next"] is True
    assert p1["pagination"]["page"] == 1
    assert len(p1["results"]) == 2
    assert p2["pagination"]["page"] == 2


def test_1008_export(screener_seed):
    json_export = asc.export_screener_results(export_format="json")
    assert json_export["format"] == "json"
    assert json_export["row_count"] > 0

    csv_export = asc.export_screener_results(export_format="csv")
    assert csv_export["format"] == "csv"
    assert "symbol" in csv_export["content"]


def test_1008_status(screener_seed):
    status = asc.asset_screener_status()
    assert status["feature_id"] == 1008
    assert status["builds_on"] == 742
    assert status["acceptance_criteria"]["filters_enforced_backend"] is True


def test_api_routes(screener_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/asset-screener/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/asset-screener/presets").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/asset-screener?page=1&page_size=2").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/asset-screener/export?format=json").status_code == 200
    resp = c.post(
        "/api/platform/intelligence-ledger/asset-screener",
        json={"bot_activity_score": {"max": 40}},
    )
    assert resp.status_code == 200
    assert resp.json()["filters_server_side"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/asset_screener_seed.json").read_text())
    assert seed["feature_id"] == 1008
    assert len(seed["builtin_presets"]) >= 3
