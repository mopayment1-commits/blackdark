"""Tests — #273 Momentum Intelligence + #755 Technical Ratings."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import momentum_intelligence as mi
from bd_platform import technical_ratings as tr


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    prices = [{"date": f"2026-08-{i:02d}", "close": 100 + i * 2} for i in range(1, 26)]
    prices[-1] = {"date": "2026-08-25", "close": 150}
    seed = tmp_path / "momentum_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "formula_version": "2.1",
            "formula": {
                "display": "Momentum = Price Trend (40%) + Acceleration (35%) + Volatility-Adjusted Return (25%)",
                "weights": {"trend": 0.4, "acceleration": 0.35, "vol_adjusted_return": 0.25},
            },
            "no_look_ahead": True,
            "assets": {
                "BTC": {
                    "price_series_daily": prices,
                    "historical_validation": {
                        "period_years": 2.5,
                        "threshold_score": 7.0,
                        "forward_30d_return_pct": 4.2,
                        "forward_30d_volatility_pct": 18.5,
                        "sample_count": 312,
                        "validation_display": "Momentum Score > 7 → Forward 30D return: +4.2% (but with 18.5% volatility)",
                        "not_a_promise": True,
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(mi, "_SEED_PATH", seed)
    return seed


def test_formula_version_documented(isolated_seed):
    result = mi.get_momentum_analysis("BTC")
    assert result["ok"] is True
    assert "Version: 2.1" in result["formula_display"]
    assert "40%" in result["formula_display"]
    assert "7D/30D/90D" in result["formula_display"]


def test_no_look_ahead(isolated_seed):
    prices = [100.0 + i for i in range(30)]
    check = mi.verify_no_look_ahead(prices, 25)
    assert check["no_look_ahead"] is True
    assert "NO" in check["test_display"]

    result = mi.get_momentum_analysis("BTC")
    assert result["no_look_ahead"]["no_look_ahead"] is True


def test_historical_validation(isolated_seed):
    result = mi.get_momentum_analysis("BTC")
    val = result["historical_validation"]
    assert val["period_years"] >= 2
    assert val["not_a_promise"] is True
    assert "Forward 30D return" in result["validation_display"]
    assert "volatility" in result["validation_display"].lower()


def test_multi_window_decomposition(isolated_seed):
    result = mi.get_momentum_analysis("BTC")
    assert "short" in result["windows"]
    assert "7D" in result["multi_window_display"]
    assert "/10" in result["multi_window_display"]


def test_components_visible(isolated_seed):
    result = mi.get_momentum_analysis("BTC")
    comps = result["components"]
    assert "Trend Component:" in comps["trend"]["display"]
    assert "Acceleration Component:" in comps["acceleration"]["display"]
    assert "Volatility-Adjusted Return:" in comps["volatility_adjusted_return"]["display"]
    assert comps["trend"]["weight_pct"] == 40
    assert comps["acceleration"]["weight_pct"] == 35


def test_not_a_signal(isolated_seed):
    result = mi.get_momentum_analysis("BTC")
    assert result["not_a_signal"] is True
    assert result["not_buy_sell"] is True
    assert "Momentum Analysis:" in result["analysis_display"]
    assert "Buy" not in result["analysis_display"]
    assert "Sell" not in result["analysis_display"]


def test_mandatory_disclaimer(isolated_seed):
    result = mi.get_momentum_analysis("BTC")
    assert result["disclaimer_hideable"] is False
    assert "not a buy/sell signal" in result["disclaimer"].lower()


def test_not_standalone(isolated_seed):
    status = mi.momentum_intelligence_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 273
    assert "#755" in status["merged_into"]


def test_technical_ratings_integration(isolated_seed):
    composite = tr.get_technical_composite("BTC")
    assert composite["ok"] is True
    assert composite["feature_id"] == 755
    assert composite["momentum_intelligence"] is not None
    assert composite["inputs"]["momentum_273"]["feature_id"] == 273
    assert composite["not_standalone_recommendation"] is True
    assert composite["not_a_signal"] is True


def test_technical_ratings_status(isolated_seed):
    status = tr.technical_ratings_status()
    assert status["feature_id"] == 755
    assert 273 in status["merged_features"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/momentum/status").status_code == 200
    mom = c.get("/api/platform/market-radar/momentum?asset=BTC")
    assert mom.status_code == 200
    assert mom.json()["feature_id"] == 273
    assert c.get("/api/platform/market-radar/technical-ratings/status").status_code == 200
    tech = c.get("/api/platform/market-radar/technical-ratings?asset=BTC")
    assert tech.status_code == 200
    assert tech.json()["feature_id"] == 755


def test_full_seed_exists():
    seed = json.loads(Path("data/momentum_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 273
    assert seed["standalone"] is False
    assert "BTC" in seed["assets"]
