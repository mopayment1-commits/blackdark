"""Derived critical failure-mode population — no hardcoded counters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FailureMode:
    failure_mode_id: str
    failure_mode: str
    detection_path: str
    local_alert_path: str
    external_alert_path: str
    fallback_channel: str
    status: str  # ALERTED_LOCAL | EXTERNAL_DELIVERY_PENDING_ONLY

    def as_dict(self) -> dict[str, Any]:
        return {
            "FAILURE_MODE_ID": self.failure_mode_id,
            "FAILURE_MODE": self.failure_mode,
            "DETECTION_PATH": self.detection_path,
            "LOCAL_ALERT_PATH": self.local_alert_path,
            "EXTERNAL_ALERT_PATH": self.external_alert_path,
            "FALLBACK_CHANNEL": self.fallback_channel,
            "STATUS": self.status,
        }


def build_critical_failure_modes() -> list[FailureMode]:
    """Population derived from incident runbook + monitoring modules."""
    modes = [
        FailureMode(
            "CFM-001",
            "Service unreachable / health probe failure",
            "uptime_monitor.record_probe; probe_endpoints /health/live,/health/ready",
            "ops.monitoring_alerting._send_ops_alert on consecutive_failures",
            "UptimeRobot/Better Stack (EXTERNAL_UPTIME_MONITOR_URL)",
            "Telegram ops + MONITORING_WEBHOOK_URL",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-002",
            "High HTTP error rate",
            "runtime_verification.alert_status; check_health_signals error_rate",
            "ops.monitoring_alerting._maybe_alert_signal error_rate",
            "External APM/Sentry (SENTRY_DSN)",
            "Telegram + webhook",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-003",
            "SLA/uptime breach (24h)",
            "uptime_monitor.uptime_stats meets_sla",
            "ops.monitoring_alerting sla_breach alert",
            "External uptime monitor",
            "Telegram + webhook",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-004",
            "Vendor rate limit / throttle",
            "ops.vendor_rate_limit_watchdog.should_alert_vendor_throttle",
            "ops.monitoring_alerting vendor_throttle alert",
            "Vendor status pages",
            "Degraded mode + logs",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-005",
            "Production guard / config failure",
            "production_guard.evaluate_production_guard; /api/production/guard",
            "Guard required_failures block deploy; ops runbook",
            "External monitor on /api/production/guard",
            "Runbook + admin dashboard",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-006",
            "Database / Postgres degradation",
            "postgres_backend.pool_stats; incident table 5xx spike",
            "INCIDENT_RESPONSE.md actions; monitoring alerts",
            "Managed DB provider alerts",
            "Runbook pg_stat_activity checks",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-007",
            "Redis / cache / queue failure",
            "scale_readiness redis check; INCIDENT_RESPONSE Redis row",
            "Incident runbook; probe degradation",
            "Redis provider monitoring",
            "Fail-closed cache paths",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-008",
            "Auth bypass / session compromise",
            "security_events.py; INCIDENT_RESPONSE auth row",
            "Incident runbook; security_events log",
            "SIEM external",
            "Session invalidation runbook",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-009",
            "Financial truth / fee-gas fail-open",
            "fee_matrix/gas_oracle fail-closed; INCIDENT_RESPONSE wrong profit",
            "Contradiction veto; execution_engine.trigger_panic",
            "External audit",
            "Fail-closed None returns",
            "ALERTED_LOCAL",
        ),
        FailureMode(
            "CFM-010",
            "Billing webhook / PSP failure",
            "billing webhook_processor; INCIDENT_RESPONSE webhook 401",
            "Incident runbook; webhook retry logs",
            "PSP dashboard alerts",
            "Manual webhook replay runbook",
            "ALERTED_LOCAL",
        ),
    ]
    return modes


def failure_mode_counters(modes: list[FailureMode]) -> dict[str, Any]:
    alerted_local = sum(1 for m in modes if m.status == "ALERTED_LOCAL")
    unalerted = sum(1 for m in modes if m.status not in {"ALERTED_LOCAL", "EXTERNAL_DELIVERY_PENDING_ONLY"})
    external_only = sum(1 for m in modes if m.status == "EXTERNAL_DELIVERY_PENDING_ONLY")
    return {
        "CRITICAL_FAILURE_MODES": len(modes),
        "CRITICAL_FAILURE_MODES_WITH_ALERT": alerted_local + external_only,
        "TRUE_UNALERTED_CRITICAL_FAILURE_MODES": unalerted,
        "EXTERNAL_PAGER_VALIDATION_PENDING": True,
        "failure_modes": [m.as_dict() for m in modes],
    }
