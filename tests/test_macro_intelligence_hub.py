"""Tests — #263 Macro Intelligence Hub."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import macro_intelligence_hub as mih


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "macro_intelligence_hub_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 263,
            "methodology_version": "1.3",
            "last_updated": "2026-08-25",
            "calculation_as_of": "2026-08-25",
            "tier_default": "pro",
            "methodology_display": (
                "Macro Integration Methodology v1.3 | Components: 7 modules | "
                "Alignment: Release-time | Look-ahead: Prevented | Last Updated: 2026-08-25"
            ),
            "integrated_modules": [
                {"feature_id": 248, "name": "Global Liquidity", "status": "live"},
                {"feature_id": 211, "name": "Economic Calendar", "status": "live"},
            ],
            "source_calendar": [
                {
                    "event": "Non-Farm Payrolls",
                    "display": (
                        "Next Release: Non-Farm Payrolls | Date: 2026-09-05 | "
                        "Time: 08:30 EST | Source: BLS | Expected Impact: High"
                    ),
                },
            ],
            "aligned_snapshots": {
                "BTC": {
                    "alignment_display": "DXY Release: 14:00 EST | Crypto Data Used: 14:00 EST | Lag: 0",
                    "lag_minutes": 0,
                },
            },
            "series": {
                "BTC": {
                    "daily": [
                        {"date": "2026-08-20", "btc_close": 115600, "dxy": 103.9, "spx": 5455,
                         "btc_published": "2026-08-20T23:59:00+00:00", "dxy_published": "2026-08-20T18:00:00+00:00"},
                        {"date": "2026-08-21", "btc_close": 115200, "dxy": 104.0, "spx": 5448,
                         "btc_published": "2026-08-21T23:59:00+00:00", "dxy_published": "2026-08-21T18:00:00+00:00"},
                        {"date": "2026-08-22", "btc_close": 114800, "dxy": 103.6, "spx": 5460,
                         "btc_published": "2026-08-22T23:59:00+00:00", "dxy_published": "2026-08-22T18:00:00+00:00", "anomaly": True},
                        {"date": "2026-08-25", "btc_close": 116500, "dxy": 103.8, "spx": 5480,
                         "btc_published": "2026-08-25T18:00:00+00:00", "dxy_published": "2026-08-25T18:00:00+00:00"},
                        {"date": "2026-08-26", "btc_close": 117000, "dxy": 103.5, "spx": 5490,
                         "btc_published": "2026-08-26T18:00:00+00:00", "dxy_published": "2026-08-26T18:00:00+00:00"},
                    ],
                    "regime_history": {
                        "Neutral Macro": {"median_btc_return_pct": 2.1, "sample_months": 12},
                    },
                    "coupling": {
                        "current_regime": "BTC-DXY Decoupling",
                        "duration_days": 12,
                        "historical_median_decoupling_days": 8,
                        "unusual": True,
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(mih, "_SEED_PATH", seed)
    return seed


def test_not_standalone(isolated_seed):
    status = mih.macro_intelligence_hub_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 263


def test_release_time_alignment(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC")
    align = hub["release_time_alignment"]
    assert "14:00 EST" in align["alignment_display"]
    assert align["lag_minutes"] == 0
    assert align["minute_level"] is True


def test_no_look_ahead(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC")
    la = hub["no_look_ahead"]
    assert la["no_look_ahead"] is True
    assert "NO" in la["test_display"]
    assert la["future_data_points"] == 0


def test_source_calendar(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC", tier="pro")
    cal = hub["tier_payload"]["source_calendar"]
    assert len(cal) >= 1
    assert "Non-Farm Payrolls" in cal[0]["display"]
    assert "Expected Impact: High" in cal[0]["display"]


def test_rolling_correlation_windows(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC", tier="pro")
    corrs = hub["tier_payload"]["correlation_tables"]
    windows = {c["window"] for c in corrs}
    assert "30D" in windows
    assert "90D" in windows
    assert "1Y" in windows
    assert all(c.get("rolling") for c in corrs)


def test_regime_analysis_enterprise(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC", tier="enterprise")
    regime = hub["tier_payload"]["regime_analysis"]
    assert "Past regime performance ≠ future" in regime["regime_display"]
    assert regime["not_predictive"] is True


def test_no_causation_language(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC")
    text = json.dumps(hub)
    assert "sell!" not in text.lower()
    assert "killing crypto" not in text.lower()
    assert hub["not_causation_language"] is True
    assert "Coupling:" in hub["coupling_note"]


def test_crypto_coupling_descriptive(isolated_seed):
    coupling = mih.build_macro_coupling("BTC")
    assert "BTC-DXY Decoupling" in coupling["coupling_display"]
    assert coupling["descriptive_only"] is True
    assert coupling["not_predictive"] is True


def test_anomaly_detection(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC", tier="enterprise")
    anomaly = hub["tier_payload"]["anomaly_detection"]
    assert anomaly is not None
    assert "Anomaly" in anomaly["display"]
    assert "Divergence: Yes" in anomaly["display"]


def test_disclaimer_non_hideable(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC")
    assert hub["disclaimer"]["hideable"] is False
    assert hub["disclaimer_top"] == hub["disclaimer_bottom"]


def test_methodology_versioned(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC")
    assert "Macro Integration Methodology v1.3" in hub["methodology_display"]
    assert "Look-ahead: Prevented" in hub["methodology_display"]


def test_tier_gating(isolated_seed):
    free = mih.build_macro_intelligence_hub("BTC", tier="free")
    pro = mih.build_macro_intelligence_hub("BTC", tier="pro")
    ent = mih.build_macro_intelligence_hub("BTC", tier="enterprise")
    assert "correlation_tables" not in free["tier_payload"]
    assert "correlation_tables" in pro["tier_payload"]
    assert "regime_analysis" in ent["tier_payload"]


def test_integrated_modules(isolated_seed):
    hub = mih.build_macro_intelligence_hub("BTC")
    assert hub["standalone"] is False
    assert hub["module_count"] >= 2
    assert "modules" in hub


def test_verify_no_look_ahead_function(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    rows = seed["series"]["BTC"]["daily"]
    result = mih.verify_no_look_ahead(rows, calculation_as_of="2026-08-25")
    assert result["no_look_ahead"] is True
    fail = mih.verify_no_look_ahead(rows, calculation_as_of="2026-08-20")
    assert fail["no_look_ahead"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/macro-hub/status").status_code == 200
    status = c.get("/api/platform/market-radar/macro-hub/status").json()
    assert status["feature_id"] == 263
    hub = c.get("/api/platform/market-radar/macro-hub/dashboard?asset=BTC&tier=pro")
    assert hub.status_code == 200
    assert hub.json()["standalone"] is False
    assert c.get("/api/platform/market-radar/macro-hub/coupling?asset=BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/macro_intelligence_hub_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 263
    assert seed["standalone"] is False
    assert len(seed["integrated_modules"]) >= 7
