"""
Session Lifecycle Hardening — #1019.

Merged into Session/Account Security — NOT standalone.
Idle timeout, absolute timeout, global logout, device binding, audit trail.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SessionLifecycle")

_FEATURE_REF = 1019
_SUB_FEATURE = "session_lifecycle_hardening"
_SEED_PATH = Path("data/session_account_security_seed.json")
_AUDIT_PATH = Path("data/session_audit.jsonl")
_REVOCATION_PATH = Path("data/session_revocation_list.json")
_GLOBAL_LOGOUT_PATH = Path("data/session_global_logout_state.json")
_DEVICE_STORE_PATH = Path("data/session_device_store.json")

_RBAC_REF = 1022
_STRIPE_REF = 908
_INCIDENT_RESPONSE_REF = 1017
_TOS_REF = 1018
_MFA_REF = 1033

SessionEventType = Literal[
    "create",
    "refresh",
    "idle-timeout",
    "absolute-timeout",
    "global-logout",
    "device-change",
    "role-change-kill",
    "mfa-disable-kill",
    "revoked",
    "concurrent-limit-evict",
]

_LOCK = threading.Lock()


def reset_session_lifecycle_state() -> None:
    for path in (_REVOCATION_PATH, _GLOBAL_LOGOUT_PATH):
        if path.is_file():
            path.unlink()


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _lifecycle_cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return (seed.get("session_account_security_1019") or {}).get("session_lifecycle") or {}


def session_lifecycle_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _lifecycle_cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "standalone_rejected": True,
        "merged_into": "#1019 Session/Account Security",
        "policy": {
            "idle_timeout_minutes": policy.get("idle_timeout_minutes", 30),
            "absolute_timeout_hours": policy.get("absolute_timeout_hours", 8),
            "backend_enforced": policy.get("backend_enforced", True),
            "client_side_forbidden": policy.get("client_side_forbidden", True),
            "concurrent_session_limit": policy.get("concurrent_session_limit", 5),
            "invalidate_oldest_on_limit": policy.get("invalidate_oldest_on_limit", True),
            "device_binding_required": policy.get("device_binding_required", True),
            "new_device_email_notification": policy.get("new_device_email_notification", True),
            "global_logout_endpoint": policy.get("global_logout_endpoint", "/auth/logout-all"),
            "billing_session_isolated": policy.get("billing_session_isolated", True),
            "audit_retention_days": policy.get("audit_retention_days", 730),
            "audit_append_only": policy.get("audit_append_only", True),
            "non_custodial": policy.get("non_custodial", True),
        },
        "integrations": cfg.get("integrations") or {
            "rbac_ref": _RBAC_REF,
            "stripe_ref": _STRIPE_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
            "tos_ref": _TOS_REF,
            "mfa_ref": _MFA_REF,
        },
        "notification_template": cfg.get("notification_template"),
        "timestamp": _utcnow_iso(),
    }


def idle_timeout_minutes(*, seed: dict[str, Any] | None = None) -> int:
    return int((_lifecycle_cfg(seed).get("policy") or {}).get("idle_timeout_minutes", 30))


def absolute_timeout_hours(*, seed: dict[str, Any] | None = None) -> int:
    return int((_lifecycle_cfg(seed).get("policy") or {}).get("absolute_timeout_hours", 8))


def concurrent_session_limit(*, seed: dict[str, Any] | None = None) -> int:
    return int((_lifecycle_cfg(seed).get("policy") or {}).get("concurrent_session_limit", 5))


def compute_absolute_expires_at(
    *,
    created_at: datetime | None = None,
    seed: dict[str, Any] | None = None,
) -> str:
    base = created_at or _utcnow()
    return (base + timedelta(hours=absolute_timeout_hours(seed=seed))).isoformat()


def compute_device_fingerprint(
    *,
    user_agent: str | None = None,
    accept_language: str | None = None,
    ip: str | None = None,
) -> str:
    from password_recovery_hardening import compute_device_fingerprint as _pr_fp

    return _pr_fp(user_agent=user_agent, accept_language=accept_language, ip=ip)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _load_revocation_list() -> dict[str, float]:
    return dict(_load_json(_REVOCATION_PATH))


def _save_revocation_list(data: dict[str, float]) -> None:
    cutoff = time.time() - (absolute_timeout_hours() * 3600)
    pruned = {k: v for k, v in data.items() if v > cutoff}
    _save_json(_REVOCATION_PATH, pruned)


def revoke_token_hash(token_hash: str) -> None:
    with _LOCK:
        revoked = _load_revocation_list()
        revoked[token_hash] = time.time()
        _save_revocation_list(revoked)


def is_token_revoked(token_hash: str) -> bool:
    revoked = _load_revocation_list()
    return token_hash in revoked


def _load_device_store() -> dict[str, list[str]]:
    return {k: list(v) for k, v in _load_json(_DEVICE_STORE_PATH).items()}


def _save_device_store(store: dict[str, list[str]]) -> None:
    _save_json(_DEVICE_STORE_PATH, store)


def is_known_session_device(user_id: int, fingerprint: str) -> bool:
    store = _load_device_store()
    return fingerprint in (store.get(str(user_id)) or [])


def register_session_device(user_id: int, fingerprint: str) -> None:
    with _LOCK:
        store = _load_device_store()
        devices = list(store.get(str(user_id)) or [])
        if fingerprint not in devices:
            devices.append(fingerprint)
            store[str(user_id)] = devices[-20:]
            _save_device_store(store)


async def notify_new_device_login(
    *,
    user_id: int,
    email: str,
    device_fingerprint: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_lifecycle_cfg(seed).get("policy") or {})
    if not policy.get("new_device_email_notification", True):
        return {"notified": False, "reason": "disabled"}
    if is_known_session_device(user_id, device_fingerprint):
        return {"notified": False, "reason": "known_device"}
    from identity_service import enqueue_identity_email

    body = (
        "A new device signed in to your BLACKDARK platform account.\n"
        f"Device fingerprint: {device_fingerprint[:12]}…\n"
        f"Time: {_utcnow_iso()}\n"
        "If this wasn't you, use logout-all and reset your password immediately."
    )
    await enqueue_identity_email(email, "New device sign-in — BLACKDARK", body)
    log_session_event(
        "device-change",
        user_id=user_id,
        email=email,
        device_fingerprint=device_fingerprint,
        detail={"notification": "new_device_email"},
        seed=seed,
    )
    return {"notified": True, "device_fingerprint": device_fingerprint}


def log_session_event(
    event_type: SessionEventType,
    *,
    user_id: int | None = None,
    email: str | None = None,
    ip: str | None = None,
    token_hash: str | None = None,
    device_fingerprint: str | None = None,
    detail: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    event = {
        "event_id": f"sess_{uuid.uuid4().hex[:12]}",
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "event_type": event_type,
        "user_id": user_id,
        "email": email,
        "ip": ip,
        "token_hash_prefix": (token_hash or "")[:16] or None,
        "device_fingerprint": device_fingerprint,
        "detail": detail or {},
        "append_only": True,
        "retention_days": (_lifecycle_cfg(seed).get("policy") or {}).get("audit_retention_days", 730),
        "timestamp": _utcnow_iso(),
        "ts": time.time(),
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logger.debug("session audit persist failed", exc_info=True)
    try:
        from security_events import record_security_event

        record_security_event(
            f"session_{event_type}",
            severity="warning" if event_type in ("global-logout", "idle-timeout", "absolute-timeout") else "info",
            actor=email or (str(user_id) if user_id else None),
            ip=ip,
            detail={"event_id": event["event_id"], **(detail or {})},
        )
    except ImportError:
        pass
    return event


def get_session_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if _AUDIT_PATH.is_file():
        try:
            lines = _AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            rows = [json.loads(x) for x in lines[-limit:] if x.strip()]
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": True,
        "events_count": len(rows),
        "events": rows,
        "append_only": True,
        "retention_days": 730,
        "path": str(_AUDIT_PATH),
        "timestamp": _utcnow_iso(),
    }


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def evaluate_session_expiry(
    *,
    created_at: str | None,
    expires_at: str | None,
    last_activity_at: str | None,
    seed: dict[str, Any] | None = None,
) -> str | None:
    """Return expiry reason or None if session is still valid."""
    seed = seed or _load_seed()
    now = _utcnow()
    created = _parse_iso(created_at)
    absolute_deadline = _parse_iso(expires_at)
    if created:
        policy_deadline = created + timedelta(hours=absolute_timeout_hours(seed=seed))
        if now >= policy_deadline:
            return "absolute-timeout"
    if absolute_deadline and now >= absolute_deadline:
        return "absolute-timeout"
    last = _parse_iso(last_activity_at) or created
    if last and now >= last + timedelta(minutes=idle_timeout_minutes(seed=seed)):
        return "idle-timeout"
    return None


async def enforce_concurrent_session_limit(user_id: int, *, seed: dict[str, Any] | None = None) -> int:
    seed = seed or _load_seed()
    policy = (_lifecycle_cfg(seed).get("policy") or {})
    if not policy.get("invalidate_oldest_on_limit", True):
        return 0
    limit = concurrent_session_limit(seed=seed)
    from database import count_user_sessions, delete_oldest_user_session

    evicted = 0
    while await count_user_sessions(user_id) >= limit:
        removed = await delete_oldest_user_session(user_id)
        if not removed:
            break
        evicted += 1
        log_session_event(
            "concurrent-limit-evict",
            user_id=user_id,
            token_hash=str(removed.get("token") or ""),
            detail={"session_id": removed.get("id")},
            seed=seed,
        )
    return evicted


async def validate_and_touch_session(
    token_hash: str,
    session_row: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Backend-enforced validation on every authenticated request."""
    seed = seed or _load_seed()
    if is_token_revoked(token_hash):
        return None
    reason = evaluate_session_expiry(
        created_at=session_row.get("session_created_at") or session_row.get("created_at"),
        expires_at=session_row.get("session_expires_at") or session_row.get("expires_at"),
        last_activity_at=session_row.get("last_activity_at"),
        seed=seed,
    )
    if reason:
        from database import delete_user_session

        await delete_user_session(token_hash)
        revoke_token_hash(token_hash)
        log_session_event(
            reason,  # type: ignore[arg-type]
            user_id=int(session_row.get("id") or 0) or None,
            email=str(session_row.get("email") or "") or None,
            token_hash=token_hash,
            seed=seed,
        )
        return None
    from database import touch_user_session_activity

    await touch_user_session_activity(token_hash)
    return session_row


