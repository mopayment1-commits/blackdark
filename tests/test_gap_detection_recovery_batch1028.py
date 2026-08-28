"""Tests — Gap Detection & Recovery Engine (#1028 Data Engine)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from blackdark.data import gap_detection_recovery_engine as gdr
from blackdark.data import multi_source_reconciliation as msr


@pytest.fixture
def gdr_seed() -> dict:
    return json.loads(Path("data/gap_detection_recovery_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def msr_seed() -> dict:
    return json.loads(Path("data/multi_source_reconciliation_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    gdr.reset_gap_recovery_state()
    msr.reset_multi_source_state()
    yield
    gdr.reset_gap_recovery_state()
    msr.reset_multi_source_state()


def test_1028_status_no_standalone(gdr_seed):
    status = gdr.gap_recovery_status_1028(seed=gdr_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["no_silent_gaps"] is True
    assert status["policy"]["rule_based_only"] is True


def test_expected_intervals(gdr_seed):
    assert gdr.expected_interval_seconds("price", seed=gdr_seed) == 300.0
    assert gdr.expected_interval_seconds("volume", seed=gdr_seed) == 3600.0
    assert gdr.expected_interval_seconds("onchain", seed=gdr_seed) == 12.0


def test_detect_price_gap(gdr_seed):
    base = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    timeseries = [
        {"timestamp_utc": base.isoformat(), "value": 42000.0, "source": "binance"},
        {"timestamp_utc": (base + timedelta(minutes=10)).isoformat(), "value": 42100.0, "source": "binance"},
    ]
    result = gdr.detect_gaps(data_type="price", timeseries=timeseries, seed=gdr_seed)
    assert result["gaps_detected"] == 1
    assert result["gaps"][0]["duration_seconds"] == 600.0


def test_no_gap_within_interval(gdr_seed):
    base = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    timeseries = [
        {"timestamp_utc": base.isoformat(), "value": 42000.0, "source": "binance"},
        {"timestamp_utc": (base + timedelta(minutes=3)).isoformat(), "value": 42100.0, "source": "binance"},
    ]
    result = gdr.detect_gaps(data_type="price", timeseries=timeseries, seed=gdr_seed)
    assert result["gaps_detected"] == 0


def test_backfill_recovery(gdr_seed):
    result = gdr.attempt_backfill(
        data_type="price",
        gap_start="2026-08-28T12:00:00+00:00",
        gap_end="2026-08-28T12:10:00+00:00",
        failed_source="binance",
        seed=gdr_seed,
    )
    assert result["recovered"] is True
    assert "Recovered from" in result["badge"]
    assert result["confidence"] == "Medium"


def test_explicit_gap_label(gdr_seed):
    result = gdr.label_explicit_gap(
        data_type="price",
        gap_start="2026-08-28T12:00:00+00:00",
        gap_end="2026-08-28T12:10:00+00:00",
        sources_attempted=["coingecko"],
        seed=gdr_seed,
    )
    assert result["badge"] == "Data Gap"
    assert result["display"] == "N/A"
    assert result["suppress_silent_null"] is True


def test_recover_timeseries(gdr_seed):
    base = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    timeseries = [
        {"timestamp_utc": base.isoformat(), "value": 42000.0, "source": "binance"},
        {"timestamp_utc": (base + timedelta(minutes=10)).isoformat(), "value": 42100.0, "source": "binance"},
    ]
    result = gdr.recover_timeseries(data_type="price", timeseries=timeseries, seed=gdr_seed)
    assert result["recovered_count"] >= 1
    assert "detect_gap" in result["pipeline_steps_completed"]


def test_apply_gap_recovery_to_observations(gdr_seed):
    result = gdr.apply_gap_recovery_to_observations(
        data_type="price",
        observations=[{"source": "binance", "value": None, "ok": False}],
        seed=gdr_seed,
    )
    assert result["gate_applied"] is True
    assert result["observations"][0]["recovered"] is True
    assert result["next_step"] == "normalize"


def test_pipeline_integration(gdr_seed, msr_seed):
    result = msr.reconcile_price(
        observations=[
            {"source": "binance", "value": None, "ok": False},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert "gap_recovery" in result


def test_provenance_fields(gdr_seed):
    prov = gdr.build_gap_provenance(
        gap_start="2026-08-28T12:00:00+00:00",
        gap_end="2026-08-28T12:05:00+00:00",
        sources_attempted=["binance", "coingecko"],
        recovery_status="recovered",
        recovered_from="coingecko",
    )
    assert prov["provenance_ref"] == 945
    assert "Gap:" in prov["tag"]
    assert prov["pit_immutable"] is True


def test_gap_audit_trail(gdr_seed):
    gdr.attempt_backfill(
        data_type="price",
        gap_start="2026-08-28T12:00:00+00:00",
        gap_end="2026-08-28T12:10:00+00:00",
        failed_source="binance",
        seed=gdr_seed,
    )
    audit = gdr.get_gap_audit_trail()
    assert audit["count"] >= 1
    assert audit["append_only"] is True


def test_production_gate(gdr_seed):
    gate = gdr.check_production_gate_1028(seed=gdr_seed)
    assert gate["production_allowed"] is True
    assert gate["blocks_production"] is True


def test_e2e_all_checks(gdr_seed):
    e2e = gdr.run_gap_recovery_e2e_1028(seed=gdr_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
