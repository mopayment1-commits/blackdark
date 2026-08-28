"""Tests — Live Feed Statistical Monitor (#1054 inside #1026)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import live_feed_statistical_monitor as lfsm
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
    lfsm.reset_live_feed_anomaly_state()
    odg.reset_outlier_state()
    msr.reset_multi_source_state()
    yield
    lfsm.reset_live_feed_anomaly_state()
    odg.reset_outlier_state()
    msr.reset_multi_source_state()


def test_1054_status_merged_into_1026(odg_seed):
    status = lfsm.live_feed_anomaly_status_1054(seed=odg_seed)
    assert status["standalone_rejected"] is True
    assert status["merged_into"] == "#1026 Outlier Detection Gate"
    assert status["policy"]["not_confirmed_attack"] is True
    assert len(status["patterns"]) == 4


def test_cross_metric_divergence(odg_seed):
    result = lfsm.evaluate_live_feed_tick(
        metric="BTC",
        source="binance",
        price_change_pct=5.0,
        volume_change_pct=-10.0,
        seed=odg_seed,
    )
    assert result["anomaly_detected"] is True
    assert "cross_metric_divergence" in result["patterns"]
    assert result["confirmed_attack"] is False
    assert "Under Review" in (result.get("badge") or "")


def test_volume_burst_after_warmup(odg_seed):
    for i in range(12):
        lfsm.evaluate_live_feed_tick(
            metric="BTC", source="binance", volume=1_000_000_000.0 + i * 1e6, seed=odg_seed
        )
    result = lfsm.evaluate_live_feed_tick(
        metric="BTC",
        source="binance",
        volume=5_000_000_000.0,
        price_change_pct=0.1,
        seed=odg_seed,
    )
    assert result["anomaly_detected"] is True
    assert "volume_burst" in result["patterns"]


def test_source_drift_in_batch(odg_seed):
    monitor = lfsm.apply_anomaly_monitor_to_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 43500.0, "ok": True},
            {"source": "coingecko", "value": 42000.0, "ok": True},
        ],
        symbol="BTC",
        seed=odg_seed,
    )
    assert monitor["monitor_applied"] is True
    assert monitor["within_latency_sla"] is True


def test_fail_closed_suppresses_anomaly_observation(odg_seed):
    monitor = lfsm.apply_anomaly_monitor_to_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 43500.0, "ok": True},
            {"source": "coingecko", "value": 42000.0, "ok": True},
        ],
        symbol="BTC",
        seed=odg_seed,
    )
    suppressed = [o for o in monitor["clean"] if o.get("anomaly_suppressed")]
    if monitor["anomaly_count"] > 0:
        assert any(o.get("data_degraded") for o in suppressed)


def test_outlier_gate_runs_anomaly_first(odg_seed, msr_seed):
    gate = odg.apply_outlier_gate_to_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 50000.0, "ok": True},
            {"source": "coingecko", "value": 42100.0, "ok": True},
        ],
        symbol="BTC",
        seed=odg_seed,
    )
    assert gate["gate_applied"] is True
    assert "anomaly_monitor" in gate


def test_anomaly_audit_trail(odg_seed):
    lfsm.evaluate_live_feed_tick(
        metric="BTC",
        source="binance",
        price_change_pct=5.0,
        volume_change_pct=-10.0,
        seed=odg_seed,
    )
    audit = lfsm.get_anomaly_audit_trail()
    assert audit["count"] >= 1
    assert audit["append_only"] is True
    event = audit["audit_trail"][-1]
    assert event["confirmed_attack"] is False
    assert "fee_db" in event


def test_e2e_all_checks(odg_seed):
    e2e = lfsm.run_live_feed_anomaly_e2e_1054(seed=odg_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
