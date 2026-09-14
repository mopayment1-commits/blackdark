"""Financial privileged authorization policy engine (FDS-10/11/12)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from privileged_access.break_glass import active_break_glass_for_actor
from privileged_access.detectors import (
    check_audit_bypass_env,
    detect_bulk_financial_export,
    detect_repeated_denied_financial_access,
)
from privileged_access.operations import ProtectedOperation, operation_spec
from privileged_access.sessions import elevate_privileged_session, require_fresh_privileged_session
from privileged_access.step_up import verify_step_up_grant
from security_events import record_security_event


@dataclass
class AuthorizationContext:
    subject_id: str
    subject_email: str
    operation: ProtectedOperation
    org_id: str | None = None
    resource_owner_id: str | None = None
    tenant_id: str | None = None
    is_admin: bool = False
    attribution_email: str | None = None


class AuthorizationDenied(PermissionError):
    def __init__(self, reason: str, *, status_code: int = 403):
        self.reason = reason
        self.status_code = status_code
        super().__init__(reason)


def _subject_key(ctx: AuthorizationContext) -> str:
    return str(ctx.subject_id or ctx.subject_email)


async def _mfa_satisfied(
    *,
    user: dict | None,
    x_admin_totp: str | None,
    x_mfa_code: str | None,
) -> bool:
    from admin_mfa import mfa_policy_enabled, verify_system_admin_totp

    if not mfa_policy_enabled():
        return True
    if verify_system_admin_totp(x_admin_totp):
        return True
    code = x_mfa_code or x_admin_totp
    if user and user.get("id") and code:
        from mfa_service import verify_user_mfa

        if await verify_user_mfa(int(user["id"]), str(code)):
            return True
    return False


def _shared_admin_key_requires_attribution(
    *,
    admin_key_used: bool,
    user: dict | None,
    x_actor_email: str | None,
) -> str:
    """SDG-07 — shared admin API key must not act without individual attribution."""
    if not admin_key_used:
        return str((user or {}).get("email") or "")
    actor = (x_actor_email or (user or {}).get("email") or "").strip().lower()
    if not actor:
        if os.getenv("ENV", "").lower() in {"production", "prod"} or os.getenv("APP_ENV", "").lower() in {"production", "prod"}:
            raise AuthorizationDenied("shared_admin_key_requires_x_actor_email", status_code=403)
        actor = "shared-admin-key@attribution-required.local"
    return actor


def _resource_owner_ok(ctx: AuthorizationContext) -> bool:
    if not ctx.resource_owner_id:
        return True
    return str(ctx.resource_owner_id) == str(ctx.subject_id)


def _tenant_permission_ok(ctx: AuthorizationContext, permission: str | None) -> bool:
    if not permission:
        return True
    if not ctx.org_id:
        return ctx.is_admin
    try:
        from org_rbac import has_permission

        return has_permission(ctx.org_id, ctx.subject_email, permission)
    except Exception:
        return False


async def authorize_financial_operation(
    ctx: AuthorizationContext,
    *,
    user: dict | None = None,
    x_admin_totp: str | None = None,
    x_mfa_code: str | None = None,
    x_step_up_token: str | None = None,
    admin_key_used: bool = False,
    x_actor_email: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    check_audit_bypass_env()
    spec = operation_spec(ctx.operation)
    actor_email = _shared_admin_key_requires_attribution(
        admin_key_used=admin_key_used,
        user=user,
        x_actor_email=x_actor_email,
    )
    ctx = AuthorizationContext(
        subject_id=ctx.subject_id,
        subject_email=actor_email or ctx.subject_email,
        operation=ctx.operation,
        org_id=ctx.org_id,
        resource_owner_id=ctx.resource_owner_id,
        tenant_id=ctx.tenant_id,
        is_admin=ctx.is_admin,
        attribution_email=actor_email,
    )
    subject = _subject_key(ctx)

    if spec.resource_owner_required and not _resource_owner_ok(ctx):
        detect_repeated_denied_financial_access(actor=ctx.subject_email, operation=spec.operation.value)
        raise AuthorizationDenied("resource_owner_mismatch", status_code=403)

    if spec.org_permission and not _tenant_permission_ok(ctx, spec.org_permission):
        if not (ctx.is_admin and active_break_glass_for_actor(subject)):
            detect_repeated_denied_financial_access(actor=ctx.subject_email, operation=spec.operation.value)
            raise AuthorizationDenied("missing_org_permission", status_code=403)

    if spec.mfa_required:
        if not await _mfa_satisfied(user=user, x_admin_totp=x_admin_totp, x_mfa_code=x_mfa_code):
            detect_repeated_denied_financial_access(actor=ctx.subject_email, operation=spec.operation.value)
            raise AuthorizationDenied("mfa_required", status_code=403)

    if spec.step_up_required:
        if not verify_step_up_grant(token=x_step_up_token, subject_id=subject, operation=spec.operation.value):
            detect_repeated_denied_financial_access(actor=ctx.subject_email, operation=spec.operation.value)
            raise AuthorizationDenied("step_up_required", status_code=403)

    if spec.privileged_session and not require_fresh_privileged_session(subject):
        elevate_privileged_session(subject_id=subject, operation=spec.operation.value, auth_strength="mfa+step_up")
    elif spec.privileged_session:
        elevate_privileged_session(subject_id=subject, operation=spec.operation.value, auth_strength="step_up")

    if spec.resource_class in {"financial_export", "financial_erasure"}:
        detect_bulk_financial_export(
            actor=ctx.subject_email,
            resource_class=spec.resource_class,
            correlation_id=correlation_id,
        )

    record_security_event(
        "privileged_financial_access",
        severity="info",
        actor=ctx.subject_email,
        detail={
            "operation": spec.operation.value,
            "resource_class": spec.resource_class,
            "org_id": ctx.org_id,
            "tenant_id": ctx.tenant_id,
            "correlation_id": correlation_id,
            "attribution_email": ctx.attribution_email,
        },
    )
    try:
        from audit_registry import record_audit_log

        await record_audit_log(
            actor=ctx.subject_email,
            action=f"privileged:{spec.operation.value}",
            outcome="allowed",
            metadata={
                "resource_class": spec.resource_class,
                "org_id": ctx.org_id,
                "tenant_id": ctx.tenant_id,
                "correlation_id": correlation_id,
            },
        )
    except Exception:
        pass
    return {
        "authorized": True,
        "operation": spec.operation.value,
        "subject": subject,
        "attribution_email": ctx.attribution_email,
    }


def deny_http(exc: AuthorizationDenied) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"error": exc.reason})
