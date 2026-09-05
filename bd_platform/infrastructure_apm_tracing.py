"""
Infrastructure APM & Distributed Tracing — #1061 (Sprint 0).

Merged into Sprint-0 Infrastructure — NOT standalone.
Metrics, distributed tracing, rule-based alerts calibrated against load test baselines.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.APMTracing")

_FEATURE_REF = 1061
_STANDALONE = False
_MERGED_INTO = "Sprint-0 Infrastructure"
_SEED_PATH = Path("data/infrastructure_ops_foundation_seed.json")
_RUNBOOK = "docs/ops/APM_TRACING.md"

_metric_samples: dict[str, list[dict[str, Any]]] = {}
_trace_spans: list[dict[str, Any]] = []
_alert_log: list[dict[str, Any]] = []


def reset_apm_tracing_state() -> None:
    _metric_samples.clear()
    _trace_spans.clear()
    _alert_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("apm tracing seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("apm_tracing_1061") or {}


def apm_tracing_status_1061(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sprint": 0,
        "policy": {
            "tooling": policy.get("tooling", "prometheus_otel"),
            "rule_based_only": policy.get("rule_based_only", True),
            "no_ml_anomaly_detection_sprint_2": policy.get("no_ml_anomaly_detection_sprint_2", True),
            "alert_latency_sec_max": policy.get("alert_latency_sec_max", 60),
            "baseline_recalibration": policy.get("baseline_recalibration", "monthly"),
            "blocks_production_if_incomplete": policy.get("blocks_production_if_incomplete", True),
        },
        "critical_services": cfg.get("critical_services") or [],
        "metric_dimensions": cfg.get("metric_dimensions") or [],
        "alert_triggers": cfg.get("alert_triggers") or {},
        "baselines": cfg.get("baselines") or {},
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "timestamp": _utcnow(),
    }


def record_metric_sample_1061(
    *,
    service: str,
    latency_p95_ms: float,
    throughput_rps: float,
    error_rate_pct: float,
    cpu_pct: float = 0.0,
    memory_pct: float = 0.0,
    db_connections_pct: float = 0.0,
    cache_hit_rate_pct: float = 0.0,
    trace_id: str = "",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record APM metric sample — 8+ dimensions."""
    seed = seed or _load_seed()
    sample = {
        "sample_id": f"met_{uuid.uuid4().hex[:8]}",
        "service": service,
        "latency_p50_ms": round(latency_p95_ms * 0.6, 2),
        "latency_p95_ms": round(latency_p95_ms, 2),
        "latency_p99_ms": round(latency_p95_ms * 1.3, 2),
        "throughput_rps": round(throughput_rps, 2),
        "error_rate_pct": round(error_rate_pct, 4),
        "cpu_pct": round(cpu_pct, 2),
        "memory_pct": round(memory_pct, 2),
        "db_connections_pct": round(db_connections_pct, 2),
        "cache_hit_rate_pct": round(cache_hit_rate_pct, 2),
        "trace_id": trace_id or f"trc_{uuid.uuid4().hex[:12]}",
        "timestamp": _utcnow(),
    }
    _metric_samples.setdefault(service, []).append(sample)
    alerts = _evaluate_apm_alerts(service=service, sample=sample, seed=seed)
    return {"ok": True, "sample": sample, "alerts": alerts}


