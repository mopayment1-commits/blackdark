"""Tests — #282 Flow Anomaly Detection Module (Intelligence Ledger, rule-based)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import flow_anomaly_detection as fad


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "flow_anomaly_detection_seed.json"
    seed.write_text(
        json.dumps({
            "baselines": [
                {
                    "asset": "BTC",
                    "venue": "binance",
                    "metric": "cvd_hourly",
                    "window_days": 30,
                    "trades_per_day": 45000,
                    "documented": True,
                    "rolling_mean": 1000000,
                    "rolling_std": 200000,
                    "iqr_q1": 800000,
                    "iqr_q3": 1200000,
                    "current_value": 2500000,
                    "sample_trade_ids": ["t-001"],
                },
                {
                    "asset": "SOL",
                    "venue": "bybit",
                    "metric": "cvd_hourly",
                    "window_days": 30,
                    "trades_per_day": 450,
                    "documented": True,
                    "rolling_mean": 100000,
                    "rolling_std": 20000,
                    "iqr_q1": 80000,
                    "iqr_q3": 120000,
                },
            ],
            "alerts": [
                {
                    "asset": "BTC",
                    "venue": "binance",
                    "metric": "cvd_hourly",
                    "expected_range": "800000 – 1200000",
                    "actual_value": 2500000,
                    "deviation_pct": 150.0,
                    "detection_method": "z_score",
                    "timestamp": "2026-08-25T14:32:00+00:00",
                    "trade_ids": ["t-001"],
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(fad, "_SEED_PATH", seed)
    return seed


def test_baseline_controls(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    controls = fad.build_baseline_controls(seed["baselines"][0])
    assert controls["window_days"] == 30
    assert controls["sample_sufficient"] is True
    assert controls["detection_enabled"] is True


def test_insufficient_sample_disabled(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    controls = fad.build_baseline_controls(seed["baselines"][1])
    assert controls["trades_per_day"] < fad._MIN_TRADES_PER_DAY
    assert controls["detection_enabled"] is False


def test_z_score_detection(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    result = fad.detect_anomaly_from_baseline(
        actual=2500000,
        baseline=seed["baselines"][0],
        method="z_score",
    )
    assert result is not None
    assert result["detection_method"] in ("z_score", "both")
    assert result["not_a_signal"] is True


def test_evidence_schema(isolated_seed):
    alerts = fad.list_anomaly_alerts(asset="BTC")
    alert = alerts["alerts"][0]
    assert "evidence" in alert
    assert "trade_ids" in alert["evidence"]
    assert alert["confidence"] in ("low", "medium", "high")
    assert "Anomaly:" in alert["display"]


def test_scope_lock_spot_perp_only(isolated_seed):
    scope = fad.build_scope_lock()
    assert "spot" in scope["asset_classes"]
    assert "DEX flow = separate" in scope["display"]
    assert "Whale alerts = separate" in scope["display"]


def test_rule_based_first(isolated_seed):
    status = fad.flow_anomaly_detection_status()
    assert status["acceptance_criteria"]["rule_based_first"] is True
    assert status["acceptance_criteria"]["ml_deferred_wave_3"] is True


def test_flow_anomaly_panel(isolated_seed):
    panel = fad.build_flow_anomaly_panel("BTC")
    assert panel["ok"] is True
    assert panel["feature_id"] == 282
    assert panel["rule_based_first"] is True
    assert len(panel["baseline_controls"]) >= 1
    assert panel["disclaimer_hideable"] is False


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/flow-anomaly/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/flow-anomaly?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["rule_based_first"] is True
    assert c.get("/api/platform/intelligence-ledger/flow-anomaly/alerts?asset=BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/flow_anomaly_detection_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 282
    assert len(seed["baselines"]) >= 2
    assert len(seed["alerts"]) >= 1
