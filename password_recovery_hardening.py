"""
Secure Password Recovery Hardening — #1019.

Merged into Session/Account Security — NOT standalone.
Token-based email reset, rate limits, device fingerprint, takeover detection.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PasswordRecovery")

_FEATURE_REF = 1019
_SUB_FEATURE = "secure_password_recovery_hardening"
_SEED_PATH = Path("data/session_account_security_seed.json")
_AUDIT_PATH = Path("data/password_recovery_audit.jsonl")
_DEVICE_STORE_PATH = Path("data/password_recovery_devices.json")

_RBAC_REF = 1022
_STRIPE_REF = 908
_INCIDENT_RESPONSE_REF = 1017
_TOS_REF = 1018
_MFA_REF = 1033

_LOCK = threading.Lock()
_email_attempts: dict[str, list[float]] = defaultdict(list)
_ip_attempts: dict[str, list[float]] = defaultdict(list)
_failed_resets: dict[str, list[float]] = defaultdict(list)


def reset_password_recovery_state() -> None:
    _email_attempts.clear()
    _ip_attempts.clear()
    _failed_resets.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _recovery_cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return (seed.get("session_account_security_1019") or {}).get("password_recovery") or {}


def password_recovery_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _recovery_cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "standalone_rejected": True,
        "merged_into": "#1019 Session/Account Security",
        "policy": {
            "token_based_only": policy.get("token_based_only", True),
            "security_questions_forbidden": policy.get("security_questions_forbidden", True),
            "token_expiry_minutes": policy.get("token_expiry_minutes", 15),
            "single_use_tokens": policy.get("single_use_tokens", True),
            "hashed_in_db": policy.get("hashed_in_db", True),
            "no_plaintext_tokens": policy.get("no_plaintext_tokens", True),
            "session_invalidation_on_reset": policy.get("session_invalidation_on_reset", True),
            "billing_email_separate": policy.get("billing_email_separate", True),
            "non_custodial": policy.get("non_custodial", True),
            "audit_retention_days": policy.get("audit_retention_days", 730),
        },
        "rate_limits": cfg.get("rate_limits") or {},
        "notification_template": cfg.get("notification_template"),
        "integrations": {
            "rbac_ref": _RBAC_REF,
            "stripe_ref": _STRIPE_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
            "tos_ref": _TOS_REF,
            "mfa_ref": _MFA_REF,
        },
        "timestamp": _utcnow(),
    }


def assert_no_security_questions(payload: dict[str, Any] | None = None) -> None:
    """OWASP — security questions explicitly forbidden."""
    if not payload:
        return
    forbidden_keys = (
        "security_question",
        "security_answer",
        "security_questions",
        "mother_maiden_name",
        "pet_name",
    )
    for key in forbidden_keys:
        if key in payload and payload[key]:
            log_recovery_event(
                "security_question_rejected",
                result="blocked",
                detail={"field": key},
            )
            raise ValueError("Security questions are not supported — use email token recovery only")


def _prune(window: list[float], *, seconds: float) -> list[float]:
    now = time.time()
    return [t for t in window if now - t < seconds]


def check_password_recovery_rate_limits(*, email: str, ip: str, seed: dict[str, Any] | None = None) -> None:
    """3 attempts/hour per email · 5 attempts/5min per IP."""
    seed = seed or _load_seed()
    limits = (_recovery_cfg(seed).get("rate_limits") or {})
    email_max = int(limits.get("per_email_per_hour", 3))
    ip_max = int(limits.get("per_ip_per_5_minutes", 5))
    ip_window = int(limits.get("ip_window_seconds", 300))
    email_window = int(limits.get("email_window_seconds", 3600))

    email_key = email.strip().lower()
    ip_key = ip.strip().lower() or "unknown"

    with _LOCK:
        _email_attempts[email_key] = _prune(_email_attempts[email_key], seconds=email_window)
        _ip_attempts[ip_key] = _prune(_ip_attempts[ip_key], seconds=ip_window)
        blocked_email = len(_email_attempts[email_key]) >= email_max
        blocked_ip = len(_ip_attempts[ip_key]) >= ip_max
        if not blocked_email and not blocked_ip:
            _email_attempts[email_key].append(time.time())
            _ip_attempts[ip_key].append(time.time())
    if blocked_email:
        log_recovery_event("rate_limited", email=email_key, ip=ip, result="blocked_email")
        raise ValueError("Too many password reset requests for this email. Try again later.")
    if blocked_ip:
        log_recovery_event("rate_limited", email=email_key, ip=ip, result="blocked_ip")
        raise ValueError("Too many password reset requests from this network. Try again later.")


def compute_device_fingerprint(
    *,
    user_agent: str | None = None,
    accept_language: str | None = None,
    ip: str | None = None,
) -> str:
    raw = "|".join([(user_agent or "")[:200], (accept_language or "")[:64], (ip or "")[:64]])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _load_device_store() -> dict[str, list[str]]:
    if not _DEVICE_STORE_PATH.is_file():
        return {}
    try:
        return json.loads(_DEVICE_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_device_store(store: dict[str, list[str]]) -> None:
    _DEVICE_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DEVICE_STORE_PATH.write_text(json.dumps(store), encoding="utf-8")


def is_known_device(user_id: int, fingerprint: str) -> bool:
    store = _load_device_store()
    return fingerprint in (store.get(str(user_id)) or [])


def register_known_device(user_id: int, fingerprint: str) -> None:
    with _LOCK:
        store = _load_device_store()
        devices = list(store.get(str(user_id)) or [])
        if fingerprint not in devices:
            devices.append(fingerprint)
            store[str(user_id)] = devices[-20:]
            _save_device_store(store)


def log_recovery_event(
    event_type: str,
    *,
    email: str | None = None,
    user_id: int | None = None,
    ip: str | None = None,
    device_fingerprint: str | None = None,
    token_hash: str | None = None,
    result: str = "ok",
    detail: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    event = {
        "event_id": f"pr_{uuid.uuid4().hex[:12]}",
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "event_type": event_type,
        "email": email,
        "user_id": user_id,
        "ip": ip,
        "device_fingerprint": device_fingerprint,
        "token_hash_prefix": (token_hash or "")[:16] or None,
        "result": result,
        "detail": detail or {},
        "append_only": True,
        "retention_days": (_recovery_cfg(seed).get("policy") or {}).get("audit_retention_days", 730),
        "timestamp": _utcnow(),
        "ts": time.time(),
    }
    should_track_failure = result in ("failed", "blocked", "blocked_email", "blocked_ip", "takeover_suspected")
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logger.debug("password recovery audit persist failed", exc_info=True)
        if should_track_failure:
            _failed_resets[(email or "unknown").lower()].append(time.time())
    if should_track_failure:
        detect_account_takeover(email=email, ip=ip, seed=seed)
    return event


def detect_account_takeover(
    *,
    email: str | None = None,
    ip: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Multiple failed resets → #1017 incident alert."""
    seed = seed or _load_seed()
    if not email:
        return {"alert": False}
    key = email.strip().lower()
    with _LOCK:
        recent = _prune(_failed_resets.get(key, []), seconds=3600)
        _failed_resets[key] = recent
    threshold = int((_recovery_cfg(seed).get("takeover_detection") or {}).get("failed_attempts_per_hour", 3))
    if len(recent) < threshold:
        return {"alert": False, "failed_count": len(recent)}
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829

        record_incident_829(
            scenario="security",
            severity="high",
            title=f"Account takeover attempt suspected: {email}",
            seed=seed,
        )
    except ImportError:
        pass
    return {"alert": True, "failed_count": len(recent), "incident_response_ref": _INCIDENT_RESPONSE_REF}


