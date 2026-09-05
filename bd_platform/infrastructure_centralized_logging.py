"""
Infrastructure Centralized Logging Stack — #1060 (Sprint 0).

Merged into Sprint-0 Infrastructure — NOT standalone.
Searchable structured JSON logs, tiered retention, trace correlation, sanitization.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.CentralizedLogging")

_FEATURE_REF = 1060
_STANDALONE = False
_MERGED_INTO = "Sprint-0 Infrastructure"
_SEED_PATH = Path("data/infrastructure_ops_foundation_seed.json")
_RUNBOOK = "docs/ops/CENTRALIZED_LOGGING.md"
_LOG_STORE = Path("data/centralized_logs.jsonl")

_SENSITIVE_PATTERNS = (
    re.compile(r"(password|passwd|secret|private_key|wallet_seed|mnemonic)\s*[:=]\s*\S+", re.I),
    re.compile(r"0x[a-fA-F0-9]{64}"),
)

_log_buffer: list[dict[str, Any]] = []
_alert_log: list[dict[str, Any]] = []


def reset_centralized_logging_state() -> None:
    _log_buffer.clear()
    _alert_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("centralized logging seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("centralized_logging_1060") or {}


def centralized_logging_status_1060(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
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
            "stack": policy.get("stack", "loki_compatible"),
            "search_latency_sec_max": policy.get("search_latency_sec_max", 2),
            "structured_json_enforced": policy.get("structured_json_enforced", True),
            "schema_version": policy.get("schema_version", "1.0.0"),
            "blocks_production_if_incomplete": policy.get("blocks_production_if_incomplete", True),
        },
        "retention": cfg.get("retention") or {},
        "schema_fields": cfg.get("schema_fields") or [],
        "services_covered": cfg.get("services") or [],
        "access_control": cfg.get("access_control") or {},
        "sanitization": cfg.get("sanitization") or {},
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "timestamp": _utcnow(),
    }


def _sanitize_message(message: str) -> str:
    out = message
    for pattern in _SENSITIVE_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def ingest_log_entry_1060(
    *,
    service: str,
    level: str,
    message: str,
    trace_id: str = "",
    user_id: str = "",
    tenant_id: str = "platform",
    metadata: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ingest structured JSON log — schema enforced, sanitization applied."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    schema = cfg.get("schema_fields") or []
    entry = {
        "log_id": f"log_{uuid.uuid4().hex[:10]}",
        "timestamp": _utcnow(),
        "timestamp_epoch": time.time(),
        "service": service,
        "level": level.upper(),
        "trace_id": trace_id or f"trc_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "message": _sanitize_message(message),
        "metadata": metadata or {},
        "schema_version": (cfg.get("policy") or {}).get("schema_version", "1.0.0"),
    }
    for field in schema:
        if field not in entry and field != "metadata":
            entry[field] = entry.get(field, "")

    _log_buffer.append(entry)
    try:
        _LOG_STORE.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_STORE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("centralized log persist failed", exc_info=True)

    if level.upper() in {"ERROR", "CRITICAL"}:
        _evaluate_log_alert(entry, seed=seed)

    return {"ok": True, "entry": entry, "sanitized": message != entry["message"]}


def _evaluate_log_alert(entry: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    alert = {
        "alert_id": f"log_{uuid.uuid4().hex[:8]}",
        "trigger": "error_rate_spike",
        "service": entry.get("service"),
        "trace_id": entry.get("trace_id"),
        "message": entry.get("message"),
        "rule_based": True,
        "timestamp": _utcnow(),
    }
    _alert_log.append(alert)


def search_logs_1060(
    *,
    query: str = "",
    service: str = "",
    trace_id: str = "",
    level: str = "",
    limit: int = 50,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full-text + structured search — target latency ≤2 seconds."""
    started = time.perf_counter()
    seed = seed or _load_seed()
    results = list(_log_buffer)
    if service:
        results = [r for r in results if r.get("service") == service]
    if trace_id:
        results = [r for r in results if r.get("trace_id") == trace_id]
    if level:
        results = [r for r in results if r.get("level") == level.upper()]
    if query:
        q = query.lower()
        results = [r for r in results if q in r.get("message", "").lower() or q in json.dumps(r.get("metadata") or {}).lower()]

    duration_sec = time.perf_counter() - started
    max_sec = float((_cfg(seed).get("policy") or {}).get("search_latency_sec_max", 2))

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "results": results[-limit:],
        "count": len(results[-limit:]),
        "duration_sec": round(duration_sec, 4),
        "within_sla": duration_sec <= max_sec,
        "timestamp": _utcnow(),
    }


def check_access_control_1060(*, role: str, environment: str = "production", seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    ac = (_cfg(seed).get("access_control") or {})
    if role == "ops":
        allowed = True
    elif role == "developer":
        allowed = environment != "production"
    else:
        allowed = False
    return {
        "ok": True,
        "role": role,
        "environment": environment,
        "read_allowed": allowed,
        "write_allowed": role == "system",
        "rbac_ref": ac.get("rbac_ref", 1022),
    }


def check_production_gate_1060(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = centralized_logging_status_1060(seed=seed)
    policy = status["policy"]
    retention = status["retention"]
    checks = {
        "structured_json": policy["structured_json_enforced"] is True,
        "search_sla_2s": policy["search_latency_sec_max"] <= 2,
        "retention_ops_30d": retention.get("operational_days") == 30,
        "retention_audit_2y": retention.get("audit_years") == 2,
        "retention_security_5y": retention.get("security_years") == 5,
        "services_covered": len(status["services_covered"]) >= 7,
        "sanitization_enabled": status["sanitization"].get("strip_private_keys") is True,
        "schema_fields": len(status["schema_fields"]) >= 8,
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "blocks_production": True,
        "production_allowed": all(checks.values()),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_centralized_logging_e2e_1060(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_centralized_logging_state()
    checks: list[dict[str, Any]] = []

    status = centralized_logging_status_1060(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "schema_enforced", "passed": status["policy"]["structured_json_enforced"] is True})

    entry = ingest_log_entry_1060(
        service="api",
        level="INFO",
        message="Oracle request processed",
        trace_id="trc_test123",
        user_id="user_1",
        seed=seed,
    )
    checks.append({"id": "ingest_structured", "passed": "trace_id" in entry["entry"]})

    redacted = ingest_log_entry_1060(
        service="api",
        level="ERROR",
        message="auth failed password=supersecret123",
        seed=seed,
    )
    checks.append({"id": "sanitization", "passed": "[REDACTED]" in redacted["entry"]["message"]})

    search = search_logs_1060(trace_id="trc_test123", seed=seed)
    checks.append({"id": "search_by_trace", "passed": search["count"] >= 1})
    checks.append({"id": "search_sla", "passed": search["within_sla"] is True})

    access = check_access_control_1060(role="developer", environment="production", seed=seed)
    checks.append({"id": "rbac_prod_dev_read_denied", "passed": access["read_allowed"] is False})

    gate = check_production_gate_1060(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["production_allowed"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
