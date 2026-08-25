"""Tests — #209+#213 Drift Monitoring Engine (merged)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import drift_monitoring_engine as dme


@pytest.fixture
def isolated_drift_store(tmp_path, monkeypatch):
    seed = tmp_path / "drift_baselines_seed.json"
    store = tmp_path / "drift_monitoring.json"
    alerts = tmp_path / "drift_alerts.jsonl"
    seed.write_text(
        json.dumps({
            "baselines": [{
                "version": "v2.1",
                "model_id": "test_model",
                "window_days": 30,
                "updated_at": "2026-08-01",
                "features": {
                    "btc_volatility_24h": {"mean": 2.5, "std": 0.8, "min": 0.5, "max": 6.0},
                    "funding_rate_btc": {"mean": 0.01, "std": 0.005, "min": -0.02, "max": 0.05},
                },
            }],
            "sample_current": {
                "btc_volatility_24h": 5.8,
                "funding_rate_btc": 0.035,
            },
            "sample_stale": {
                "btc_volatility_24h": None,
                "funding_rate_btc": None,
                "stale_since": "2026-08-25T11:00:00+00:00",
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(dme, "_SEED_PATH", seed)
    monkeypatch.setattr(dme, "_STORE_PATH", store)
    monkeypatch.setattr(dme, "_ALERTS_PATH", alerts)
    return store


def test_versioned_baseline_display(isolated_drift_store):
    baseline = dme.get_baseline("v2.1")["baseline"]
    assert "Baseline v2.1" in baseline["display"]
    assert "Window: 30 days" in baseline["display"]
    assert "Updated: 2026-08-01" in baseline["display"]


def test_data_gap_separated_from_drift(isolated_drift_store):
    result = dme.detect_drift({
        "btc_volatility_24h": None,
        "funding_rate_btc": None,
        "stale_since": "2026-08-25T11:00:00+00:00",
    })
    assert result["data_gap_detected"] is True
    gap_types = {a["alert_type"] for a in result["gap_alerts"]}
    assert "data_gap" in gap_types
    assert "stale_data" in gap_types
    assert all(not a.get("is_drift") for a in result["gap_alerts"])


def test_distribution_drift_detected(isolated_drift_store):
    result = dme.detect_drift({
        "btc_volatility_24h": 5.8,
        "funding_rate_btc": 0.035,
    })
    assert result["drift_detected"] is True
    assert all(a["alert_type"] == "distribution_drift" for a in result["drift_alerts"])


def test_severity_and_persistence(isolated_drift_store):
    result = dme.detect_drift({"btc_volatility_24h": 5.8, "funding_rate_btc": 0.035})
    for alert in result["drift_alerts"]:
        assert alert["severity"] in ("low", "medium", "high")
        assert alert["persistence"] in ("1_hour", "1_day", "1_week")
        assert "Severity:" in alert["display"]
        assert "Persistence:" in alert["display"]


def test_no_automatic_promotion(isolated_drift_store):
    result = dme.detect_drift({"btc_volatility_24h": 5.8, "funding_rate_btc": 0.035})
    assert result["no_automatic_promotion"] is True
    assert result["human_review_required"] is True
    assert result["retraining_trigger"]["auto_retrain"] is False
    assert "Not: Auto-retrain" in result["retraining_trigger"]["display"]


def test_false_alarm_review(isolated_drift_store):
    result = dme.detect_drift({"btc_volatility_24h": 5.8, "funding_rate_btc": 0.035})
    alert_id = result["drift_alerts"][0]["alert_id"]
    review = dme.review_drift_alert(alert_id, decision="false_alarm", reviewer="analyst@bd")
    assert review["review"]["false_alarm_review"] is True
    assert review["no_automatic_promotion"] is True


def test_reproducible_deterministic(isolated_drift_store):
    test = dme.run_reproducible_drift_test()
    assert test["reproducible"] is True
    assert test["deterministic"] is True


def test_human_review_required_on_alerts(isolated_drift_store):
    result = dme.detect_drift({"btc_volatility_24h": 5.8, "funding_rate_btc": 0.035})
    for alert in result["alerts"]:
        assert alert["human_review_required"] is True
        assert alert.get("auto_action") is None


def test_dashboard_separates_samples(isolated_drift_store):
    dash = dme.get_drift_dashboard(model_id="test_model")
    assert dash["data_gap_separated_from_drift"] is True
    assert dash["current_sample"]["drift_detected"] is True
    assert dash["stale_sample"]["data_gap_detected"] is True


def test_status_policies(isolated_drift_store):
    status = dme.drift_monitoring_status()
    assert 209 in status["merged_features"]
    assert 213 in status["merged_features"]
    assert status["versioned_baselines"] is True
    assert status["false_alarm_review"] is True
    assert status["no_automatic_promotion"] is True


def test_full_seed_file_exists():
    seed = json.loads(Path("data/drift_baselines_seed.json").read_text(encoding="utf-8"))
    assert len(seed["baselines"]) >= 2


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/drift-monitoring/status")
    assert status.status_code == 200
    assert status.json()["feature_id"] == 209

    baselines = c.get("/api/platform/drift-monitoring/baselines")
    assert baselines.status_code == 200

    repro = c.post("/api/platform/drift-monitoring/reproducible-test")
    assert repro.status_code == 200
    assert repro.json()["reproducible"] is True