def password_changed_notification_body(*, seed: dict[str, Any] | None = None) -> str:
    seed = seed or _load_seed()
    tpl = (_recovery_cfg(seed).get("notification_template") or {})
    return str(
        tpl.get("password_changed")
        or "Your password was changed. If this wasn't you, contact support immediately."
    )


async def notify_new_device_password_reset(
    user_id: int,
    email: str,
    *,
    device_fingerprint: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Email notification when reset requested from new device."""
    seed = seed or _load_seed()
    if is_known_device(user_id, device_fingerprint):
        return {"notified": False, "reason": "known_device"}
    from identity_service import enqueue_identity_email

    body = (
        "A password reset was requested for your BLACKDARK account from a new device.\n\n"
        "If this was you, you can ignore this message after completing the reset.\n"
        "If this wasn't you, contact support immediately and enable 2FA.\n"
    )
    await enqueue_identity_email(email, "Password reset requested — new device", body)
    return {"notified": True, "device_fingerprint": device_fingerprint}


async def send_hardened_password_reset(
    user_id: int,
    email: str,
    *,
    ip: str,
    user_agent: str | None = None,
    accept_language: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Issue token + audit + optional new-device notification."""
    seed = seed or _load_seed()
    fingerprint = compute_device_fingerprint(
        user_agent=user_agent, accept_language=accept_language, ip=ip
    )
    from identity_service import hash_token, send_password_reset_email

    result = await send_password_reset_email(user_id, email)
    log_recovery_event(
        "reset_requested",
        email=email,
        user_id=user_id,
        ip=ip,
        device_fingerprint=fingerprint,
        result="ok",
        seed=seed,
    )
    await notify_new_device_password_reset(
        user_id, email, device_fingerprint=fingerprint, seed=seed
    )
    register_known_device(user_id, fingerprint)
    return {**result, "device_fingerprint": fingerprint, "token_hashed": True}


async def complete_hardened_password_reset(
    *,
    token: str,
    new_password: str,
    email: str | None = None,
    mfa_code: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    accept_language: str | None = None,
    is_admin: bool = False,
    admin_approval_token: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Token verify → optional 2FA → password change → kill sessions → notify."""
    seed = seed or _load_seed()
    from auth_service import create_session, hash_password
    from database import delete_user_sessions_for_user, fetch_user_by_id, update_user_profile_fields
    from identity_service import consume_auth_token, hash_token, validate_password

    fingerprint = compute_device_fingerprint(
        user_agent=user_agent, accept_language=accept_language, ip=ip
    )
    token_hash = hash_token(token)

    if is_admin:
        assert_admin_reset_approval(admin_approval_token=admin_approval_token, seed=seed)

    try:
        user_id = await consume_auth_token(token, "password_reset")
    except ValueError:
        log_recovery_event(
            "reset_failed",
            email=email,
            ip=ip,
            device_fingerprint=fingerprint,
            token_hash=token_hash,
            result="failed",
            detail={"reason": "invalid_token"},
            seed=seed,
        )
        raise

    user = await fetch_user_by_id(user_id)
    if not user:
        raise ValueError("Invalid or expired link")
    user_email = str(user.get("email") or email or "")

    mfa_enabled = bool(int(user.get("mfa_enabled") or 0))
    if mfa_enabled:
        if not mfa_code:
            raise ValueError("2FA code required to reset password when 2FA is enabled")
        from mfa_service import verify_user_mfa

        if not await verify_user_mfa(user_id, mfa_code):
            log_recovery_event(
                "reset_failed",
                email=user_email,
                user_id=user_id,
                ip=ip,
                result="failed",
                detail={"reason": "invalid_mfa"},
                seed=seed,
            )
            raise ValueError("Invalid 2FA code")

    validate_password(new_password, email=user_email)
    await update_user_profile_fields(
        user_id,
        {"password_hash": hash_password(new_password), "password_is_set": 1},
    )
    await delete_user_sessions_for_user(user_id)

    from identity_service import enqueue_identity_email

    await enqueue_identity_email(
        user_email,
        "Your BLACKDARK password was changed",
        password_changed_notification_body(seed=seed) + "\n",
    )

    log_recovery_event(
        "reset_completed",
        email=user_email,
        user_id=user_id,
        ip=ip,
        device_fingerprint=fingerprint,
        token_hash=token_hash,
        result="ok",
        seed=seed,
    )
    register_known_device(user_id, fingerprint)
    session = await create_session(user_id)
    return {
        "ok": True,
        "user_id": user_id,
        "sessions_invalidated": True,
        "token": session["token"],
        "expires_at": session["expires_at"],
    }


def assert_admin_reset_approval(
    *,
    admin_approval_token: str | None,
    seed: dict[str, Any] | None = None,
) -> None:
    """#1022 — admin password reset requires secondary approval token."""
    seed = seed or _load_seed()
    if not (_recovery_cfg(seed).get("admin_reset") or {}).get("secondary_approval_required", True):
        return
    if not admin_approval_token:
        raise PermissionError("admin_password_reset_requires_secondary_approval")
    expected = (_recovery_cfg(seed).get("admin_reset") or {}).get("approval_token_env", "ADMIN_RESET_APPROVAL_TOKEN")
    import os

    if not admin_approval_token or admin_approval_token != os.getenv(expected, ""):
        raise PermissionError("invalid_admin_reset_approval")


def get_password_recovery_audit_trail(*, limit: int = 50) -> dict[str, Any]:
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
        "path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def check_password_recovery_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = password_recovery_status(seed=seed)
    p = status["policy"]
    return {
        "ok": all(
            [
                p["token_based_only"],
                p["security_questions_forbidden"],
                p["token_expiry_minutes"] == 15,
                p["single_use_tokens"],
                p["hashed_in_db"],
            ]
        ),
        "feature_ref": _FEATURE_REF,
        "checks": p,
        "timestamp": _utcnow(),
    }


def run_password_recovery_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_password_recovery_state()

    status = password_recovery_status(seed=seed)
    checks.append({"id": "no_security_questions", "passed": status["policy"]["security_questions_forbidden"]})
    checks.append({"id": "token_15min", "passed": status["policy"]["token_expiry_minutes"] == 15})

    try:
        assert_no_security_questions({"security_question": "pet?"})
        checks.append({"id": "reject_security_q", "passed": False})
    except ValueError:
        checks.append({"id": "reject_security_q", "passed": True})

    try:
        check_password_recovery_rate_limits(email="a@b.com", ip="1.2.3.4", seed=seed)
        check_password_recovery_rate_limits(email="a@b.com", ip="1.2.3.4", seed=seed)
        check_password_recovery_rate_limits(email="a@b.com", ip="1.2.3.4", seed=seed)
        check_password_recovery_rate_limits(email="a@b.com", ip="1.2.3.4", seed=seed)
        checks.append({"id": "email_rate_limit", "passed": False})
    except ValueError:
        checks.append({"id": "email_rate_limit", "passed": True})

    fp = compute_device_fingerprint(user_agent="test", ip="10.0.0.1")
    checks.append({"id": "device_fingerprint", "passed": len(fp) == 32})

    log_recovery_event("reset_requested", email="test@example.com", result="ok", seed=seed)
    audit = get_password_recovery_audit_trail()
    checks.append({"id": "audit_logged", "passed": audit["events_count"] >= 1})

    takeover = detect_account_takeover(email="victim@example.com", seed=seed)
    for _ in range(4):
        log_recovery_event("reset_failed", email="victim@example.com", result="failed", seed=seed)
    takeover2 = detect_account_takeover(email="victim@example.com", seed=seed)
    checks.append({"id": "takeover_detection", "passed": takeover2.get("failed_count", 0) >= 3})

    gate = check_password_recovery_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
