"""Tests — Batch: #832 Performance Validation Gate (REL-001 Sprint-0 Infrastructure)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infrastructure_performance_validation as perf


@pytest.fixture
def perf_seed() -> dict:
    return json.loads(
        Path("data/infrastructure_performance_validation_seed.json").read_text(encoding="utf-8")
    )


@pytest.fixture(autouse=True)
def reset_state():
    perf.reset_performance_validation_state()
    yield
    perf.reset_performance_validation_state()


def test_832_status_policy(perf_seed):
    status = perf.performance_validation_status_832(seed=perf_seed)
    assert status["standalone_rejected"] is True
    assert status["control_ref"] == "REL-001"
    assert status["sprint"] == 0
    policy = status["policy"]
    assert policy["tooling"]["primary"] == "k6"
    assert policy["no_theoretical_estimate"] is True
    assert policy["no_localhost_only"] is True
    assert policy["critical_systems_min"] == 6
    assert policy["scaling_stages"] == [10, 100, 500, 1000, 5000]
    assert policy["blocks_sprint_1"] is True


def test_832_k6_tooling_required(perf_seed):
    tooling = perf.get_load_test_tooling_832(seed=perf_seed)
    assert tooling["primary"] == "k6"
    assert tooling["no_manual_only"] is True
    assert tooling["no_theoretical_estimate"] is True
    assert "k6_performance_validation_gate.js" in tooling["scripts"]["k6"]


def test_832_six_critical_systems(perf_seed):
    endpoints = perf.get_critical_endpoints_832(seed=perf_seed)
    assert endpoints["meets_minimum"] is True
    assert endpoints["count"] == 6
    for key in (
        "oracle_api",
        "market_radar",
        "portfolio_ai",
        "intelligence_ledger",
        "stripe_webhook",
        "admin_panel",
    ):
        assert key in endpoints["systems"]


def test_832_curl_proofs_under_load(perf_seed):
    proofs = perf.get_curl_proofs_832(seed=perf_seed)
    assert proofs["tested_under_load"] is True
    assert proofs["slo_met_under_load"] is True
    assert len(proofs["proofs"]) == 8
    for proof_id in ("5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8"):
        assert proof_id in proofs["proofs"]
        assert proofs["proofs"][proof_id]["tested_under_load"] is True


def test_832_latency_slos(perf_seed):
    intel = perf.check_latency_slo_832("intelligence_ledger", p95_ms=420, seed=perf_seed)
    assert intel["limit_ms"] == 500
    assert intel["slo_met"] is True

    radar = perf.check_latency_slo_832("market_radar", p95_ms=1800, seed=perf_seed)
    assert radar["limit_ms"] == 2000
    assert radar["slo_met"] is True

    over = perf.check_latency_slo_832("intelligence_ledger", p95_ms=512, seed=perf_seed)
    assert over["slo_met"] is False


def test_832_scaling_stages(perf_seed):
    scaling = perf.get_scaling_stages_832(seed=perf_seed)
    assert scaling["stages"] == [10, 100, 500, 1000, 5000]
    triggers = scaling["degradation_triggers"]
    assert "latency_degradation_gt_2x_baseline" in triggers
    assert "error_rate_gt_1_percent" in triggers


def test_832_exact_degradation_numbers(perf_seed):
    report = perf.get_degradation_report_832(seed=perf_seed)
    assert report["exact_numbers"] is True
    assert report["no_rounded_estimates"] is True
    findings = report["examples"]
    assert len(findings) >= 1
    market = next(f for f in findings if "market-radar" in f["endpoint"])
    assert market["concurrent_users"] == 1847
    assert "1,847" in market["statement"]


def test_832_sprint1_gate(perf_seed):
    gate = perf.check_sprint1_gate_832(seed=perf_seed)
    assert gate["blocks_sprint_1"] is True
    assert gate["all_passed"] is True
    assert gate["sprint_1_allowed"] is True
    assert "data_engine" in gate["prerequisites"]
    assert "oracle_api" in gate["prerequisites"]


def test_832_record_load_test_run(perf_seed):
    run = perf.record_load_test_run_832(
        environment="production_off_peak",
        concurrent_users=1000,
        endpoint="/api/oracle/price",
        metrics={"p95_ms": 156.2, "error_rate_pct": 0.0, "throughput_rps": 2847.1},
        passed=True,
        seed=perf_seed,
    )
    assert run["ok"] is True
    assert run["run"]["tooling"] == "k6"
    assert run["run"]["audit_logged"] is True


def test_832_incident_on_failure(perf_seed):
    trigger = perf.trigger_incident_on_failure_832(
        endpoint="/api/market-radar/snapshot",
        concurrent_users=1847,
        error_rate=1.2,
        seed=perf_seed,
    )
    assert trigger["incident_triggered"] is True
    assert trigger["auto_alert_ops"] is True
    assert trigger["incident_response_ref"] == 829


def test_832_failed_run_triggers_incident(perf_seed):
    result = perf.record_load_test_run_832(
        environment="production_off_peak",
        concurrent_users=5000,
        endpoint="/api/billing/stripe/webhook",
        metrics={"p95_ms": 248.0, "error_rate_pct": 1.03},
        passed=False,
        seed=perf_seed,
    )
    assert result["ok"] is False


def test_832_signed_evidence(perf_seed):
    evidence = perf.get_signed_load_evidence_832(seed=perf_seed)
    assert evidence["ok"] is True
    assert evidence["production_like"] is True
    artifact = evidence.get("artifact") or {}
    assert artifact.get("p95_ms") == 143.4 or artifact.get("gate") == "CAP-644"


def test_832_billing_and_session_integrations(perf_seed):
    assert perf_seed["billing_under_load"]["no_billing_corruption"] is True
    assert perf_seed["billing_under_load"]["idempotency_tested"] is True
    assert perf_seed["session_under_load"]["no_race_condition"] is True


def test_832_e2e_all_checks(perf_seed):
    e2e = perf.run_performance_validation_e2e_832(seed=perf_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed checks: {failed}"
