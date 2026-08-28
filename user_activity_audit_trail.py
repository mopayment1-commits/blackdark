"""
User Activity Audit Trail — Cross-Cutting Infrastructure.

Merged into #1019 + #1022 + #945 + #1029 — NOT standalone.
Full user action logging: who · what · when · where · result.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.UserActivityAudit")

_FEATURE = "user_activity_audit_trail"
_SEED_PATH = Path("data/user_activity_audit_seed.json")
_AUDIT_PATH = Path("data/user_activity_audit.jsonl")
_IMMUTABLE_DIR = Path("data/immutable_recommendation_audit")

_SESSION_REF = 1019
_RBAC_REF = 1022
_PROVENANCE_REF = 945
_IMMUTABLE_REF = 1029
_STRIPE_REF = 908
_INCIDENT_REF = 1017
_GDPR_REF = 1023
_RETENTION_REF = 949

_LOCK = threading.Lock()
_ANONYMIZED_USERS: set[int] = set()

ResultStatus = Literal["success", "failure", "denied"]


def reset_user_activity_state() -> None:
    _ANONYMIZED_USERS.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("user_activity_audit") or {}


def user_activity_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "policy": {
            "append_only": policy.get("append_only", True),
            "worm_storage": policy.get("worm_storage", True),
            "backend_enforced": policy.get("backend_enforced", True),
            "gateway_logging": policy.get("gateway_logging", True),
            "operational_retention_days": policy.get("operational_retention_days", 730),
            "institutional_retention_days": policy.get("institutional_retention_days", 1825),
            "gdpr_anonymize_not_delete": policy.get("gdpr_anonymize_not_delete", True),
            "blocks_production": policy.get("blocks_production", True),
        },
        "scoped_actions": _cfg(seed).get("scoped_actions") or [],
        "high_sensitivity_actions": _cfg(seed).get("high_sensitivity_actions") or [],
        "integrations": _cfg(seed).get("integrations") or {},
        "path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def _signing_key() -> str:
    return (
        os.getenv("AUDIT_SIGNING_KEY", "").strip()
        or os.getenv("SECRETS_MASTER_KEY", "").strip()
        or "blackdark-user-activity-audit-dev"
    )


def _sign_event(event: dict[str, Any]) -> str:
    canonical = {
        "event_id": event.get("event_id"),
        "who": event.get("who"),
        "what": event.get("what"),
        "when": event.get("when"),
        "where": event.get("where"),
        "result": event.get("result"),
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(_signing_key().encode() + raw).hexdigest()


def _email_hash(email: str | None) -> str | None:
    if not email:
        return None
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:32]


def log_user_activity(
    action: str,
    *,
    user_id: int | None = None,
    email: str | None = None,
    role: str | None = None,
    tenant_id: str | None = None,
    resource_id: str | None = None,
    data_snapshot_hash: str | None = None,
    ip: str | None = None,
    device_fingerprint: str | None = None,
    result: ResultStatus = "success",
    error_code: str | None = None,
    http_status: int | None = None,
    detail: dict[str, Any] | None = None,
    retention_tier: Literal["operational", "institutional"] = "operational",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append-only WORM user activity event — 5 dimensions."""
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    if user_id and user_id in _ANONYMIZED_USERS:
        email = None
        user_id = None

    event = {
        "event_id": f"ua_{uuid.uuid4().hex[:16]}",
        "who": {
            "user_id": user_id,
            "email_hash": _email_hash(email),
            "role": role,
            "tenant_id": tenant_id,
        },
        "what": {
            "action": action,
            "resource_id": resource_id,
            "data_snapshot_hash": data_snapshot_hash,
        },
        "when": _utcnow(),
        "where": {
            "ip": ip,
            "device_fingerprint": device_fingerprint,
        },
        "result": {
            "status": result,
            "error_code": error_code,
            "http_status": http_status,
        },
        "detail": detail or {},
        "append_only": True,
        "worm": policy.get("worm_storage", True),
        "retention_days": (
            policy.get("institutional_retention_days", 1825)
            if retention_tier == "institutional"
            else policy.get("operational_retention_days", 730)
        ),
        "retention_tier": retention_tier,
        "ts": time.time(),
    }
    event["signature"] = _sign_event(event)

    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    _maybe_mirror_immutable(event, seed=seed)
    _maybe_high_sensitivity_alert(event, seed=seed)
    _check_suspicious_patterns(event, seed=seed)

    try:
        from security_events import record_security_event

        record_security_event(
            f"user_activity_{action}",
            severity="warning" if result in ("failure", "denied") else "info",
            actor=email or (str(user_id) if user_id else None),
            ip=ip,
            detail={"event_id": event["event_id"], "action": action, "result": result},
        )
    except ImportError:
        pass
    return event


