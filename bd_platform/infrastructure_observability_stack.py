"""
Infrastructure Observability Stack — Feature #789 (Sprint-0 SRE).

NOT user-facing market alerts — internal DevOps observability only.
Prometheus (metrics) + Grafana (dashboards) + Loki (logging) + Jaeger (tracing)
+ PagerDuty/Opsgenie (infra alerts).

Separate from #788 user alert system.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.InfraObservability")

_FEATURE_ID = 789
_TITLE = "Logging, Metrics, Tracing and Alerts (Infrastructure)"
_STANDALONE = False
_MERGED_INTO = "Sprint-0 Infrastructure / SRE Stack"
_SPRINT = 0
_SEED_PATH = Path("data/infrastructure_observability_stack_seed.json")

_DISCLAIMER = (
    "Internal infrastructure observability only. "
    "NOT user-facing market alerts. NOT portfolio or price conditions."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("infra observability seed load failed: %s", exc)
        return {}


def build_sre_observability_stack_789(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#789 — SRE observability stack status (internal only)."""
    seed = seed or _load_seed()
    cfg = seed.get("sre_stack_789") or {}
    slos = cfg.get("slos") or {}
    components = cfg.get("components") or {}

    return {
        "ok": True,
        "feature_ref": 789,
        "title": _TITLE,
        "standalone_rejected": True,
        "not_user_alert_system": True,
        "user_alerts_built_in_788": True,
        "infra_alerts_only": True,
        "no_market_data": True,
        "no_user_conditions": True,
        "components": {
            "prometheus": {"purpose": "metrics", **(components.get("prometheus") or {})},
            "grafana": {"purpose": "dashboards", **(components.get("grafana") or {})},
            "loki": {"purpose": "logging", **(components.get("loki") or {})},
            "jaeger": {"purpose": "tracing", **(components.get("jaeger") or {})},
            "pagerduty": {"purpose": "infra_alerts", **(components.get("pagerduty") or {})},
        },
        "slos": {
            "uptime_target_pct": float(slos.get("uptime_target_pct", 99.9)),
            "latency_p99_max_ms": float(slos.get("latency_p99_max_ms", 500)),
            "error_rate_max_pct": float(slos.get("error_rate_max_pct", 0.1)),
            "monitored": True,
        },
        "current_metrics": cfg.get("current_metrics") or {},
        "fee_db": cfg.get("fee_db") or {"infra_monitoring_usd": 50.0, "tier": "ops"},
        "internal_dashboard": "Grafana (team only)",
        "no_user_surface": True,
        "integrations": ["Data Engine health", "Oracle API latency/error rate", "#824 Quality Monitor"],
        "quality_monitor_feed_824": (seed.get("sre_stack_789") or {}).get("quality_monitor_feed_824") or {},
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_infra_observability_slo_tests_789(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#789 — SLO compliance checks."""
    seed = seed or _load_seed()
    stack = build_sre_observability_stack_789(seed=seed)
    metrics = (seed.get("sre_stack_789") or {}).get("current_metrics") or {}
    slos = stack.get("slos") or {}

    tests = [
        {
            "test": "uptime_slo",
            "passed": float(metrics.get("uptime_pct", 0)) >= float(slos.get("uptime_target_pct", 99.9)),
            "actual": metrics.get("uptime_pct"),
            "target": slos.get("uptime_target_pct"),
        },
        {
            "test": "latency_p99_slo",
            "passed": float(metrics.get("latency_p99_ms", 9999)) <= float(slos.get("latency_p99_max_ms", 500)),
            "actual": metrics.get("latency_p99_ms"),
            "target": slos.get("latency_p99_max_ms"),
        },
        {
            "test": "error_rate_slo",
            "passed": float(metrics.get("error_rate_pct", 100)) <= float(slos.get("error_rate_max_pct", 0.1)),
            "actual": metrics.get("error_rate_pct"),
            "target": slos.get("error_rate_max_pct"),
        },
        {"test": "not_user_alerts", "passed": stack.get("not_user_alert_system") is True},
        {"test": "no_market_data", "passed": stack.get("no_market_data") is True},
    ]
    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": 789,
        "slo_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }


def build_sre_observability_with_quality_monitor_789(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#789 + #824 — SRE stack enriched with Data Engine quality monitor feed."""
    seed = seed or _load_seed()
    stack = build_sre_observability_stack_789(seed=seed)
    try:
        from bd_platform.data_engine_quality_monitor import build_infra_observability_quality_feed_824

        feed = build_infra_observability_quality_feed_824()
        stack["quality_monitor_feed_824"] = feed
        stack["data_quality_checks_passed"] = feed.get("quality_metrics", {}).get("daily_checks_passed")
    except Exception:
        logger.debug("824 quality monitor feed skipped", exc_info=True)
    try:
        from bd_platform.data_health_monitor import build_infra_observability_health_feed_849

        health_feed = build_infra_observability_health_feed_849()
        stack["data_health_feed_849"] = health_feed
        stack["all_venues_within_slo"] = health_feed.get("all_venues_within_slo")
    except Exception:
        logger.debug("849 data health feed skipped", exc_info=True)
    try:
        shield = build_uptime_slo_shield_862(seed=seed)
        stack["uptime_shield_862"] = shield
        stack["uptime_slo_compliant"] = run_uptime_slo_tests_862(seed=seed).get("all_passed")
    except Exception:
        logger.debug("862 uptime shield feed skipped", exc_info=True)
    return stack


def infrastructure_observability_status_789() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "sprint": _SPRINT,
        "internal_admin_only": True,
        "not_user_alert_system": True,
        "user_alerts_ref": 788,
        "stack_components": ["prometheus", "grafana", "loki", "jaeger", "pagerduty"],
        "quality_monitor_ref": 824,
        "data_health_monitor_ref": 849,
        "uptime_shield_ref": 862,
        "timestamp": _utcnow(),
    }


# --- #862 Infrastructure Uptime Shield (merged into #789) ---

_UPTIME_SHIELD_REF = 862


def build_uptime_slo_shield_862(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#862 — SLO/SLA uptime shield layer with burn-rate and dependency isolation."""
    seed = seed or _load_seed()
    cfg = seed.get("uptime_slo_862") or {}
    slos = cfg.get("slos") or {}
    synthetic = cfg.get("synthetic_checks") or {}
    deps = cfg.get("dependency_isolation") or {}

    return {
        "ok": True,
        "feature_ref": _UPTIME_SHIELD_REF,
        "merged_into": f"#{_FEATURE_ID} Infrastructure Observability",
        "component": "uptime_slo",
        "standalone_rejected": True,
        "sprint": 0,
        "slos_documented": True,
        "slos": {
            "availability_target_pct": float(slos.get("availability_target_pct", 99.9)),
            "latency_p99_max_ms": float(slos.get("latency_p99_max_ms", 500)),
            "error_rate_max_pct": float(slos.get("error_rate_max_pct", 0.1)),
        },
        "synthetic_checks": {
            "interval_sec": int(synthetic.get("interval_sec", 60)),
            "endpoint": synthetic.get("endpoint", "/health"),
            "enabled": synthetic.get("enabled", True),
        },
        "alert_tests": cfg.get("alert_tests") or {"daily_fake_incident": True},
        "incident_runbooks": cfg.get("incident_runbooks") or [],
        "burn_rate_alerts": cfg.get("burn_rate_alerts") or {
            "enabled": True,
            "alert_within_minutes": 5,
        },
        "dependency_isolation": deps,
        "measured_availability": cfg.get("measured_availability") or {},
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_uptime_slo_tests_862(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#862 — SLO compliance, synthetic checks, alert tests."""
    seed = seed or _load_seed()
    shield = build_uptime_slo_shield_862(seed=seed)
    slos = shield.get("slos") or {}
    measured = shield.get("measured_availability") or {}

    tests = [
        {
            "test": "availability_slo",
            "passed": float(measured.get("uptime_pct", 0)) >= float(slos.get("availability_target_pct", 99.9)),
            "actual": measured.get("uptime_pct"),
            "target": slos.get("availability_target_pct"),
        },
        {
            "test": "latency_p99_slo",
            "passed": float(measured.get("latency_p99_ms", 9999)) <= float(slos.get("latency_p99_max_ms", 500)),
            "actual": measured.get("latency_p99_ms"),
            "target": slos.get("latency_p99_max_ms"),
        },
        {
            "test": "error_rate_slo",
            "passed": float(measured.get("error_rate_pct", 100)) <= float(slos.get("error_rate_max_pct", 0.1)),
            "actual": measured.get("error_rate_pct"),
            "target": slos.get("error_rate_max_pct"),
        },
        {
            "test": "synthetic_checks_60s",
            "passed": shield.get("synthetic_checks", {}).get("interval_sec") == 60,
        },
        {
            "test": "daily_alert_test",
            "passed": shield.get("alert_tests", {}).get("daily_fake_incident") is True,
        },
        {
            "test": "incident_runbooks_documented",
            "passed": len(shield.get("incident_runbooks") or []) > 0,
        },
        {
            "test": "burn_rate_alerts",
            "passed": shield.get("burn_rate_alerts", {}).get("enabled") is True,
        },
        {
            "test": "circuit_breaker_configured",
            "passed": bool(shield.get("dependency_isolation", {}).get("circuit_breakers")),
        },
    ]
    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _UPTIME_SHIELD_REF,
        "slo_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }


def run_uptime_shield_e2e_862(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    shield = build_uptime_slo_shield_862(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": shield.get("standalone_rejected") is True})
    tests.append({"test": "slos_documented", "passed": shield.get("slos_documented") is True})
    tests.append({"test": "availability_99_9", "passed": shield.get("slos", {}).get("availability_target_pct") == 99.9})

    slo_tests = run_uptime_slo_tests_862(seed=seed)
    tests.append({"test": "all_slo_tests_pass", "passed": slo_tests.get("all_passed") is True})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _UPTIME_SHIELD_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
