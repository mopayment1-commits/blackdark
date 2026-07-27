"""Auth API router."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException

from api.deps import optional_user, record_behavior
from security_models import AuthLoginBody, AuthRegisterBody

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
        result = await login_user(body.email, body.password)
        background_tasks.add_task(record_behavior, "auth_login", user=result.get("user"))
        from observability import increment_metric

        increment_metric("auth_logins_total")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


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

    if user is None:
        return {"authenticated": False, "tier": tier_payload(None)}
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
