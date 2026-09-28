"""FastAPI dependencies for privileged financial operations."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from privileged_access.operations import ProtectedOperation
from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation
from privileged_access.step_up import issue_step_up_grant
from security_auth import optional_user_from_request, require_authenticated, verify_admin_key


async def require_financial_privilege(
    operation: ProtectedOperation,
    *,
    user: dict,
    org_id: str | None = None,
    resource_owner_id: str | None = None,
    x_admin_totp: str | None = None,
    x_mfa_code: str | None = None,
    x_step_up_token: str | None = None,
    x_admin_key: str | None = None,
    x_actor_email: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    admin_key_used = verify_admin_key(x_admin_key)
    is_admin = bool(user.get("is_admin")) or admin_key_used
    ctx = AuthorizationContext(
        subject_id=str(user.get("id") or user.get("email") or ""),
        subject_email=str(user.get("email") or x_actor_email or ""),
        operation=operation,
        org_id=org_id,
        resource_owner_id=resource_owner_id or (str(user.get("id")) if user.get("id") else None),
        tenant_id=org_id,
        is_admin=is_admin,
    )
    try:
        await authorize_financial_operation(
            ctx,
            user=user,
            x_admin_totp=x_admin_totp,
            x_mfa_code=x_mfa_code,
            x_step_up_token=x_step_up_token,
            admin_key_used=admin_key_used,
            x_actor_email=x_actor_email,
            correlation_id=correlation_id,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.reason}) from exc
    return user


def financial_privilege_dep(operation: ProtectedOperation):
    async def _dep(
        user: Annotated[dict, Depends(require_authenticated)],
        x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
        x_mfa_code: Annotated[str | None, Header(alias="X-MFA-Code")] = None,
        x_step_up_token: Annotated[str | None, Header(alias="X-Step-Up-Token")] = None,
        x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
        x_actor_email: Annotated[str | None, Header(alias="X-Actor-Email")] = None,
        x_correlation_id: Annotated[str | None, Header(alias="X-Correlation-Id")] = None,
        org_id: str | None = None,
    ) -> dict:
        return await require_financial_privilege(
            operation,
            user=user,
            org_id=org_id,
            x_admin_totp=x_admin_totp,
            x_mfa_code=x_mfa_code,
            x_step_up_token=x_step_up_token,
            x_admin_key=x_admin_key,
            x_actor_email=x_actor_email,
            correlation_id=x_correlation_id,
        )

    return _dep


async def issue_step_up_for_user(
    *,
    user: dict,
    operation: ProtectedOperation,
    x_admin_totp: str | None = None,
    x_mfa_code: str | None = None,
) -> dict:
    from admin_mfa import mfa_policy_enabled, verify_system_admin_totp

    subject = str(user.get("id") or user.get("email") or "")
    if mfa_policy_enabled():
        ok = verify_system_admin_totp(x_admin_totp)
        if not ok and user.get("id") and (x_mfa_code or x_admin_totp):
            from mfa_service import verify_user_mfa

            ok = await verify_user_mfa(int(user["id"]), str(x_mfa_code or x_admin_totp))
        if not ok:
            raise HTTPException(status_code=403, detail={"error": "mfa_required_for_step_up"})
    return issue_step_up_grant(subject_id=subject, operation=operation.value)
