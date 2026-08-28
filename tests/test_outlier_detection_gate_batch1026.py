"""Tests — Outlier Detection Gate (#1026 Data Engine)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import multi_source_reconciliation as msr
from blackdark.data import outlier_detection_gate as odg


@pytest.fixture
def odg_seed() -> dict:
    return json.loads(Path("data/outlier_detection_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def msr_seed() -> dict:
    return json.loads(Path("data/multi_source_reconciliation_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    odg.reset_outlier_state()
    msr.reset_multi_source_state()
    yield
    odg.reset_outlier_state()
    msr.reset_multi_source_state()


def test_1026_status_no_standalone(odg_seed):
    status = odg.outlier_gate_status_1026(seed=odg_seed)
    assert status["standalone_rejected"] is True
    assert status["merged_into"] == "Data Engine"
    assert status["policy"]["fail_closed"] is True
    assert status["policy"]["no_ml_anomaly_detection_sprint_2"] is True


def test_price_bounds_configured(odg_seed):
    bounds = odg.outlier_gate_status_1026(seed=odg_seed)["bounds"]
    assert bounds["price"]["tolerance_pct"] == 5.0
    assert bounds["volume"]["sigma_threshold"] == 3.0
    assert bounds["onchain"]["tolerance_pct"] == 0.1


def test_normal_price_passes(odg_seed):
    result = odg.check_observation(
        data_type="price", source="binance", value=42100.0, symbol="BTC", seed=odg_seed
    )
    assert result["is_outlier"] is False
    assert result["badge"] is None


def test_price_outlier_detected(odg_seed):
    result = odg.check_observation(
        data_type="price", source="binance", value=50000.0, symbol="BTC", seed=odg_seed
    )
    assert result["is_outlier"] is True
    assert result["badge"] == "Outlier Detected / Data Degraded"


def test_volume_zscore_outlier(odg_seed):
    result = odg.check_observation(
        data_type="volume",
        source="coinmarketcap",
        value=3_000_000_000.0,
        symbol="BTC",
        seed=odg_seed,
    )
    assert result["is_outlier"] is True


def test_corroborated_event_not_outlier(odg_seed):
    result = odg.check_observation(
        data_type="price",
        source="binance",
        value=50000.0,
        symbol="BTC",
        observation={"source": "binance", "value": 50000.0, "corroborated_by_news": True},
        seed=odg_seed,
    )
    assert result["corroborated"] is True
    assert result["is_outlier"] is False
    assert result["badge"] == "Confirmed Event"


def test_cross_source_outlier_suppress_and_failover(odg_seed, msr_seed):
    gate = odg.apply_outlier_gate_to_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 50000.0, "ok": True},
            {"source": "coingecko", "value": 42100.0, "ok": True},
        ],
        symbol="BTC",
        seed=odg_seed,
    )
    assert gate["outlier_count"] == 1
    assert len(gate["failover_actions"]) >= 1

    reconciled = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": 50000.0, "ok": True},
            {"source": "coingecko", "value": 42100.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert reconciled["ok"] is True
    assert "outlier_gate" in reconciled


def test_fail_closed_response_gate(odg_seed):
    result = odg.apply_outlier_gate_to_response(
        result={"ok": True, "value": 50000.0, "status": "reconciled"},
        data_type="price",
        symbol="BTC",
        seed=odg_seed,
    )
    assert result["suppress_output"] is True
    assert result["badge"] == "Outlier Detected / Data Degraded"
    assert result["outlier_gate"]["fail_closed"] is True


def test_outlier_audit_trail(odg_seed):
    odg.apply_outlier_gate_to_observations(
        data_type="price",
        observations=[{"source": "binance", "value": 50000.0, "ok": True}],
        symbol="BTC",
        seed=odg_seed,
    )
    audit = odg.get_outlier_audit_trail()
    assert audit["count"] >= 1
    assert audit["append_only"] is True
    event = audit["audit_trail"][-1]
    assert "expected_range" in event
    assert "action_taken" in event


def test_production_gate(odg_seed):
    gate = odg.check_production_gate_1026(seed=odg_seed)
    assert gate["production_allowed"] is True
    assert gate["blocks_production"] is True


def test_z_score_method(odg_seed):
    result = odg.detect_outlier_zscore(value=3_000_000_000.0, mean=1_200_000_000.0, std=80_000_000.0)
    assert result["is_outlier"] is True


def test_iqr_method():
    values = [10.0, 11.0, 10.5, 10.2, 10.8, 200.0]
    result = odg.detect_outlier_iqr(values=values, value=200.0)
    assert result["is_outlier"] is True


def test_overhead_sla(odg_seed):
    result = odg.check_observation(
        data_type="price", source="binance", value=42100.0, symbol="BTC", seed=odg_seed
    )
    assert result["within_overhead_sla"] is True


def test_e2e_all_checks(odg_seed):
    e2e = odg.run_outlier_e2e_1026(seed=odg_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
