"""Tests — #821 TradingView Lightweight Charts chart_component."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import chart_component as cc
from bd_platform import market_radar_indicators as mri


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"))


def test_821_status(seed):
    status = cc.chart_component_status_821(seed=seed)
    assert status["standalone_rejected"] is True
    assert status["component"] == "chart_component"
    assert status["chart_library_version"] == "v4"
    assert status["max_indicators_sprint_1"] == 4
    assert status["save_settings_deferred"] is True
    assert status["export_deferred"] is True
    assert "BTC" in status["supported_assets"]
    assert "ETH" in status["supported_assets"]


def test_821_four_indicators_only(seed):
    chart = cc.build_chart_component_821("BTC", seed=seed)
    assert chart["ok"] is True
    assert chart["selected_charting_solution"] is True
    assert chart["max_indicators_sprint_1"] == 4
    ind = chart["indicators"]
    assert "RSI" in ind
    assert "MACD" in ind
    assert "SMA" in ind
    assert "Volume" in ind


def test_821_tradingview_v4_config(seed):
    chart = cc.build_chart_component_821("BTC", seed=seed)
    tv = chart["tradingview_config"]
    assert tv["version"] == "v4"
    assert "lightweight-charts@4" in tv["cdn"]
    assert tv["interaction"]["zoom"] is True
    assert tv["interaction"]["pan"] is True


def test_821_performance_targets(seed):
    chart = cc.build_chart_component_821("BTC", seed=seed)
    perf = chart["performance"]
    assert perf["max_candles_supported"] >= 50000
    assert perf["within_latency_target"] is True
    assert perf["responsive"] is True


def test_821_zoom_pan_no_save_export(seed):
    chart = cc.build_chart_component_821("BTC", seed=seed)
    interaction = chart["interaction"]
    assert interaction["zoom"] is True
    assert interaction["pan"] is True
    assert interaction["save_settings"] is False
    assert interaction["export"] is False


def test_821_ohlcv_cache(seed):
    cc._OHLCV_CACHE.clear()
    first = cc.fetch_ohlcv_cached_821("BTC", seed=seed)
    assert first["ok"] is True
    assert first["cache_hit"] is False
    second = cc.fetch_ohlcv_cached_821("BTC", seed=seed)
    assert second["cache_hit"] is True
    assert second["latency_ms"] <= 100


def test_821_multi_asset(seed):
    multi = cc.build_multi_asset_chart_config_821(seed=seed)
    assert multi["ok"] is True
    assert len(multi["assets"]) >= 2
    assert all(c["ok"] for c in multi["charts"])


def test_821_asset_card(seed):
    card = cc.build_asset_card_chart_indicators_821("BTC", seed=seed)
    assert card["ok"] is True
    assert card["panel_name_ar"] == "مؤشرات فنية"


def test_821_market_radar_integration():
    panel = mri.build_market_radar_panel("BTC")
    chart = panel.get("chart_component_821") or {}
    assert chart.get("ok") is True
    assert chart.get("component") == "chart_component"


def test_821_e2e(seed):
    e2e = cc.run_chart_component_e2e_821(seed=seed)
    assert e2e["all_passed"] is True


def test_821_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/market-radar/chart-component/status").status_code == 200
    chart = c.get("/api/platform/intelligence-ledger/market-radar/chart-component?asset=BTC")
    assert chart.status_code == 200
    assert chart.json()["chart_library_version"] == "v4"
    assert c.get("/api/platform/intelligence-ledger/market-radar/chart-component/ohlcv?asset=BTC").status_code == 200
    multi = c.get("/api/platform/intelligence-ledger/market-radar/chart-component/multi-asset")
    assert multi.status_code == 200
    assert multi.json()["ok"] is True
    e2e = c.get("/api/platform/intelligence-ledger/market-radar/chart-component/e2e")
    assert e2e.status_code == 200
    assert e2e.json()["all_passed"] is True
