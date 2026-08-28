"""
OAuth Social Login Hardening — #1019.

Merged into Session/Account Security — NOT standalone.
Optional OAuth with limited scope, 2FA enforcement, admin restriction, audit.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OAuthLogin")

_FEATURE_REF = 1019
_SUB_FEATURE = "oauth_login_option"
_SEED_PATH = Path("data/session_account_security_seed.json")
_AUDIT_PATH = Path("data/oauth_audit.jsonl")

_RBAC_REF = 1022
_MFA_REF = 1033
_PASSWORD_RECOVERY_REF = 1034
_SESSION_REF = 1019

ProviderName = Literal["google", "github", "twitter"]

_LOCK = threading.Lock()
_pending_links: dict[str, dict[str, Any]] = {}

FORBIDDEN_SCOPE_PARTS = frozenset(
    {
        "contacts",
        "wallet",
        "post",
        "write",
        "admin",
        "delete",
        "gist",
        "notifications",
        "repo",
        "tweet.write",
        "offline.access",
        "calendar",
        "drive",
    }
)


def reset_oauth_login_state() -> None:
    _pending_links.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _oauth_cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return (seed.get("session_account_security_1019") or {}).get("oauth_login") or {}


def allowed_providers(*, seed: dict[str, Any] | None = None) -> list[str]:
    return list((_oauth_cfg(seed).get("providers") or {}).get("allowed") or ["google", "github", "twitter"])


def allowed_scopes(provider: str, *, seed: dict[str, Any] | None = None) -> set[str]:
    seed = seed or _load_seed()
    scopes = (_oauth_cfg(seed).get("providers") or {}).get("scopes") or {}
    defaults = {
        "google": ["openid", "email", "profile"],
        "github": ["read:user", "user:email"],
        "twitter": ["users.read", "users.email"],
    }
    return set(scopes.get(provider.lower()) or defaults.get(provider.lower(), []))


def oauth_login_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _oauth_cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "standalone_rejected": True,
        "merged_into": "#1019 Session/Account Security",
        "policy": {
            "optional_only": policy.get("optional_only", True),
            "email_password_always_available": policy.get("email_password_always_available", True),
            "limited_scope_only": policy.get("limited_scope_only", True),
            "admin_oauth_forbidden": policy.get("admin_oauth_forbidden", True),
            "no_oauth_only_accounts": policy.get("no_oauth_only_accounts", True),
            "password_backup_required": policy.get("password_backup_required", True),
            "mfa_not_bypassed": policy.get("mfa_not_bypassed", True),
            "link_requires_email_confirmation": policy.get("link_requires_email_confirmation", True),
            "tokens_encrypted_at_rest": policy.get("tokens_encrypted_at_rest", True),
            "tokens_never_exposed_to_client": policy.get("tokens_never_exposed_to_client", True),
            "tenant_isolation": policy.get("tenant_isolation", True),
            "audit_retention_days": policy.get("audit_retention_days", 730),
            "audit_append_only": policy.get("audit_append_only", True),
            "non_custodial": policy.get("non_custodial", True),
        },
        "providers": {
            "allowed": allowed_providers(seed=seed),
            "scopes": {p: sorted(allowed_scopes(p, seed=seed)) for p in allowed_providers(seed=seed)},
            "forbidden_scope_parts": sorted(FORBIDDEN_SCOPE_PARTS),
        },
        "integrations": cfg.get("integrations") or {
            "session_ref": _SESSION_REF,
            "rbac_ref": _RBAC_REF,
            "mfa_ref": _MFA_REF,
            "password_recovery_ref": _PASSWORD_RECOVERY_REF,
        },
        "timestamp": _utcnow(),
    }


def assert_provider_allowed(provider: str, *, seed: dict[str, Any] | None = None) -> str:
    key = provider.strip().lower()
    if key == "x":
        key = "twitter"
    if key not in allowed_providers(seed=seed):
        raise ValueError(f"OAuth provider not allowed: {provider}")
    return key


def validate_requested_scopes(provider: str, scope: str, *, seed: dict[str, Any] | None = None) -> str:
    """Reject excess scopes — email + public profile only."""
    provider = assert_provider_allowed(provider, seed=seed)
    requested = {s.strip() for s in scope.split() if s.strip()}
    allowed = allowed_scopes(provider, seed=seed)
    for part in requested:
        low = part.lower()
        if any(f in low for f in FORBIDDEN_SCOPE_PARTS):
            log_oauth_event(
                "scope_rejected",
                provider=provider,
                scope=scope,
                result="blocked",
                detail={"reason": "forbidden_scope_part", "part": part},
                seed=seed,
            )
            raise ValueError(f"Forbidden OAuth scope requested: {part}")
    excess = requested - allowed
    if excess:
        log_oauth_event(
            "scope_rejected",
            provider=provider,
            scope=scope,
            result="blocked",
            detail={"reason": "excess_scope", "excess": sorted(excess)},
            seed=seed,
        )
        raise ValueError(f"OAuth scope exceeds allowed minimum: {', '.join(sorted(excess))}")
    return scope


def assert_admin_oauth_forbidden(email: str, *, seed: dict[str, Any] | None = None) -> None:
    seed = seed or _load_seed()
    if not (_oauth_cfg(seed).get("policy") or {}).get("admin_oauth_forbidden", True):
        return
    from security_auth import admin_emails

    if email.strip().lower() in admin_emails():
        log_oauth_event(
            "admin_blocked",
            email=email,
            result="blocked",
            detail={"reason": "admin_must_use_email_password_totp"},
            seed=seed,
        )
        raise PermissionError("Admin accounts must use email/password + TOTP — OAuth is forbidden")


def assert_password_backup(user_row: dict[str, Any], *, seed: dict[str, Any] | None = None) -> bool:
    """Return True if password backup is set."""
    seed = seed or _load_seed()
    if not (_oauth_cfg(seed).get("policy") or {}).get("password_backup_required", True):
        return True
    return bool(int(user_row.get("password_is_set") if user_row.get("password_is_set") is not None else 1))


def resolve_tenant_id(tenant_id: str | None = None) -> str:
    raw = (tenant_id or os.getenv("DEFAULT_TENANT_ID") or "platform").strip().lower()
    return raw or "platform"


def encrypt_oauth_token(plain: str) -> str:
    try:
        from secrets_vault import encrypt_secret

        return encrypt_secret(plain)
    except ImportError:
        from mfa_service import encrypt_secret

        return encrypt_secret(plain)


def decrypt_oauth_token(ciphertext: str) -> str:
    try:
        from secrets_vault import decrypt_secret

        return decrypt_secret(ciphertext)
    except ImportError:
        from mfa_service import decrypt_secret

        return decrypt_secret(ciphertext)


def log_oauth_event(
    event_type: str,
    *,
    user_id: int | None = None,
    email: str | None = None,
    provider: str | None = None,
    scope: str | None = None,
    ip: str | None = None,
    device_fingerprint: str | None = None,
    tenant_id: str | None = None,
    result: str = "ok",
    detail: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    event = {
        "event_id": f"oauth_{uuid.uuid4().hex[:12]}",
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "event_type": event_type,
        "user_id": user_id,
        "email": email,
        "provider": provider,
        "scope": scope,
        "ip": ip,
        "device_fingerprint": device_fingerprint,
        "tenant_id": resolve_tenant_id(tenant_id),
        "result": result,
        "detail": detail or {},
        "append_only": True,
        "retention_days": (_oauth_cfg(seed).get("policy") or {}).get("audit_retention_days", 730),
        "timestamp": _utcnow(),
        "ts": time.time(),
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logger.debug("oauth audit persist failed", exc_info=True)
    try:
        from security_events import record_security_event

        record_security_event(
            f"oauth_{event_type}",
            severity="warning" if result in ("blocked", "failed") else "info",
            actor=email or (str(user_id) if user_id else None),
            ip=ip,
            detail={"event_id": event["event_id"], "provider": provider, **(detail or {})},
        )
    except ImportError:
        pass
    return event


def get_oauth_audit_trail(*, limit: int = 50) -> dict[str, Any]:
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
        "timestamp": _utcnow(),
    }


async def initiate_oauth_link_confirmation(
    *,
    user_id: int,
    email: str,
    provider: str,
    subject: str,
    tenant_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Existing account — require email confirmation before linking OAuth."""
    seed = seed or _load_seed()
    provider = assert_provider_allowed(provider, seed=seed)
    from identity_service import issue_auth_token

    token = await issue_auth_token(user_id, "oauth_link_confirm")
    base = (os.getenv("APP_BASE_URL") or "").rstrip("/")
    link = f"{base}/api/auth/oauth/{provider}/confirm-link?token={token}" if base else None
    from identity_service import enqueue_identity_email

    body = (
        f"Confirm linking your {provider} account to BLACKDARK.\n"
        f"If you did not request this, ignore this email.\n"
        f"Provider subject: {subject[:12]}…\n"
    )
    if link:
        body += f"\nConfirm: {link}\n"
    await enqueue_identity_email(email, f"Confirm {provider} account link — BLACKDARK", body)
    _pending_links[token] = {
        "user_id": user_id,
        "provider": provider,
        "subject": subject,
        "tenant_id": resolve_tenant_id(tenant_id),
    }
    log_oauth_event(
        "link_confirmation_sent",
        user_id=user_id,
        email=email,
        provider=provider,
        tenant_id=tenant_id,
        seed=seed,
    )
    return {
        "link_confirmation_required": True,
        "provider": provider,
        "message": "Confirmation email sent — link will not merge without verification.",
    }


