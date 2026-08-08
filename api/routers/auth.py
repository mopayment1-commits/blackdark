"""Auth API router — password, MFA (TOTP), OAuth2."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from api.deps import optional_user, record_behavior
from security_models import (
    AuthLoginBody,
    AuthMfaChallengeBody,
    AuthMfaConfirmBody,
    AuthRegisterBody,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def auth_register(body: AuthRegisterBody, background_tasks: BackgroundTasks):
    from auth_service import register_user

    try:
        result = await register_user(body.email, body.password, body.name)
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
async def auth_login(body: AuthLoginBody, background_tasks: BackgroundTasks):
    from auth_service import login_user

    try:
        result = await login_user(body.email, body.password, mfa_code=body.mfa_code)
        if result.get("mfa_required"):
            return result
        background_tasks.add_task(record_behavior, "auth_login", user=result.get("user"))
        from observability import increment_metric

        increment_metric("auth_logins_total")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/mfa/complete")
async def auth_mfa_complete(body: AuthMfaChallengeBody, background_tasks: BackgroundTasks):
    from auth_service import complete_mfa_login

    try:
        result = await complete_mfa_login(body.challenge, body.code)
        background_tasks.add_task(record_behavior, "auth_login_mfa", user=result.get("user"))
        from observability import increment_metric

        increment_metric("auth_logins_total")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/mfa/status")
async def auth_mfa_status(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    from mfa_service import mfa_status_for_user

    return await mfa_status_for_user(int(user["id"]))


@router.post("/mfa/enroll")
async def auth_mfa_enroll(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    from mfa_service import begin_mfa_enroll

    return await begin_mfa_enroll(int(user["id"]), str(user["email"]))


@router.post("/mfa/confirm")
async def auth_mfa_confirm(
    body: AuthMfaConfirmBody,
    user: dict | None = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    from mfa_service import confirm_mfa_enroll

    try:
        return await confirm_mfa_enroll(int(user["id"]), body.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/mfa/disable")
async def auth_mfa_disable(
    body: AuthMfaConfirmBody,
    user: dict | None = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    from mfa_service import disable_mfa

    try:
        return await disable_mfa(int(user["id"]), body.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/oauth/status")
async def auth_oauth_status():
    from oauth_service import oauth_status

    return oauth_status()


@router.get("/oauth/{provider}/start")
async def auth_oauth_start(provider: str):
    from oauth_service import build_authorize_url

    try:
        payload = build_authorize_url(provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return payload


@router.get("/oauth/{provider}/callback")
async def auth_oauth_callback(
    provider: str,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code")
    from oauth_service import exchange_code, login_or_link_oauth_user

    try:
        profile = await exchange_code(provider, code)
        result = await login_or_link_oauth_user(profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OAuth provider failure: {exc}") from exc

    # Redirect browser sessions to dashboard with token fragment avoided —
    # return JSON for API clients; HTML clients can use ?token= via cookie set below.
    token = result.get("token")
    base = (os.getenv("APP_BASE_URL") or "").rstrip("/")
    if base and token:
        resp = RedirectResponse(url=f"{base}/dashboard?oauth=1", status_code=302)
        resp.set_cookie(
            "bd_token",
            str(token),
            httponly=True,
            samesite="lax",
            secure=base.startswith("https"),
            max_age=60 * 60 * 24 * 30,
        )
        return resp
    return result


@router.post("/logout")
async def auth_logout(user: dict | None = Depends(optional_user)):
    from auth_service import logout_user

    if user and user.get("token"):
        await logout_user(str(user["token"]))
    return {"success": True}


@router.get("/me")
async def auth_me(user: dict | None = Depends(optional_user)):
    from auth_service import tier_payload
    from database import fetch_active_subscription_for_email, fetch_user_profile
    from mfa_service import mfa_status_for_user
    from oauth_service import oauth_status

    if user is None:
        return {"authenticated": False, "tier": tier_payload(None), "oauth": oauth_status()}
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
    mfa = await mfa_status_for_user(int(user["id"]))
    return {
        "authenticated": True,
        "user": user,
        "profile": profile,
        "tier": tier_payload(user, sub),
        "subscription": sub,
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "retention_hint": retention_hint,
        "mfa": mfa,
        "oauth": oauth_status(),
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
