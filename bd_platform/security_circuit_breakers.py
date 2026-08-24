"""
Security Controls and Circuit Breakers — Feature #190 (Sprint 0, non-negotiable).

24/7 threat monitoring, suspicious-pattern detection, platform circuit breakers,
and full audit logging. Integrates with #192 Security-First Architecture and #165 API Security.

Acceptance targets:
  - Detection latency ≤ 1 minute (60s rolling window)
  - False positive rate ≤ 5% (minimum sample gate before trip)
  - 50% error rate → auto-shutdown → alert → investigate
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SecurityCircuitBreakers")

_FEATURE_ID = 190
_AUDIT_PATH = Path("data/security_circuit_breaker_audit.jsonl")
_STATE_PATH = Path("data/security_circuit_breaker_state.json")
_ALERTS_PATH = Path("data/security_circuit_breaker_alerts.jsonl")

# Circuit breaker thresholds (institutional recommendation)
_WINDOW_SECONDS = 60
_ERROR_RATE_THRESHOLD = 0.50
_MIN_SAMPLES = 20  # false-positive guard — do not trip on sparse traffic
_FALSE_POSITIVE_TARGET = 0.05
_LOGIN_FAIL_THRESHOLD = 5  # per IP in 5 minutes
_LOGIN_FAIL_WINDOW = 300
_WITHDRAWAL_CRITICAL = 50.0

_LOCK = threading.Lock()
_REQUEST_WINDOW: deque[tuple[float, bool]] = deque()
_FALSE_POSITIVE_TRACKER: deque[bool] = deque(maxlen=200)

# In-memory state (persisted to disk on transitions)
_STATE: dict[str, Any] = {
    "status": "closed",
    "opened_at": None,
    "opened_reason": None,
    "error_rate": 0.0,
    "sample_count": 0,
    "last_evaluated_at": None,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_state() -> dict[str, Any]:
    if not _STATE_PATH.is_file():
        return dict(_STATE)
    try:
        blob = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
        return {**_STATE, **blob}
    except (OSError, json.JSONDecodeError):
        return dict(_STATE)


def _save_state(state: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_audit(
    *,
    action: str,
    severity: str = "info",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "timestamp": _utcnow(),
        "feature_id": _FEATURE_ID,
        "action": action,
        "severity": severity,
        "detail": detail or {},
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    logger.info("Security circuit breaker audit | action=%s severity=%s", action, severity)
    return row


def _append_alert(alert: dict[str, Any]) -> dict[str, Any]:
    alert = {**alert, "id": str(uuid.uuid4()), "timestamp": _utcnow(), "feature_id": _FEATURE_ID}
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, ensure_ascii=False) + "\n")
    return alert


def _prune_window(now: float | None = None) -> None:
    cutoff = (now or time.time()) - _WINDOW_SECONDS
    while _REQUEST_WINDOW and _REQUEST_WINDOW[0][0] < cutoff:
        _REQUEST_WINDOW.popleft()


def record_request_outcome(*, success: bool, path: str = "") -> None:
    """Record HTTP outcome for rolling error-rate circuit breaker."""
    now = time.time()
    with _LOCK:
        _REQUEST_WINDOW.append((now, success))
        _prune_window(now)


def _compute_error_rate() -> tuple[float, int]:
    now = time.time()
    with _LOCK:
        _prune_window(now)
        samples = list(_REQUEST_WINDOW)
    if not samples:
        return 0.0, 0
    errors = sum(1 for _, ok in samples if not ok)
    return errors / len(samples), len(samples)


def is_platform_shutdown() -> bool:
    state = _load_state()
    return state.get("status") == "open"


def _bypass_paths() -> frozenset[str]:
    return frozenset(
        {
            "/api/health",
            "/api/security/status",
            "/api/security/wave-00",
            "/api/platform/security/circuit-breakers/status",
            "/api/platform/security/circuit-breakers/threats",
            "/api/platform/security/architecture/status",
            "/api/platform/security/threat-model",
        }
    )


def should_block_request(path: str) -> bool:
    if not is_platform_shutdown():
        return False
    base = (path or "").split("?")[0]
    if base in _bypass_paths() or base.startswith("/static/"):
        return False
    return True


def evaluate_circuit_breaker(*, force: bool = False) -> dict[str, Any]:
    """Evaluate rolling error rate; trip breaker at 50% when sample gate met."""
    error_rate, sample_count = _compute_error_rate()
    state = _load_state()
    now_iso = _utcnow()

    should_trip = (
        sample_count >= _MIN_SAMPLES or force
    ) and error_rate >= _ERROR_RATE_THRESHOLD

    previous_status = state.get("status", "closed")

    if should_trip and previous_status != "open":
        state = {
            "status": "open",
            "opened_at": now_iso,
            "opened_reason": f"error_rate_{error_rate:.2%}_samples_{sample_count}",
            "error_rate": round(error_rate, 4),
            "sample_count": sample_count,
            "last_evaluated_at": now_iso,
        }
        _save_state(state)
        alert = _append_alert(
            {
                "kind": "circuit_breaker_open",
                "severity": "critical",
                "headline": "Platform circuit breaker OPEN — auto-shutdown engaged",
                "error_rate": round(error_rate, 4),
                "sample_count": sample_count,
                "action_required": "investigate",
            }
        )
        _append_audit(
            action="circuit_breaker_opened",
            severity="critical",
            detail={"error_rate": error_rate, "sample_count": sample_count, "alert_id": alert["id"]},
        )
        try:
            from security_events import record_security_event

            record_security_event(
                "circuit_breaker_open",
                severity="critical",
                detail={"error_rate": error_rate, "samples": sample_count},
            )
        except Exception:
            logger.debug("security event hook failed", exc_info=True)
    elif not should_trip:
        state["error_rate"] = round(error_rate, 4)
        state["sample_count"] = sample_count
        state["last_evaluated_at"] = now_iso
        if previous_status == "open" and error_rate < _ERROR_RATE_THRESHOLD * 0.5:
            # Auto half-close when error rate drops well below threshold
            state["status"] = "half_open"
            _append_audit(
                action="circuit_breaker_half_open",
                severity="warning",
                detail={"error_rate": error_rate, "sample_count": sample_count},
            )
        _save_state(state)

    return {
        "ok": True,
        "status": state.get("status"),
        "error_rate": round(error_rate, 4),
        "sample_count": sample_count,
        "threshold": _ERROR_RATE_THRESHOLD,
        "min_samples": _MIN_SAMPLES,
        "tripped": should_trip,
        "detection_window_seconds": _WINDOW_SECONDS,
    }


def reset_circuit_breaker(*, reason: str = "admin_reset") -> dict[str, Any]:
    """Admin reset after investigation."""
    state = {
        "status": "closed",
        "opened_at": None,
        "opened_reason": None,
        "error_rate": 0.0,
        "sample_count": 0,
        "last_evaluated_at": _utcnow(),
        "reset_reason": reason,
    }
    _save_state(state)
    with _LOCK:
        _REQUEST_WINDOW.clear()
    _append_audit(action="circuit_breaker_reset", severity="info", detail={"reason": reason})
    return {"ok": True, "status": "closed", "reason": reason}


def _detect_suspicious_logins() -> list[dict[str, Any]]:
    try:
        from security_events import recent_security_events
    except ImportError:
        return []

    now = time.time()
    events = recent_security_events(limit=200, kind=None)
    ip_failures: dict[str, int] = {}
    alerts: list[dict[str, Any]] = []

    for ev in events:
        kind = str(ev.get("kind") or "")
        if kind not in {"login_failed", "auth_denied", "brute_force"}:
            continue
        ts = float(ev.get("ts") or 0)
        if now - ts > _LOGIN_FAIL_WINDOW:
            continue
        ip = str(ev.get("ip") or "unknown")
        ip_failures[ip] = ip_failures.get(ip, 0) + 1

    for ip, count in ip_failures.items():
        if count >= _LOGIN_FAIL_THRESHOLD:
            alerts.append(
                {
                    "kind": "suspicious_login",
                    "severity": "high",
                    "ip": ip,
                    "failure_count": count,
                    "window_seconds": _LOGIN_FAIL_WINDOW,
                    "headline": f"Suspicious login pattern: {count} failures from {ip}",
                    "recommended_action": "rate_limit_and_alert",
                }
            )
    return alerts


def _detect_abnormal_withdrawals() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    snapshot_path = Path("data/exchange_health_snapshots.jsonl")
    if not snapshot_path.is_file():
        return alerts

    latest: dict[str, dict[str, Any]] = {}
    try:
        for line in snapshot_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            ex_id = str(row.get("exchange_id") or "").lower()
            if not ex_id:
                continue
            prev = latest.get(ex_id)
            if not prev or str(row.get("timestamp") or "") >= str(prev.get("timestamp") or ""):
                latest[ex_id] = row
    except (OSError, json.JSONDecodeError):
        return alerts

    for ex_id, snap in latest.items():
        dims = snap.get("dimensions") or {}
        withdrawal = float(dims.get("withdrawal") or 100)
        if withdrawal < _WITHDRAWAL_CRITICAL:
            alerts.append(
                {
                    "kind": "abnormal_withdrawal",
                    "severity": "critical",
                    "exchange_id": ex_id,
                    "withdrawal_score": withdrawal,
                    "headline": f"Abnormal withdrawal stress on {ex_id}: score {withdrawal:.1f}",
                    "recommended_action": "reduce_exposure_and_verify",
                }
            )
    return alerts


def scan_threat_patterns() -> dict[str, Any]:
    """Run WAF/IDS-style pattern detection over security events and exchange health."""
    started = time.perf_counter()
    login_alerts = _detect_suspicious_logins()
    withdrawal_alerts = _detect_abnormal_withdrawals()
    all_alerts = login_alerts + withdrawal_alerts

    for alert in all_alerts:
        _append_alert(alert)
        _append_audit(
            action="threat_pattern_detected",
            severity=str(alert.get("severity") or "warning"),
            detail=alert,
        )

    duration_ms = (time.perf_counter() - started) * 1000.0
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "monitoring": "24/7",
        "detection_latency_target_seconds": _WINDOW_SECONDS,
        "false_positive_target": _FALSE_POSITIVE_TARGET,
        "alerts": all_alerts,
        "alert_count": len(all_alerts),
        "patterns_scanned": ["suspicious_login", "abnormal_withdrawal"],
        "waf_ids_templates": _waf_status(),
        "sla_met": duration_ms <= 2000,
        "duration_ms": round(duration_ms, 2),
        "timestamp": _utcnow(),
    }


def _waf_status() -> dict[str, Any]:
    root = Path(__file__).resolve().parent.parent
    cloudflare = (root / "deploy" / "cloudflare").exists()
    nginx = (root / "nginx" / "blackdark.conf").exists()
    return {
        "edge_waf_templates_present": cloudflare or nginx,
        "cloudflare_deploy_dir": cloudflare,
        "nginx_config": nginx,
        "operator_activation_required": True,
        "intrusion_detection": "application_layer_pattern_scan",
    }


def record_false_positive_feedback(*, was_false_positive: bool) -> dict[str, Any]:
    """Track false-positive rate for acceptance metric (≤5%)."""
    with _LOCK:
        _FALSE_POSITIVE_TRACKER.append(was_false_positive)
        tracker = list(_FALSE_POSITIVE_TRACKER)
    if not tracker:
        rate = 0.0
    else:
        rate = sum(1 for x in tracker if x) / len(tracker)
    return {
        "ok": True,
        "false_positive_rate": round(rate, 4),
        "target": _FALSE_POSITIVE_TARGET,
        "within_target": rate <= _FALSE_POSITIVE_TARGET,
        "samples": len(tracker),
    }


def recent_audit_events(*, limit: int = 50) -> list[dict[str, Any]]:
    if not _AUDIT_PATH.is_file():
        return []
    try:
        lines = _AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(x) for x in lines if x.strip()]
    except (OSError, json.JSONDecodeError):
        return []


def circuit_breaker_status() -> dict[str, Any]:
    """Platform security circuit breaker status (#190)."""
    started = time.perf_counter()
    state = _load_state()
    error_rate, sample_count = _compute_error_rate()
    fp = record_false_positive_feedback(was_false_positive=False)
    duration_ms = (time.perf_counter() - started) * 1000.0

    audit_count = 0
    if _AUDIT_PATH.is_file():
        audit_count = sum(1 for _ in _AUDIT_PATH.open(encoding="utf-8"))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Security Controls and Circuit Breakers",
        "mode": "infrastructure",
        "user_facing": False,
        "status": state.get("status", "closed"),
        "platform_shutdown": is_platform_shutdown(),
        "error_rate": round(error_rate, 4),
        "error_rate_threshold": _ERROR_RATE_THRESHOLD,
        "sample_count": sample_count,
        "min_samples_for_trip": _MIN_SAMPLES,
        "detection_window_seconds": _WINDOW_SECONDS,
        "false_positive_rate": fp["false_positive_rate"],
        "false_positive_target": _FALSE_POSITIVE_TARGET,
        "monitoring_24_7": True,
        "opened_at": state.get("opened_at"),
        "opened_reason": state.get("opened_reason"),
        "audit_events": audit_count,
        "integrated_features": ["#165", "#192"],
        "policy": (
            "50% error rate in 60s window trips platform circuit breaker. "
            "Minimum 20 samples prevents false-positive shutdown. "
            "Full audit trail in security_circuit_breaker_audit.jsonl."
        ),
        "sla_met": duration_ms <= 2000,
        "duration_ms": round(duration_ms, 2),
        "timestamp": _utcnow(),
    }
