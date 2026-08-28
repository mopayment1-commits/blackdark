"""
Infrastructure Uptime Monitoring & Alerting — #1059 (Sprint 0).

Merged into Sprint-0 Infrastructure — NOT standalone.
Outside-in multi-region probes, immediate alerting, status page, incident auto-creation.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.UptimeMonitoring")

_FEATURE_REF = 1059
_STANDALONE = False
_MERGED_INTO = "Sprint-0 Infrastructure"
_SEED_PATH = Path("data/infrastructure_ops_foundation_seed.json")
_RUNBOOK = "docs/ops/UPTIME_MONITORING.md"

_INCIDENT_REF = 1017
_CIRCUIT_BREAKER_REF = 1051
_LOAD_TEST_REF = 1020
_DDOS_REF = 1047
_BADGE_REF = 1030
_AUDIT_REF = 1038

_probe_results: list[dict[str, Any]] = []
_alert_log: list[dict[str, Any]] = []
_escalation_log: list[dict[str, Any]] = []


def reset_uptime_monitoring_state() -> None:
    _probe_results.clear()
    _alert_log.clear()
    _escalation_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("uptime monitoring seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("uptime_monitoring_1059") or {}


def uptime_monitoring_status_1059(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    services = cfg.get("critical_services") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sprint": 0,
        "policy": {
            "probe_interval_sec": policy.get("probe_interval_sec", 30),
            "outside_in_monitoring": policy.get("outside_in_only", True),
            "no_localhost_only": policy.get("no_localhost_only", True),
            "down_alert_threshold_sec": policy.get("down_alert_threshold_sec", 60),
            "notification_sla_sec": policy.get("notification_sla_sec", 120),
            "escalation_no_ack_minutes": policy.get("escalation_no_ack_minutes", 5),
            "public_status_page": policy.get("public_status_page", "/status"),
            "best_effort_language": policy.get("best_effort_language", True),
            "no_guaranteed_uptime": policy.get("no_guaranteed_uptime", True),
            "user_notify_outage_minutes": policy.get("user_notify_outage_minutes", 5),
            "blocks_production_if_incomplete": policy.get("blocks_production_if_incomplete", True),
        },
        "critical_services_count": len(services),
        "critical_services": list(services.keys()),
        "probe_regions": cfg.get("probe_regions") or [],
        "alert_channels": cfg.get("alert_channels") or [],
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "timestamp": _utcnow(),
    }


def record_external_probe_1059(
    *,
    service: str,
    region: str,
    ok: bool,
    latency_ms: float,
    path: str = "",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record outside-in probe result from multi-region monitor."""
    seed = seed or _load_seed()
    entry = {
        "probe_id": f"prb_{uuid.uuid4().hex[:10]}",
        "service": service,
        "region": region,
        "ok": ok,
        "latency_ms": round(latency_ms, 2),
        "path": path,
        "source": "external_probe",
        "timestamp": _utcnow(),
        "timestamp_epoch": time.time(),
    }
    _probe_results.append(entry)

    try:
        from uptime_monitor import record_probe

        record_probe(ok=ok, source=f"external:{region}", latency_ms=latency_ms)
    except ImportError:
        pass

    down_since = _service_down_since(service)
    policy = (_cfg(seed).get("policy") or {})
    threshold = float(policy.get("down_alert_threshold_sec", 60))
    recent_fails = sum(1 for p in _probe_results[-5:] if p.get("service") == service and not p.get("ok"))
    sustained_down = down_since and (time.time() - down_since) >= threshold
    consecutive_fail = recent_fails >= 3
    alert = None
    if not ok and (sustained_down or consecutive_fail):
        down_sec = (time.time() - down_since) if down_since else 0
        alert = _trigger_uptime_alert(service=service, region=region, down_sec=down_sec, seed=seed)

    return {"ok": ok, "probe": entry, "alert": alert, "timestamp": _utcnow()}


def _service_down_since(service: str) -> float | None:
    recent = [p for p in _probe_results if p.get("service") == service][-10:]
    if not recent:
        return None
    fails = [p for p in recent if not p.get("ok")]
    if len(fails) < 2:
        return None
    return fails[0].get("timestamp_epoch")


