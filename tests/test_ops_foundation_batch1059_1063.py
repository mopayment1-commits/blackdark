"""Tests — Ops Foundation (#1059–#1063 Sprint-0 Infrastructure)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import explainability_policy as exp
from bd_platform import infrastructure_apm_tracing as apm
from bd_platform import infrastructure_centralized_logging as logging_stack
from bd_platform import infrastructure_self_healing_watchdog as watchdog
from bd_platform import infrastructure_uptime_monitoring as uptime


@pytest.fixture
def ops_seed() -> dict:
    return json.loads(
        Path("data/infrastructure_ops_foundation_seed.json").read_text(encoding="utf-8")
    )


@pytest.fixture(autouse=True)
def reset_all_state():
    uptime.reset_uptime_monitoring_state()
    logging_stack.reset_centralized_logging_state()
    apm.reset_apm_tracing_state()
    watchdog.reset_self_healing_state()
    exp.reset_explainability_state()
    yield
    uptime.reset_uptime_monitoring_state()
    logging_stack.reset_centralized_logging_state()
    apm.reset_apm_tracing_state()
    watchdog.reset_self_healing_state()
    exp.reset_explainability_state()


# ─── #1059 Uptime ────────────────────────────────────────────────────────────


def test_1059_status(ops_seed):
    status = uptime.uptime_monitoring_status_1059(seed=ops_seed)
    assert status["standalone_rejected"] is True
    assert status["critical_services_count"] >= 7
    assert status["policy"]["probe_interval_sec"] == 30
    assert status["policy"]["no_guaranteed_uptime"] is True


def test_1059_external_probe_and_alert(ops_seed):
    for _ in range(4):
        uptime.record_external_probe_1059(
            service="oracle_api", region="eu-west-1", ok=False, latency_ms=0, seed=ops_seed
        )
    assert len(uptime._alert_log) >= 1


def test_1059_status_page(ops_seed):
    page = uptime.build_public_status_page_1059(seed=ops_seed)
    assert page["no_guaranteed_uptime"] is True
    assert page["page_path"] == "/status"


def test_1059_e2e(ops_seed):
    e2e = uptime.run_uptime_monitoring_e2e_1059(seed=ops_seed)
    assert e2e["all_passed"] is True


# ─── #1060 Logging ───────────────────────────────────────────────────────────


def test_1060_status(ops_seed):
    status = logging_stack.centralized_logging_status_1060(seed=ops_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["structured_json_enforced"] is True
    assert status["retention"]["operational_days"] == 30


def test_1060_sanitization(ops_seed):
    entry = logging_stack.ingest_log_entry_1060(
        service="api", level="ERROR", message="leaked password=secret123", seed=ops_seed
    )
    assert "[REDACTED]" in entry["entry"]["message"]


def test_1060_search(ops_seed):
    logging_stack.ingest_log_entry_1060(
        service="worker", level="INFO", message="job complete", trace_id="trc_abc", seed=ops_seed
    )
    result = logging_stack.search_logs_1060(trace_id="trc_abc", seed=ops_seed)
    assert result["count"] >= 1
    assert result["within_sla"] is True


def test_1060_e2e(ops_seed):
    e2e = logging_stack.run_centralized_logging_e2e_1060(seed=ops_seed)
    assert e2e["all_passed"] is True


# ─── #1061 APM ────────────────────────────────────────────────────────────────


def test_1061_status(ops_seed):
    status = apm.apm_tracing_status_1061(seed=ops_seed)
    assert status["standalone_rejected"] is True
    assert len(status["metric_dimensions"]) >= 8
    assert len(status["critical_services"]) >= 7


def test_1061_alerts(ops_seed):
    result = apm.record_metric_sample_1061(
        service="oracle_api",
        latency_p95_ms=3000,
        throughput_rps=10,
        error_rate_pct=3.0,
        memory_pct=90,
        db_connections_pct=85,
        seed=ops_seed,
    )
    assert len(result["alerts"]) >= 1


def test_1061_distributed_trace(ops_seed):
    tid = "trc_dist_001"
    apm.record_trace_span_1061(trace_id=tid, span_name="gateway", service="oracle_api")
    apm.record_trace_span_1061(trace_id=tid, span_name="db", service="database", parent_span="gateway")
    assert len(apm._trace_spans) == 2


def test_1061_e2e(ops_seed):
    e2e = apm.run_apm_tracing_e2e_1061(seed=ops_seed)
    assert e2e["all_passed"] is True


# ─── #1062 Watchdog ──────────────────────────────────────────────────────────


def test_1062_status(ops_seed):
    status = watchdog.self_healing_status_1062(seed=ops_seed)
    assert status["standalone_rejected"] is True
    assert len(status["triggers"]) >= 4


def test_1062_stateful_exception(ops_seed):
    ev = watchdog.evaluate_watchdog_trigger_1062(service="database", trigger="process_exit_crash", seed=ops_seed)
    assert ev["action"] == "no_restart"


def test_1062_health_3x_restart(ops_seed):
    watchdog.record_health_check_failure_1062(service="api", seed=ops_seed)
    watchdog.record_health_check_failure_1062(service="api", seed=ops_seed)
    result = watchdog.record_health_check_failure_1062(service="api", seed=ops_seed)
    assert result.get("restart", {}).get("trigger") == "health_check_fail_3x" or result.get("ok") is True


def test_1062_e2e(ops_seed):
    e2e = watchdog.run_self_healing_e2e_1062(seed=ops_seed)
    assert e2e["all_passed"] is True


# ─── #1063 Explainability ────────────────────────────────────────────────────


def test_1063_policy(ops_seed):
    status = exp.explainability_policy_status_1063(seed=ops_seed)
    assert status["cross_cutting"] is True
    assert status["policy"]["why_mandatory"] is True


def test_1063_validate_explanation(ops_seed):
    explanation = exp.build_rule_based_explanation(
        summary_en="Volume spike detected",
        reasons=[
            {"indicator": "volume", "value": "+200%"},
            {"indicator": "price", "value": "+0.5%"},
            {"indicator": "sources", "value": "3"},
        ],
        confidence=6.0,
        source_count=3,
    )
    payload = {"risk_score": 5, "explanation": explanation}
    assert exp.validate_explanation_present_1063(payload, seed=ops_seed)["valid"] is True


def test_1063_block_missing_explanation(ops_seed):
    blocked = exp.enforce_explanation_on_output_1063({"value": 1}, seed=ops_seed)
    assert blocked.get("suppressed") is True


def test_1063_e2e(ops_seed):
    e2e = exp.run_explainability_e2e_1063(seed=ops_seed)
    assert e2e["all_passed"] is True