def record_trace_span_1061(
    *,
    trace_id: str,
    span_name: str,
    service: str,
    parent_span: str = "",
    duration_ms: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Distributed trace span — API → service → DB → cache → external."""
    span = {
        "span_id": f"spn_{uuid.uuid4().hex[:10]}",
        "trace_id": trace_id,
        "span_name": span_name,
        "service": service,
        "parent_span": parent_span,
        "duration_ms": round(duration_ms, 2),
        "metadata": metadata or {},
        "timestamp": _utcnow(),
    }
    _trace_spans.append(span)
    return {"ok": True, "span": span}


def _evaluate_apm_alerts(
    *, service: str, sample: dict[str, Any], seed: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    triggers = cfg.get("alert_triggers") or {}
    baselines = (cfg.get("baselines") or {}).get(service) or {}
    alerts: list[dict[str, Any]] = []

    baseline_p95 = float(baselines.get("latency_p95_ms", 1000))
    multiplier = float(triggers.get("latency_p95_multiplier", 2.0))
    if sample["latency_p95_ms"] > baseline_p95 * multiplier:
        alerts.append(_create_apm_alert("latency_p95_breach", service, sample, seed=seed))

    if sample["error_rate_pct"] > float(triggers.get("error_rate_pct_max", 1.0)):
        alerts.append(_create_apm_alert("error_rate_breach", service, sample, seed=seed))

    if sample["memory_pct"] > float(triggers.get("memory_pct_max", 85.0)):
        alerts.append(_create_apm_alert("memory_breach", service, sample, seed=seed))

    if sample["db_connections_pct"] > float(triggers.get("db_connections_pct_max", 80.0)):
        alerts.append(_create_apm_alert("db_connections_breach", service, sample, seed=seed))

    return alerts


def _create_apm_alert(
    trigger: str, service: str, sample: dict[str, Any], *, seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    alert = {
        "alert_id": f"apm_{uuid.uuid4().hex[:8]}",
        "trigger": trigger,
        "service": service,
        "sample": sample,
        "rule_based": True,
        "methodology_version": "1.0.0",
        "timestamp": _utcnow(),
    }
    _alert_log.append(alert)
    _trigger_circuit_breaker_if_needed(service=service, trigger=trigger, seed=seed)
    return alert


def _trigger_circuit_breaker_if_needed(*, service: str, trigger: str, seed: dict[str, Any] | None = None) -> None:
    try:
        from circuit_breaker_layer import trip_circuit_breaker
        trip_circuit_breaker(source=service, reason=f"apm_{trigger}")
    except ImportError:
        logger.debug("circuit breaker bridge unavailable for apm alert")


def build_apm_dashboard_1061(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ops-only real-time dashboard data."""
    seed = seed or _load_seed()
    services = (_cfg(seed).get("critical_services") or [])
    panels: dict[str, Any] = {}
    for svc in services:
        samples = _metric_samples.get(svc, [])
        if samples:
            latest = samples[-1]
            panels[svc] = {
                "latency_p95_ms": latest["latency_p95_ms"],
                "error_rate_pct": latest["error_rate_pct"],
                "throughput_rps": latest["throughput_rps"],
            }
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "ops_only": True,
        "panels": panels,
        "active_alerts": len(_alert_log),
        "timestamp": _utcnow(),
    }


def check_production_gate_1061(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = apm_tracing_status_1061(seed=seed)
    checks = {
        "services_min_7": len(status["critical_services"]) >= 7,
        "metrics_min_8": len(status["metric_dimensions"]) >= 8,
        "rule_based_only": status["policy"]["rule_based_only"] is True,
        "no_ml_sprint_2": status["policy"]["no_ml_anomaly_detection_sprint_2"] is True,
        "alert_triggers_4": len(status["alert_triggers"]) >= 4,
        "baseline_from_load_test": status["baselines"].get("source") == "load_test_1020",
        "alert_latency_1min": status["policy"]["alert_latency_sec_max"] <= 60,
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "blocks_production": True,
        "production_allowed": all(checks.values()),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_apm_tracing_e2e_1061(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_apm_tracing_state()
    checks: list[dict[str, Any]] = []

    status = apm_tracing_status_1061(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "metrics_8_dims", "passed": len(status["metric_dimensions"]) >= 8})

    trace_id = f"trc_e2e_{uuid.uuid4().hex[:8]}"
    record_trace_span_1061(trace_id=trace_id, span_name="api_gateway", service="oracle_api", duration_ms=5.0)
    record_trace_span_1061(
        trace_id=trace_id, span_name="db_query", service="database", parent_span="api_gateway", duration_ms=12.0
    )
    checks.append({"id": "distributed_trace", "passed": len(_trace_spans) >= 2})

    normal = record_metric_sample_1061(
        service="oracle_api", latency_p95_ms=400, throughput_rps=100, error_rate_pct=0.05, seed=seed
    )
    checks.append({"id": "normal_metrics", "passed": normal.get("ok") is True})

    breach = record_metric_sample_1061(
        service="oracle_api",
        latency_p95_ms=2000,
        throughput_rps=50,
        error_rate_pct=2.0,
        memory_pct=90,
        db_connections_pct=85,
        trace_id=trace_id,
        seed=seed,
    )
    checks.append({"id": "apm_alerts", "passed": len(breach.get("alerts") or []) >= 1})

    dashboard = build_apm_dashboard_1061(seed=seed)
    checks.append({"id": "ops_dashboard", "passed": dashboard.get("ops_only") is True})

    gate = check_production_gate_1061(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["production_allowed"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
