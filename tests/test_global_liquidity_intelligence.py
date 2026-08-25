"""Tests — #248 Global Liquidity Intelligence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import global_liquidity_intelligence as gli


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "global_liquidity_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 248,
            "module_version": "2.1",
            "index_version": "1.2",
            "last_revised": "2026-08-25",
            "calculation_date": "2026-08-25",
            "tier": "pro",
            "no_real_time_fabrication": True,
            "update_frequencies": {
                "policy_rate": "Daily",
                "m2": "Monthly",
                "fx": "Hourly",
            },
            "lag_methodology": {
                "fed_m2": {"display": "M2 (Fed): 14-day lag", "lag_days": 14},
                "ecb_m2": {"display": "M2 (ECB): 30-day lag", "lag_days": 30},
                "boj_m2": {"display": "M2 (BoJ): 45-day lag", "lag_days": 45},
                "policy_rate": {"display": "Policy Rate: same-day", "lag_days": 0},
                "dxy": {"display": "FX: hourly", "lag_days": 0},
            },
            "lag_methodology_display": (
                "M2 (Fed): 14-day lag | M2 (ECB): 30-day lag | M2 (BoJ): 45-day lag | "
                "Policy Rate: same-day | FX: hourly"
            ),
            "composite_weights": {
                "fed_m2": 0.30,
                "ecb_m2": 0.25,
                "boj_m2": 0.20,
                "global_policy_rate": 0.15,
                "dxy": 0.10,
            },
            "composite_display": (
                "Components: Fed M2 (30%) + ECB M2 (25%) + BoJ M2 (20%) + "
                "Global Policy Rate Average (15%) + DXY (10%) | Version: 1.2 | Last Revised: 2026-08-25"
            ),
            "series": {
                "fed_m2": {
                    "source": "Federal Reserve",
                    "update_frequency": "Monthly",
                    "lag_days": 14,
                    "as_of": "2026-08-11",
                    "next_release": "2026-09-01",
                    "latest_value": 21.42,
                    "latest_value_display": (
                        "Latest Available M2 (Fed): $21.42T | As of: 2026-08-11 | Next Release: 2026-09-01"
                    ),
                    "yoy_pct": 2.8,
                    "revisions": [
                        {"release_date": "2026-08-01", "value": 21.38, "type": "initial_release"},
                        {"release_date": "2026-08-15", "value": 21.40, "delta": 0.02, "type": "revision_1"},
                        {"release_date": "2026-08-25", "value": 21.42, "delta": 0.02, "type": "current"},
                    ],
                    "revision_display": (
                        "Value: $21.42T | Initial Release: 2026-08-01 | "
                        "Revision 1: 2026-08-15 (+$0.02T) | Current: 2026-08-25"
                    ),
                },
                "global_policy_rate": {
                    "update_frequency": "Daily",
                    "as_of": "2026-08-25",
                    "latest_value": 4.35,
                    "trajectory": "declining",
                },
                "dxy": {
                    "update_frequency": "Hourly",
                    "as_of": "2026-08-25T14:00:00+00:00",
                    "latest_value": 103.8,
                },
            },
            "composite_index": {
                "value": 105.2,
                "calculation_date": "2026-08-25",
                "latest_input_date": "2026-08-11",
                "latest_input_series": "Fed M2",
            },
            "regime": {
                "label": "Easing",
                "m2_yoy_weighted_pct": 2.6,
                "policy_rate_trajectory": "declining",
                "duration_months": 8,
                "regime_display": (
                    "Regime: Easing | Based on: M2 YoY + Policy Rate trajectory | Duration: 8 months"
                ),
            },
            "historical_relationship": {
                "correlation_90d_lagged": 0.58,
                "correlation_varies_by_regime": True,
            },
            "macro_context": {
                "display": "Macro Context: Liquidity Expanding",
            },
            "assets": {"BTC": {"correlation_90d_lagged": 0.58}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(gli, "_SEED_PATH", seed)
    return seed


def test_lag_methodology_documented(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    lag = dash["lag_methodology"]
    assert "14-day lag" in lag["lag_display"]
    assert "30-day lag" in lag["lag_display"]
    assert "45-day lag" in lag["lag_display"]
    assert "same-day" in lag["lag_display"]
    assert lag["not_real_time"] is True


def test_revisions_tracked(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    fed = dash["series"]["fed_m2"]
    rev = fed["revisions"]
    assert rev["revisions_tracked"] is True
    assert rev["revision_count"] >= 2
    assert "Initial Release" in fed["revisions"]["revision_display"]
    assert "Revision 1" in fed["revisions"]["revision_display"]


def test_no_fabricated_realtime(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    assert dash["no_fabricated_realtime"] is True
    assert dash["no_real_time_m2"] is True
    assert dash["real_time_m2_forbidden"] is True
    fed = dash["series"]["fed_m2"]
    assert "Latest Available" in fed["latest_value_display"]
    assert "As of:" in fed["latest_value_display"]
    assert "Next Release" in fed["latest_value_display"]
    text = json.dumps(dash)
    assert "Real-Time Global M2" not in text


def test_composite_index_documented(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    comp = dash["composite_index"]
    assert comp["value"] == 105.2
    assert "Fed M2 (30%)" in comp["composite_display"]
    assert comp["methodology_documented"] is True
    assert "Global Liquidity Index" in comp["index_display"]
    assert "Latest Input Date" in comp["index_display"]


def test_historical_not_predictive(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    rel = dash["historical_relationship"]
    assert rel["not_predictive"] is True
    assert rel["not_causation"] is True
    assert "Not predictive" in rel["relationship_display"]
    assert "Correlation varies by regime" in rel["relationship_display"]


def test_regime_descriptive(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    regime = dash["liquidity_regime"]
    assert regime["regime"] in ("Tightening", "Neutral", "Easing")
    assert regime["descriptive_only"] is True
    assert regime["no_price_target"] is True
    assert "Duration: 8 months" in regime["regime_display"]
    text = json.dumps(dash)
    assert "BTC to $" not in text


def test_disclaimer_non_hideable(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    assert dash["disclaimer"]["hideable"] is False
    assert dash["disclaimer_top"] == dash["disclaimer_bottom"]
    assert "inherent lags" in dash["disclaimer"]["text"].lower()


def test_macro_context_not_opportunity(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    ctx = dash["macro_context"]
    assert "Macro Context" in ctx["display"]
    assert ctx["not_opportunity_framing"] is True
    assert ctx["not_buy_signal"] is True
    text = json.dumps(dash)
    assert "liquidity pump" not in text.lower()
    assert "buy crypto" not in text.lower()


def test_batch_updates_only(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    assert "Monthly" in dash["batch_update_policy"]
    assert dash["lag_methodology"]["no_sub_second_updates"] is True


def test_version_timestamp_on_index(isolated_seed):
    dash = gli.build_global_liquidity_dashboard("BTC")
    assert dash["module_version"] == "2.1"
    assert "Calculation Date" in dash["composite_index"]["index_display"]
    assert dash["composite_index"]["latest_input_date"] == "2026-08-11"


def test_liquidity_regime_endpoint(isolated_seed):
    regime = gli.build_liquidity_regime("BTC")
    assert regime["regime"] == "Easing"
    assert regime["not_predictive"] is True


def test_liquidity_index_endpoint(isolated_seed):
    idx = gli.build_liquidity_index()
    assert idx["composite_index"]["value"] == 105.2
    assert idx["no_fabricated_realtime"] is True


def test_status(isolated_seed):
    status = gli.global_liquidity_status()
    assert status["feature_id"] == 248
    assert status["standalone"] is False
    assert status["tier"] == "pro"


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/global-liquidity/status").status_code == 200
    status = c.get("/api/platform/market-radar/global-liquidity/status").json()
    assert status["feature_id"] == 248
    dash = c.get("/api/platform/market-radar/global-liquidity/dashboard?asset=BTC")
    assert dash.status_code == 200
    assert dash.json()["composite_index"]["value"] == 105.2
    assert c.get("/api/platform/market-radar/global-liquidity/regime?asset=BTC").status_code == 200
    assert c.get("/api/platform/market-radar/global-liquidity/index").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/global_liquidity_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 248
    assert seed["no_real_time_fabrication"] is True
    assert "fed_m2" in seed["series"]