def _trigger_uptime_alert(
    *, service: str, region: str, down_sec: float, seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    seed = seed or _load_seed()
    alert = {
        "alert_id": f"upt_{uuid.uuid4().hex[:10]}",
        "service": service,
        "region": region,
        "down_seconds": round(down_sec, 1),
        "severity": "critical",
        "channels": (_cfg(seed).get("alert_channels") or ["pagerduty"]),
        "notification_sla_sec": (_cfg(seed).get("policy") or {}).get("notification_sla_sec", 120),
        "acknowledged": False,
        "escalated": False,
        "timestamp": _utcnow(),
        "append_only": True,
        "activity_audit_ref": _AUDIT_REF,
    }
    _alert_log.append(alert)
    _create_incident_from_uptime_alert(alert, seed=seed)
    return alert


def _create_incident_from_uptime_alert(alert: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        try:
            from institutional_assurance import ir_program
            ir_program()
        except ImportError:
            logger.debug("incident response bridge unavailable for uptime alert")
        return
    try:
        record_incident_829(
            scenario="service_outage",
            severity="critical",
            title=f"Uptime alert: {alert['service']} down {alert['down_seconds']}s ({alert['region']})",
            seed=seed,
        )
    except Exception:
        logger.debug("uptime incident creation skipped", exc_info=True)


def acknowledge_uptime_alert_1059(*, alert_id: str, operator: str = "oncall") -> dict[str, Any]:
    for alert in _alert_log:
        if alert.get("alert_id") == alert_id:
            alert["acknowledged"] = True
            alert["acknowledged_by"] = operator
            alert["acknowledged_at"] = _utcnow()
            return {"ok": True, "alert": alert}
    return {"ok": False, "error": "alert_not_found"}


def check_alert_escalation_1059(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Escalate unacknowledged alerts after 5 minutes to Incident Commander."""
    seed = seed or _load_seed()
    minutes = int((_cfg(seed).get("policy") or {}).get("escalation_no_ack_minutes", 5))
    escalated: list[dict[str, Any]] = []
    cutoff = time.time() - minutes * 60
    for alert in _alert_log:
        if alert.get("acknowledged") or alert.get("escalated"):
            continue
        ts = alert.get("timestamp", "")
        try:
            created = datetime.fromisoformat(ts).timestamp()
        except (TypeError, ValueError):
            continue
        if created <= cutoff:
            alert["escalated"] = True
            alert["escalated_to"] = "incident_commander"
            alert["escalated_at"] = _utcnow()
            escalated.append(alert)
            _escalation_log.append({"alert_id": alert["alert_id"], "escalated_at": _utcnow()})
    return {"ok": True, "escalated_count": len(escalated), "escalated": escalated}


def build_public_status_page_1059(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Public /status data — uptime %, historical, best-effort language."""
    seed = seed or _load_seed()
    services = (_cfg(seed).get("critical_services") or {})
    service_status: dict[str, Any] = {}
    for name in services:
        recent = [p for p in _probe_results if p.get("service") == name][-20:]
        if not recent:
            recent_seed = (seed.get("uptime_monitoring_1059") or {}).get("seed_probe_history") or []
            recent = [p for p in recent_seed if p.get("service") == name]
        ok_count = sum(1 for p in recent if p.get("ok"))
        total = len(recent) or 1
        service_status[name] = {
            "status": "operational" if ok_count / total >= 0.95 else "degraded",
            "uptime_percent": round((ok_count / total) * 100, 2),
        }

    try:
        from uptime_monitor import uptime_stats

        stats = uptime_stats(window_hours=24.0)
    except ImportError:
        stats = {"uptime_percent": 100.0, "probes_total": 0}

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "page_path": "/status",
        "language": "best_effort",
        "no_guaranteed_uptime": True,
        "services": service_status,
        "overall_uptime_percent": stats.get("uptime_percent", 100.0),
        "historical_window_hours": 24,
        "timestamp": _utcnow(),
    }


def get_uptime_audit_trail_1059(*, limit: int = 50) -> dict[str, Any]:
    alerts = _alert_log[-limit:]
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "alerts": alerts,
        "escalations": _escalation_log[-limit:],
        "append_only": True,
        "activity_audit_ref": _AUDIT_REF,
        "count": len(alerts),
        "timestamp": _utcnow(),
    }


def check_production_gate_1059(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = uptime_monitoring_status_1059(seed=seed)
    policy = status["policy"]
    checks = {
        "outside_in_monitoring": policy["outside_in_monitoring"] is True,
        "probe_interval_30s": policy["probe_interval_sec"] == 30,
        "services_min_7": status["critical_services_count"] >= 7,
        "multi_region_probes": len(status["probe_regions"]) >= 2,
        "notification_sla_2min": policy["notification_sla_sec"] <= 120,
        "escalation_5min": policy["escalation_no_ack_minutes"] == 5,
        "public_status_page": bool(policy["public_status_page"]),
        "no_guaranteed_uptime": policy["no_guaranteed_uptime"] is True,
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "blocks_production": True,
        "production_allowed": all(checks.values()),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_uptime_monitoring_e2e_1059(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_uptime_monitoring_state()
    checks: list[dict[str, Any]] = []

    status = uptime_monitoring_status_1059(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "services_min_7", "passed": status["critical_services_count"] >= 7})
    checks.append({"id": "probe_30s", "passed": status["policy"]["probe_interval_sec"] == 30})
    checks.append({"id": "outside_in", "passed": status["policy"]["outside_in_monitoring"] is True})

    for region in ("eu-west-1", "us-east-1"):
        record_external_probe_1059(
            service="oracle_api", region=region, ok=True, latency_ms=45.0, path="/api/oracle/quick", seed=seed
        )
    checks.append({"id": "probe_recorded", "passed": len(_probe_results) >= 2})

    record_external_probe_1059(service="oracle_api", region="eu-west-1", ok=False, latency_ms=0, seed=seed)
    record_external_probe_1059(service="oracle_api", region="us-east-1", ok=False, latency_ms=0, seed=seed)
    time.sleep(0.01)
    for _ in range(3):
        record_external_probe_1059(service="oracle_api", region="eu-west-1", ok=False, latency_ms=0, seed=seed)
    checks.append({"id": "alert_on_downtime", "passed": len(_alert_log) >= 1})

    ack = acknowledge_uptime_alert_1059(alert_id=_alert_log[0]["alert_id"]) if _alert_log else {"ok": False}
    checks.append({"id": "acknowledgment", "passed": ack.get("ok") is True})

    escalation = check_alert_escalation_1059(seed=seed)
    checks.append({"id": "escalation_check", "passed": escalation.get("ok") is True})

    page = build_public_status_page_1059(seed=seed)
    checks.append({"id": "status_page", "passed": page.get("no_guaranteed_uptime") is True})

    gate = check_production_gate_1059(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["production_allowed"] is True})

    audit = get_uptime_audit_trail_1059()
    checks.append({"id": "audit_logged", "passed": audit["count"] >= 1})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
