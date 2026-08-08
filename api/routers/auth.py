"""Auth API router."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse

from api.deps import optional_user, record_behavior
from security_auth import is_admin_user, require_admin, require_authenticated
from security_models import AuthLoginBody, AuthRegisterBody, TotpCodeBody

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str, expires_at: str | None = None) -> None:
    secure = (os.getenv("ENV") or "").strip().lower() in {"production", "prod"}
    response.set_cookie(
        key="bd_token",
        value=token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=30 * 24 * 3600,
        path="/",
    )


@router.post("/register")
async def auth_register(body: AuthRegisterBody, background_tasks: BackgroundTasks, response: Response):
    from auth_service import register_user

    try:
        result = await register_user(body.email, body.password, body.name)
        if result.get("token"):
            _set_session_cookie(response, str(result["token"]), result.get("expires_at"))
        background_tasks.add_task(
            record_behavior,
            "auth_register",
            user=result.get("user"),
            payload={"email_domain": body.email.split("@")[-1] if "@" in body.email else ""},
        )
        from observability import increment_metric

        increment_metric("auth_logins_total")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
async def auth_login(body: AuthLoginBody, background_tasks: BackgroundTasks, response: Response):
    from auth_service import login_user

    try:
        result = await login_user(body.email, body.password)
        if result.get("token"):
            _set_session_cookie(response, str(result["token"]), result.get("expires_at"))
        background_tasks.add_task(record_behavior, "auth_login", user=result.get("user"))
        from observability import increment_metric

        increment_metric("auth_logins_total")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
async def auth_logout(response: Response, user: dict | None = Depends(optional_user)):
    from auth_service import logout_user

    if user and user.get("token"):
        await logout_user(str(user["token"]))
    response.delete_cookie("bd_token", path="/")
    return {"success": True}


@router.get("/me")
async def auth_me(user: dict | None = Depends(optional_user)):
    from auth_service import tier_payload
    from database import fetch_active_subscription_for_email, fetch_user_profile
    from oauth_service import oauth_status

    if user is None:
        return {
            "authenticated": False,
            "tier": tier_payload(None),
            "oauth": oauth_status(),
        }
    sub = await fetch_active_subscription_for_email(user["email"])
    profile = await fetch_user_profile(user["email"])
    retention_hint: dict[str, Any] | None = None
    try:
        from retention_service import fetch_live_market_snapshot

        market = await fetch_live_market_snapshot()
        if market.get("bear_market_mode"):
            retention_hint = {
                "bear_market_mode": True,
                "dashboard_mode": market.get("primary_value_pivot"),
                "headline_en": market.get("headline_en"),
            }
    except Exception:
        pass
    return {
        "authenticated": True,
        "user": user,
        "profile": profile,
        "tier": tier_payload(user, sub),
        "subscription": sub,
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "retention_hint": retention_hint,
        "oauth": oauth_status(),
        "is_admin": is_admin_user(user),
    }


@router.patch("/profile")
async def auth_profile_update(
    data: dict = Body(...),
    user: dict | None = Depends(optional_user),
):
    from database import update_user_telegram_chat_id

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    telegram_chat_id = (data.get("telegram_chat_id") or "").strip() or None
    if telegram_chat_id is not None:
        await update_user_telegram_chat_id(user["email"], telegram_chat_id)
    return {"success": True, "telegram_chat_id": telegram_chat_id}


@router.get("/oauth/status")
async def auth_oauth_status():
    from oauth_service import oauth_status

    return oauth_status()


@router.get("/oauth/{provider}/login")
async def auth_oauth_login(provider: str):
    from oauth_service import build_authorize_url

    try:
        payload = build_authorize_url(provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(payload["authorize_url"], status_code=302)


@router.get("/oauth/{provider}/callback")
async def auth_oauth_callback(
    provider: str,
    background_tasks: BackgroundTasks,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    from oauth_service import exchange_code, login_or_register_oauth

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code/state")
    try:
        profile = await exchange_code(provider, code, state)
        result = await login_or_register_oauth(profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OAuth provider failure: {exc}") from exc

    token = str(result["token"])
    # HttpOnly cookie + one-time query bridge for existing localStorage clients.
    redirect = RedirectResponse(url=f"/login?oauth=1&token={token}", status_code=302)
    _set_session_cookie(redirect, token, result.get("expires_at"))
    background_tasks.add_task(record_behavior, "auth_oauth_login", user=result.get("user"))
    return redirect


@router.get("/admin/mfa/status")
async def admin_mfa_status(admin: dict = Depends(require_admin)):
    from admin_mfa import mfa_status

    return {"admin": admin.get("email"), **mfa_status()}


@router.post("/admin/totp/setup")
async def admin_totp_setup(user: dict = Depends(require_authenticated)):
    """Begin TOTP enrollment for an admin email account (pre-MFA gate)."""
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin email required")
    from admin_mfa import enroll_user_totp

    payload = await enroll_user_totp(int(user["id"]), str(user["email"]))
    return {"success": True, **payload}


@router.post("/admin/totp/verify")
async def admin_totp_verify(
    body: TotpCodeBody,
    user: dict = Depends(require_authenticated),
):
    if not is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin email required")
    from admin_mfa import confirm_user_totp

    ok = await confirm_user_totp(int(user["id"]), body.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    return {"success": True, "totp_enabled": True}