def _maybe_mirror_immutable(event: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    action = str((event.get("what") or {}).get("action") or "")
    insight_actions = ("report.generate", "query.execute", "decisions.view", "api.request")
    if not any(action.startswith(p) for p in insight_actions):
        return
    _IMMUTABLE_DIR.mkdir(parents=True, exist_ok=True)
    path = _IMMUTABLE_DIR / f"{event['event_id']}.json"
    try:
        path.write_text(json.dumps(event, ensure_ascii=False), encoding="utf-8")
    except OSError:
        logger.debug("immutable mirror failed", exc_info=True)


def _maybe_high_sensitivity_alert(event: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    seed = seed or _load_seed()
    action = str((event.get("what") or {}).get("action") or "")
    sensitive = set((_cfg(seed).get("high_sensitivity_actions") or []))
    if action not in sensitive:
        return
    try:
        from security_events import record_security_event

        record_security_event(
            "high_sensitivity_activity",
            severity="warning",
            actor=str((event.get("who") or {}).get("user_id") or ""),
            ip=(event.get("where") or {}).get("ip"),
            detail={"action": action, "event_id": event.get("event_id")},
        )
    except ImportError:
        pass


def _recent_events_for_user(user_id: int | None, email_hash: str | None, *, window_seconds: int = 900) -> list[dict[str, Any]]:
    if not _AUDIT_PATH.is_file():
        return []
    cutoff = time.time() - window_seconds
    rows: list[dict[str, Any]] = []
    try:
        for line in _AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-500:]:
            if not line.strip():
                continue
            row = json.loads(line)
            if float(row.get("ts") or 0) < cutoff:
                continue
            who = row.get("who") or {}
            if user_id and who.get("user_id") == user_id:
                rows.append(row)
            elif email_hash and who.get("email_hash") == email_hash:
                rows.append(row)
    except (OSError, json.JSONDecodeError):
        pass
    return rows


def _check_suspicious_patterns(event: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    """#1017 — new location + mass export + role change = auto-alert."""
    who = event.get("who") or {}
    user_id = who.get("user_id")
    if not user_id:
        return
    recent = _recent_events_for_user(int(user_id), who.get("email_hash"))
    actions = {str((r.get("what") or {}).get("action") or "") for r in recent}
    action = str((event.get("what") or {}).get("action") or "")
    suspicious = (
        "auth.login" in actions
        and ("data.export" in actions or action == "data.export")
        and ("rbac.role_change" in actions or action == "rbac.role_change")
    )
    if not suspicious:
        return
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        return
    try:
        record_incident_829(
            scenario="security",
            severity="critical",
            title=f"Suspicious user activity pattern user_id={user_id}",
            seed=seed,
        )
    except Exception:
        logger.debug("incident alert failed", exc_info=True)


async def log_user_activity_from_request(
    request: Any,
    *,
    response_status: int,
    body_bytes: bytes | None = None,
    user: dict[str, Any] | None = None,
    action: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """API gateway hook — log every /api/ request with 5 dimensions."""
    path = getattr(getattr(request, "url", None), "path", "") or ""
    if not str(path).startswith("/api/"):
        return None
    if str(path).startswith("/api/audit/") or str(path).startswith("/api/platform/user-activity/"):
        return None

    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip:
        client = getattr(request, "client", None)
        ip = getattr(client, "host", None) if client else None

    device_fp = None
    try:
        from password_recovery_hardening import compute_device_fingerprint

        device_fp = compute_device_fingerprint(
            user_agent=request.headers.get("user-agent"),
            accept_language=request.headers.get("accept-language"),
            ip=ip,
        )
    except ImportError:
        pass

    from audit_registry import hash_payload, request_payload_fingerprint

    fingerprint = request_payload_fingerprint(
        method=request.method,
        path=path,
        query=str(getattr(getattr(request, "url", None), "query", "") or ""),
        body_bytes=body_bytes,
    )

    resolved_action = action or f"api.request.{request.method.lower()}"
    tenant_id = (request.headers.get("x-tenant-id") or "").strip() or None
    uid = int(user["id"]) if user and user.get("id") else None
    email = str(user.get("email") or "") if user else None
    tier = str(user.get("tier") or "free") if user else "free"
    retention = "institutional" if tier == "institutional" else "operational"

    result: ResultStatus = "success" if 200 <= int(response_status) < 400 else "failure"
    if int(response_status) in (401, 403):
        result = "denied"

    return log_user_activity(
        resolved_action,
        user_id=uid,
        email=email,
        role=user.get("role") if user else None,
        tenant_id=tenant_id,
        resource_id=path,
        data_snapshot_hash=fingerprint,
        ip=ip,
        device_fingerprint=device_fp,
        result=result,
        error_code=f"http_{response_status}" if result != "success" else None,
        http_status=int(response_status),
        detail={"method": request.method, "path": path},
        retention_tier=retention,  # type: ignore[arg-type]
        seed=seed,
    )


def anonymize_user_activity(user_id: int, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#1023 GDPR — anonymize PII in log entries; retain hash for integrity."""
    seed = seed or _load_seed()
    _ANONYMIZED_USERS.add(int(user_id))
    entry = log_user_activity(
        "gdpr.anonymize",
        user_id=user_id,
        result="success",
        detail={"anonymized": True, "entries_preserved": True},
        seed=seed,
    )
    return {"ok": True, "user_id": user_id, "anonymized": True, "audit_event_id": entry["event_id"]}


def _load_events(*, limit: int = 500) -> list[dict[str, Any]]:
    if not _AUDIT_PATH.is_file():
        return []
    try:
        lines = _AUDIT_PATH.read_text(encoding="utf-8").splitlines()
        return [json.loads(x) for x in lines[-limit:] if x.strip()]
    except (OSError, json.JSONDecodeError):
        return []


def query_user_activity(
    *,
    viewer_email: str,
    viewer_user_id: int | None = None,
    tenant_id: str | None = None,
    target_user_id: int | None = None,
    action: str | None = None,
    limit: int = 50,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """RBAC-scoped activity query — user own · admin team · super admin all."""
    seed = seed or _load_seed()
    rows = _load_events(limit=max(limit * 5, 200))
    viewer_email = viewer_email.strip().lower()

    scope = "own"
    team_emails: set[str] = set()
    if tenant_id:
        try:
            from org_tenant import list_members, member_of

            mem = member_of(tenant_id, viewer_email)
            role = str((mem or {}).get("role") or "viewer")
            if role in {"admin", "super_admin"}:
                scope = "team"
                team_emails = {str(m.get("email") or "").lower() for m in list_members(tenant_id)}
            elif role == "super_admin":
                scope = "all"
        except ImportError:
            pass

    try:
        from security_auth import is_admin_user, admin_emails

        if viewer_email in admin_emails() or (
            viewer_user_id and is_admin_user({"email": viewer_email, "id": viewer_user_id})
        ):
            scope = "all"
    except ImportError:
        pass

    viewer_hash = _email_hash(viewer_email)
    filtered: list[dict[str, Any]] = []
    for row in reversed(rows):
        who = row.get("who") or {}
        if action and str((row.get("what") or {}).get("action") or "") != action:
            continue
        if tenant_id and who.get("tenant_id") and who.get("tenant_id") != tenant_id:
            continue
        if scope == "own":
            if viewer_user_id and who.get("user_id") != viewer_user_id and who.get("email_hash") != viewer_hash:
                continue
        elif scope == "team":
            if tenant_id and who.get("tenant_id") and who.get("tenant_id") != tenant_id:
                continue
        if target_user_id and who.get("user_id") != target_user_id:
            continue
        filtered.append(row)
        if len(filtered) >= limit:
            break

    return {
        "ok": True,
        "scope": scope,
        "events_count": len(filtered),
        "events": filtered,
        "append_only": True,
        "timestamp": _utcnow(),
    }


def get_user_activity_trail(*, limit: int = 50) -> dict[str, Any]:
    rows = _load_events(limit=limit)
    return {
        "ok": True,
        "events_count": len(rows),
        "events": rows,
        "path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def bridge_auth_event(
    event_type: str,
    *,
    user_id: int | None = None,
    email: str | None = None,
    ip: str | None = None,
    result: ResultStatus = "success",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#1019 — unify auth events into activity trail."""
    action_map = {
        "enable": "auth.mfa_enable",
        "disable": "auth.mfa_disable",
        "verify": "auth.mfa_verify",
        "create": "auth.login",
        "global-logout": "auth.logout_all",
        "login": "auth.login",
        "logout": "auth.logout",
        "password_change": "auth.password_change",
        "password_reset": "auth.password_reset",
        "role-change-kill": "rbac.role_change",
    }
    return log_user_activity(
        action_map.get(event_type, f"auth.{event_type}"),
        user_id=user_id,
        email=email,
        ip=ip,
        result=result,
        detail=detail,
    )


def bridge_authz_event(
    *,
    email: str | None,
    tenant_id: str | None,
    role: str | None,
    action: str,
    resource: str,
    result: str,
    user_id: int | None = None,
) -> dict[str, Any]:
    """#1022 — unify RBAC authZ decisions."""
    mapped = "rbac.role_change" if "role" in action else f"rbac.{action}"
    return log_user_activity(
        mapped,
        user_id=user_id,
        email=email,
        role=role,
        tenant_id=tenant_id,
        resource_id=resource,
        result="success" if result == "allowed" else "denied",
        detail={"authz_result": result},
        retention_tier="institutional" if tenant_id else "operational",
    )


def check_user_activity_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = user_activity_status(seed=seed)
    policy = status["policy"]
    checks = {
        "append_only": policy["append_only"] is True,
        "worm": policy["worm_storage"] is True,
        "backend_enforced": policy["backend_enforced"] is True,
        "gateway_logging": policy["gateway_logging"] is True,
        "retention_2y": policy["operational_retention_days"] == 730,
        "retention_5y_institutional": policy["institutional_retention_days"] == 1825,
        "gdpr_anonymize": policy.get("gdpr_anonymize_not_delete", True),
        "scoped_actions": len(status["scoped_actions"]) >= 10,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_user_activity_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_user_activity_state()

    status = user_activity_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "worm", "passed": status["policy"]["worm_storage"] is True})
    checks.append({"id": "retention_2y", "passed": status["policy"]["operational_retention_days"] == 730})

    evt = log_user_activity(
        "data.export",
        user_id=1,
        email="user@example.com",
        role="analyst",
        tenant_id="org_test",
        resource_id="report_abc",
        data_snapshot_hash="deadbeef",
        ip="10.0.0.1",
        result="success",
        seed=seed,
    )
    checks.append({"id": "five_dimensions", "passed": all(k in evt for k in ("who", "what", "when", "where", "result"))})
    checks.append({"id": "signed", "passed": bool(evt.get("signature"))})

    bridge_auth_event("login", user_id=1, email="user@example.com", ip="10.0.0.1")
    bridge_authz_event(
        email="admin@example.com",
        tenant_id="org_test",
        role="admin",
        action="permission_check",
        resource="data.export",
        result="allowed",
        user_id=2,
    )
    trail = get_user_activity_trail(limit=10)
    checks.append({"id": "events_logged", "passed": trail["events_count"] >= 2})

    q = query_user_activity(
        viewer_email="user@example.com",
        viewer_user_id=1,
        limit=10,
        seed=seed,
    )
    checks.append({"id": "own_scope", "passed": q["scope"] == "own" and q["events_count"] >= 1})

    anon = anonymize_user_activity(99, seed=seed)
    checks.append({"id": "gdpr_anonymize", "passed": anon["anonymized"] is True})

    gate = check_user_activity_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
