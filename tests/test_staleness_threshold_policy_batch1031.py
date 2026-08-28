"""Tests — Staleness Threshold Policy Engine (#1031)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import blackdark.data.multi_source_reconciliation as msr
from bd_platform.staleness_threshold_policy_engine import (
    apply_staleness_to_freshness_badge,
    check_production_gate_1031,
    dispatch_internal_alert,
    evaluate_and_attach_freshness,
    evaluate_staleness,
    get_staleness_audit_trail,
    get_threshold_seconds,
    normalize_tier_name,
    reset_staleness_policy_state,
    run_health_check_cycle,
    run_staleness_policy_e2e_1031,
    staleness_policy_status_1031,
)


@pytest.fixture
def msr_seed() -> dict:
    return json.loads(Path("data/multi_source_reconciliation_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def st_seed() -> dict:
    return json.loads(Path("data/staleness_threshold_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset_state():
    reset_staleness_policy_state()
    msr.reset_multi_source_state()
    yield
    reset_staleness_policy_state()
    msr.reset_multi_source_state()


def test_1031_status_no_standalone(st_seed):
    status = staleness_policy_status_1031(seed=st_seed)
    assert status["standalone_rejected"] is True
    assert status["feature_ref"] == 1031
    assert status["thresholds_seconds"]["price"] == 300


def test_thresholds_per_source(st_seed):
    assert get_threshold_seconds("price", seed=st_seed) == 300.0
    assert get_threshold_seconds("volume", seed=st_seed) == 3600.0
    assert get_threshold_seconds("onchain", seed=st_seed) == 12.0
    assert get_threshold_seconds("governance", seed=st_seed) == 86400.0
    assert get_threshold_seconds("news", seed=st_seed) == 1800.0


def test_tier_multipliers(st_seed):
    assert get_threshold_seconds("price", tier="free", seed=st_seed) > 300.0
    assert get_threshold_seconds("price", tier="pro", seed=st_seed) < 300.0
    assert get_threshold_seconds("price", tier="institution", seed=st_seed) < 300.0
    assert normalize_tier_name("enterprise") == "institution"


def test_breach_dispatches_internal_alert(st_seed):
    ev = evaluate_staleness(source_id="binance", category="price", delay_seconds=400, seed=st_seed)
    assert ev["breached"] is True
    assert ev["alert_dispatched"] is True
    assert ev["freshness_score"] == "Degraded"
    assert ev["internal_alert"]["user_facing"] is False
    assert ev["fee_db"]["fee_db_logged"] is True


def test_escalation_freshness_failed_at_2x(st_seed):
    ev = evaluate_staleness(source_id="binance", category="price", delay_seconds=650, seed=st_seed)
    assert ev["freshness_score"] == "Failed"
    assert ev["incident_escalation"] is not None


def test_outlier_combined_data_compromised(st_seed):
    ev = evaluate_staleness(
        source_id="binance",
        category="price",
        delay_seconds=400,
        outlier_detected=True,
        seed=st_seed,
    )
    assert ev["data_compromised"] is True
    assert ev["suppress_display"] is True


def test_gap_triggers_backfill_priority(st_seed):
    ev = evaluate_staleness(
        source_id="binance",
        category="price",
        delay_seconds=400,
        gap_detected=True,
        seed=st_seed,
    )
    assert ev["gap_recovery_priority"] == "backfill_prioritized"


def test_health_check_no_silent_degradation(st_seed):
    cycle = run_health_check_cycle(
        [{"source_id": "binance", "category": "price", "delay_seconds": 400}],
        seed=st_seed,
    )
    assert cycle["breaches"] == 1
    assert cycle["breaches_without_alert"] == 0
    assert cycle["silent_degradation_failure"] is False


def test_apply_staleness_updates_badge(st_seed):
    freshness = {"state": "Live", "badge": {"state": "Live", "label": "Live"}}
    ev = evaluate_staleness(source_id="binance", category="price", delay_seconds=400, seed=st_seed)
    updated = apply_staleness_to_freshness_badge(freshness, ev)
    assert updated["state"] == "Delayed"
    assert updated["badge"]["label"] == "Delayed"


def test_evaluate_and_attach_freshness(st_seed):
    out = evaluate_and_attach_freshness(
        {"value": 42000, "timestamp": "2026-08-28T12:00:00+00:00"},
        source_id="binance",
        category="price",
        delay_seconds=400,
        seed=st_seed,
    )
    assert out["staleness"]["breached"] is True
    assert out["provenance_freshness_score"] == "Degraded"
    assert out["freshness"]["state"] == "Delayed"


def test_audit_trail(st_seed):
    dispatch_internal_alert(
        source_id="binance",
        category="price",
        delay_seconds=400,
        threshold_seconds=300,
        breach_multiplier=1.33,
        seed=st_seed,
    )
    trail = get_staleness_audit_trail()
    assert trail["alerts_count"] >= 1
    assert trail["append_only"] is True


def test_production_gate(st_seed):
    gate = check_production_gate_1031(seed=st_seed)
    assert gate["definitions_ready"] is True
    assert gate["checks"]["thresholds_defined"] is True


def test_e2e_1031(st_seed):
    result = run_staleness_policy_e2e_1031(seed=st_seed)
    assert result["all_passed"] is True
    assert result["ok"] is True


def test_reconcile_price_includes_staleness(msr_seed):
    result = msr.reconcile_price(
        symbol="BTC",
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=msr_seed,
    )
    assert "freshness" in result
    assert "staleness" in result
    assert "breached" in result["staleness"]
