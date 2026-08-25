"""Tests — #271 Correlation & Lead-Lag Module merged into Intelligence Ledger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import correlation_lead_lag as cll


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "correlation_lead_lag_seed.json"
    seed.write_text(
        json.dumps({
            "dependency_gate": {
                "data_engine_stable": True,
                "stability_days_required": 30,
                "stability_days_met": 30,
                "production_grade_metrics": True,
            },
            "current_phase": 1,
            "analyses": {
                "BTC:active_addresses": {
                    "correlation": {"coefficient": 0.72, "p_value": 0.003, "window_days": 30},
                    "lead_lag": {"best_lag_days": 3, "max_correlation": 0.68},
                    "data_quality": {
                        "missing_pct": 0.05,
                        "interpolation_method": "linear",
                        "outlier_handling": "winsorize_3sigma",
                    },
                },
                "ETH:gas_used": {
                    "correlation": {"coefficient": 0.38, "p_value": 0.041, "window_days": 90},
                    "lead_lag": {"best_lag_days": 0, "max_correlation": 0.38},
                    "data_quality": {"missing_pct": 0.25},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(cll, "_SEED_PATH", seed)
    return seed


def test_dependency_gate(isolated_seed):
    gate = cll.check_dependency_gate()
    assert gate["gate_passed"] is True
    assert gate["stability_days_required"] == 30
    assert "production-grade" in gate["display"]


def test_no_causation_language(isolated_seed):
    result = cll.build_correlation_analysis("BTC:active_addresses", "active_addresses", window_days=30)
    assert result["ok"] is True
    text = json.dumps(result).lower()
    for banned in ("causes", "drives", "predicts"):
        assert banned not in text
    assert result["no_causation_language"] is True
    assert "does not imply causation" in result["disclaimer"].lower()


def test_window_and_significance_visible(isolated_seed):
    result = cll.build_correlation_analysis("BTC:active_addresses", "active_addresses", window_days=30)
    corr = result["correlation"]
    assert corr["window_visible"] is True
    assert corr["significance_visible"] is True
    assert "p-value" in corr["display"]
    assert "Window: 30D" in corr["display"]


def test_lead_lag_panel(isolated_seed):
    result = cll.build_correlation_analysis("BTC:active_addresses", "active_addresses")
    lag = result["lead_lag"]
    assert lag["lag_range"] == [-30, 30]
    assert "Lead-Lag" in lag["display"]
    assert lag["no_causation_language"] is True


def test_missing_data_blocked(isolated_seed):
    result = cll.build_correlation_analysis("ETH:gas_used", "gas_used", window_days=90)
    assert result["ok"] is False
    assert result["error"] == "missing_data_threshold_exceeded"


def test_scope_lock(isolated_seed):
    scope = cll.build_scope_lock()
    assert scope["current_phase"] == 1
    assert "daily batch" in scope["display"]


def test_not_standalone(isolated_seed):
    status = cll.correlation_lead_lag_status()
    assert status["feature_id"] == 271
    assert status["standalone"] is False
    assert status["analyst_suite_module"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/correlation/status").status_code == 200
    resp = c.get(
        "/api/platform/intelligence-ledger/correlation"
        "?metric_a=price&metric_b=active_addresses&asset=BTC&window_days=30"
    )
    assert resp.status_code == 200
    assert resp.json()["correlation"]["no_causation_language"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/correlation_lead_lag_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 271
    assert seed["dependency_gate"]["data_engine_stable"] is True