def _record_global_logout(user_id: int, ip: str | None = None) -> None:
    with _LOCK:
        state = _load_json(_GLOBAL_LOGOUT_PATH)
        state[str(user_id)] = {"ts": time.time(), "ip": ip or "unknown", "at": _utcnow_iso()}
        _save_json(_GLOBAL_LOGOUT_PATH, state)


def check_suspicious_post_logout_login(
    *,
    user_id: int,
    ip: str | None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#1017 — login shortly after global logout from different IP triggers alert."""
    seed = seed or _load_seed()
    state = _load_json(_GLOBAL_LOGOUT_PATH).get(str(user_id))
    if not state:
        return {"suspicious": False}
    elapsed = time.time() - float(state.get("ts") or 0)
    window = int((_lifecycle_cfg(seed).get("takeover_detection") or {}).get("post_logout_window_seconds", 900))
    if elapsed > window:
        return {"suspicious": False}
    prior_ip = str(state.get("ip") or "")
    if not ip or not prior_ip or ip == prior_ip:
        return {"suspicious": False}
    log_session_event(
        "create",
        user_id=user_id,
        ip=ip,
        detail={"suspicious": True, "reason": "post_global_logout_different_ip", "prior_ip": prior_ip},
        seed=seed,
    )
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829

        record_incident_829(
            scenario="security",
            severity="high",
            title=f"Suspicious login after global logout user_id={user_id}",
            seed=seed,
        )
    except ImportError:
        pass
    return {"suspicious": True, "incident_response_ref": _INCIDENT_RESPONSE_REF}


async def global_logout_all(
    user_id: int,
    *,
    email: str | None = None,
    ip: str | None = None,
    actor: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Kill all platform sessions + revocation list — billing sessions unaffected (#908)."""
    seed = seed or _load_seed()
    from database import delete_user_sessions_for_user, list_user_session_tokens

    tokens = await list_user_session_tokens(user_id)
    revoked = await delete_user_sessions_for_user(user_id)
    for token_hash in tokens:
        revoke_token_hash(token_hash)
    _record_global_logout(user_id, ip=ip)
    log_session_event(
        "global-logout",
        user_id=user_id,
        email=email,
        ip=ip,
        detail={"sessions_revoked": revoked, "actor": actor, "billing_session_isolated": True},
        seed=seed,
    )
    if email:
        try:
            from identity_service import enqueue_identity_email

            template = (_lifecycle_cfg(seed).get("notification_template") or {}).get(
                "global_logout",
                "You have been signed out from all devices on BLACKDARK.",
            )
            body = f"{template}\nTimestamp: {_utcnow_iso()}"
            await enqueue_identity_email(email, "Signed out from all devices — BLACKDARK", body)
        except Exception:
            logger.debug("global logout notification failed", exc_info=True)
    return {
        "ok": True,
        "sessions_revoked": revoked,
        "global_logout": True,
        "billing_session_isolated": True,
        "timestamp": _utcnow_iso(),
    }


async def on_role_change_kill_sessions(
    *,
    user_id: int,
    email: str | None,
    from_role: str,
    to_role: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#1022 — role change invalidates existing sessions (no elevated permissions on stale session)."""
    seed = seed or _load_seed()
    rank = {"viewer": 0, "analyst": 1, "pm": 2, "compliance": 3, "admin": 4}
    if rank.get(to_role, 0) <= rank.get(from_role, 0):
        return {"killed": False, "reason": "not_elevation"}
    result = await global_logout_all(user_id, email=email, actor="rbac_role_change", seed=seed)
    log_session_event(
        "role-change-kill",
        user_id=user_id,
        email=email,
        detail={"from_role": from_role, "to_role": to_role},
        seed=seed,
    )
    return {"killed": True, **result}


async def on_mfa_disable_global_logout(user_id: int, *, email: str | None = None) -> dict[str, Any]:
    """#1033 — disabling 2FA forces global logout + re-auth required."""
    result = await global_logout_all(user_id, email=email, actor="mfa_disable", seed=None)
    log_session_event("mfa-disable-kill", user_id=user_id, email=email)
    return result


async def prepare_new_session(
    user_id: int,
    *,
    email: str | None = None,
    device_fingerprint: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    accept_language: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    if device_fingerprint is None and (user_agent or ip):
        device_fingerprint = compute_device_fingerprint(
            user_agent=user_agent, accept_language=accept_language, ip=ip
        )
    await enforce_concurrent_session_limit(user_id, seed=seed)
    if device_fingerprint and email:
        await notify_new_device_login(
            user_id=user_id,
            email=email,
            device_fingerprint=device_fingerprint,
            seed=seed,
        )
        register_session_device(user_id, device_fingerprint)
    if ip:
        check_suspicious_post_logout_login(user_id=user_id, ip=ip, seed=seed)
    expires_at = compute_absolute_expires_at(seed=seed)
    return {
        "expires_at": expires_at,
        "device_fingerprint": device_fingerprint,
        "last_activity_at": _utcnow_iso(),
    }


def check_session_lifecycle_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = session_lifecycle_status(seed=seed)
    policy = status["policy"]
    checks = {
        "idle_30m": policy["idle_timeout_minutes"] == 30,
        "absolute_8h": policy["absolute_timeout_hours"] == 8,
        "backend_enforced": policy["backend_enforced"] is True,
        "global_logout_endpoint": policy["global_logout_endpoint"] == "/auth/logout-all",
        "device_binding": policy["device_binding_required"] is True,
        "audit_2y": policy["audit_retention_days"] == 730,
        "billing_isolated": policy["billing_session_isolated"] is True,
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "checks": checks,
        "blocks_production": True,
        "timestamp": _utcnow_iso(),
    }


def run_session_lifecycle_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_session_lifecycle_state()

    status = session_lifecycle_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "idle_30m", "passed": status["policy"]["idle_timeout_minutes"] == 30})
    checks.append({"id": "absolute_8h", "passed": status["policy"]["absolute_timeout_hours"] == 8})
    checks.append({"id": "backend_enforced", "passed": status["policy"]["backend_enforced"] is True})
    checks.append({"id": "device_binding", "passed": status["policy"]["device_binding_required"] is True})
    checks.append({"id": "billing_isolated", "passed": status["policy"]["billing_session_isolated"] is True})

    fp = compute_device_fingerprint(user_agent="test", ip="1.2.3.4")
    checks.append({"id": "device_fingerprint", "passed": len(fp) == 32})

    reason = evaluate_session_expiry(
        created_at=(_utcnow() - timedelta(hours=9)).isoformat(),
        expires_at=(_utcnow() + timedelta(hours=1)).isoformat(),
        last_activity_at=_utcnow_iso(),
        seed=seed,
    )
    checks.append({"id": "absolute_expiry", "passed": reason == "absolute-timeout"})

    reason_idle = evaluate_session_expiry(
        created_at=_utcnow_iso(),
        expires_at=compute_absolute_expires_at(seed=seed),
        last_activity_at=(_utcnow() - timedelta(minutes=31)).isoformat(),
        seed=seed,
    )
    checks.append({"id": "idle_expiry", "passed": reason_idle == "idle-timeout"})

    token_hash = "abc123deadbeef"
    revoke_token_hash(token_hash)
    checks.append({"id": "revocation_list", "passed": is_token_revoked(token_hash)})

    log_session_event("create", user_id=1, email="u@example.com", seed=seed)
    audit = get_session_audit_trail(limit=5)
    checks.append({"id": "audit_logged", "passed": audit["events_count"] >= 1})

    gate = check_session_lifecycle_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow_iso(),
    }