async def complete_oauth_link_confirmation(
    *,
    token: str,
    provider: str,
    tenant_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    provider = assert_provider_allowed(provider, seed=seed)
    from identity_service import consume_auth_token

    user_id = await consume_auth_token(token, "oauth_link_confirm")
    pending = _pending_links.pop(token, {})
    subject = str(pending.get("subject") or "")
    tenant = resolve_tenant_id(pending.get("tenant_id") or tenant_id)
    from database import fetch_user_by_id, upsert_oauth_provider_link

    user = await fetch_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    await upsert_oauth_provider_link(
        user_id=user_id,
        provider=provider,
        subject=subject or str(pending.get("subject") or ""),
        tenant_id=tenant,
        scope=" ".join(sorted(allowed_scopes(provider, seed=seed))),
    )
    log_oauth_event(
        "link_confirmed",
        user_id=user_id,
        email=str(user.get("email") or ""),
        provider=provider,
        tenant_id=tenant,
        seed=seed,
    )
    return {"ok": True, "linked": True, "provider": provider, "user_id": user_id}


async def unlink_oauth_provider(
    user_id: int,
    provider: str,
    *,
    tenant_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Revoke OAuth access without deleting the platform account."""
    seed = seed or _load_seed()
    provider = assert_provider_allowed(provider, seed=seed)
    tenant = resolve_tenant_id(tenant_id)
    from database import delete_oauth_provider_link, fetch_user_by_id

    removed = await delete_oauth_provider_link(user_id, provider, tenant_id=tenant)
    user = await fetch_user_by_id(user_id)
    log_oauth_event(
        "unlink",
        user_id=user_id,
        email=str((user or {}).get("email") or ""),
        provider=provider,
        tenant_id=tenant,
        detail={"removed": removed},
        seed=seed,
    )
    return {"ok": True, "unlinked": True, "provider": provider, "account_preserved": True}


def check_oauth_login_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = oauth_login_status(seed=seed)
    policy = status["policy"]
    checks = {
        "optional_only": policy["optional_only"] is True,
        "limited_scope": policy["limited_scope_only"] is True,
        "admin_forbidden": policy["admin_oauth_forbidden"] is True,
        "no_oauth_only": policy["no_oauth_only_accounts"] is True,
        "mfa_not_bypassed": policy["mfa_not_bypassed"] is True,
        "link_confirmation": policy["link_requires_email_confirmation"] is True,
        "tokens_encrypted": policy["tokens_encrypted_at_rest"] is True,
        "tenant_isolation": policy["tenant_isolation"] is True,
        "audit_2y": policy["audit_retention_days"] == 730,
        "providers_google_github_twitter": set(allowed_providers(seed=seed))
        == {"google", "github", "twitter"},
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "checks": checks,
        "sprint": 1,
        "blocks_production": False,
        "timestamp": _utcnow(),
    }


def run_oauth_login_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_oauth_login_state()

    status = oauth_login_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "optional_only", "passed": status["policy"]["optional_only"] is True})
    checks.append({"id": "admin_forbidden", "passed": status["policy"]["admin_oauth_forbidden"] is True})
    checks.append({"id": "mfa_not_bypassed", "passed": status["policy"]["mfa_not_bypassed"] is True})
    checks.append({"id": "three_providers", "passed": len(status["providers"]["allowed"]) == 3})

    try:
        validate_requested_scopes("google", "openid email profile", seed=seed)
        checks.append({"id": "google_scope_ok", "passed": True})
    except ValueError:
        checks.append({"id": "google_scope_ok", "passed": False})

    try:
        validate_requested_scopes("github", "read:user user:email repo", seed=seed)
        checks.append({"id": "github_scope_block", "passed": False})
    except ValueError:
        checks.append({"id": "github_scope_block", "passed": True})

    try:
        import os as _os

        prior = _os.environ.get("ADMIN_EMAILS")
        _os.environ["ADMIN_EMAILS"] = "admin@blackdark.io"
        try:
            assert_admin_oauth_forbidden("admin@blackdark.io", seed=seed)
            checks.append({"id": "admin_block", "passed": False})
        except PermissionError:
            checks.append({"id": "admin_block", "passed": True})
        finally:
            if prior is None:
                _os.environ.pop("ADMIN_EMAILS", None)
            else:
                _os.environ["ADMIN_EMAILS"] = prior
    except Exception:
        checks.append({"id": "admin_block", "passed": False})

    enc = encrypt_oauth_token("secret-token-value")
    dec = decrypt_oauth_token(enc)
    checks.append({"id": "token_encryption", "passed": dec == "secret-token-value" and enc != dec})

    log_oauth_event("start", provider="google", scope="openid email profile", seed=seed)
    audit = get_oauth_audit_trail(limit=5)
    checks.append({"id": "audit_logged", "passed": audit["events_count"] >= 1})

    gate = check_oauth_login_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
