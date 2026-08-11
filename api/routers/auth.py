"""Auth API router — password, MFA (TOTP), OAuth2, recovery, profile."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse, RedirectResponse, Response as RawResponse

from api.deps import optional_user, raw_bearer_or_cookie, record_behavior
from security_models import (
    AuthChangePasswordBody,
    AuthForgotPasswordBody,
    AuthLoginBody,
    AuthMfaChallengeBody,
    AuthMfaConfirmBody,
    AuthProfileUpdateBody,
    AuthRegisterBody,
    AuthResetPasswordBody,
)

# Sonar S1192: duplicated string literals
STR_LOGIN_REQUIRED = 'Login required'

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _attach_session_cookie(response: Response, token: str | None) -> None:
    if not token:
        return
    from security_middleware import attach_session_cookie

    # Opaque session bearer (secrets.token_urlsafe) — never a password.
    attach_session_cookie(response, str(token))


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie("bd_token", path="/")


@router.get("/identity")
async def auth_identity_architecture():
    from identity_service import identity_architecture

    return identity_architecture()


@router.post("/register")
async def auth_register(body: AuthRegisterBody, background_tasks: BackgroundTasks):
    from auth_service import register_user
    from security_auth import check_login_rate_limit

    try:
        check_login_rate_limit(f"register:{body.email.lower()}")
        result = await register_user(
            body.email,
            body.password,
            body.name,
            username=body.username,
            accepted_terms=body.accepted_terms,
            plan=body.plan,
        )
        background_tasks.add_task(
            record_behavior,
            "auth_register",
            user=result.get("user"),
            payload={
                "email_domain": body.email.split("@")[-1] if "@" in body.email else "",
                "selected_plan": result.get("selected_plan"),
            },
        )
        from observability import increment_metric

        increment_metric("auth_logins_total")
        resp = JSONResponse(result)
        _attach_session_cookie(resp, result.get("token"))
        return resp
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
async def auth_login(
    body: AuthLoginBody,
    request: Request,
    background_tasks: BackgroundTasks,
):
    from auth_service import login_user
    from security_auth import check_login_rate_limit

    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip and request.client:
        ip = request.client.host or "unknown"
    check_login_rate_limit(f"ip:{ip}")
    try:
        result = await login_user(body.email, body.password, mfa_code=body.mfa_code)
        if result.get("mfa_required"):
            return result
        background_tasks.add_task(record_behavior, "auth_login", user=result.get("user"))
        from observability import increment_metric

        increment_metric("auth_logins_total")
        resp = JSONResponse(result)
        _attach_session_cookie(resp, result.get("token"))
        return resp
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
        resp = JSONResponse(result)
        _attach_session_cookie(resp, result.get("token"))
        return resp
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/mfa/status")
async def auth_mfa_status(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from mfa_service import mfa_status_for_user

    return await mfa_status_for_user(int(user["id"]))


@router.post("/mfa/enroll")
async def auth_mfa_enroll(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from mfa_service import begin_mfa_enroll

    return await begin_mfa_enroll(int(user["id"]), str(user["email"]))


@router.post("/mfa/confirm")
async def auth_mfa_confirm(
    body: AuthMfaConfirmBody,
    user: dict | None = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
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
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from mfa_service import disable_mfa

    try:
        return await disable_mfa(int(user["id"]), body.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/forgot-password")
async def auth_forgot_password(body: AuthForgotPasswordBody, request: Request):
    """Always returns generic success to avoid account enumeration."""
    from database import fetch_user_by_email
    from identity_service import send_password_reset_email, validate_email
    from security_auth import check_login_rate_limit

    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or "unknown"
    check_login_rate_limit(f"forgot:{ip}")
    try:
        email = validate_email(body.email)
    except ValueError:
        return {
            "ok": True,
            "message": "If an account exists for that email, a reset link was sent.",
        }
    user = await fetch_user_by_email(email)
    debug: dict[str, Any] = {}
    if user and int(user.get("password_is_set") if user.get("password_is_set") is not None else 1):
        try:
            debug = await send_password_reset_email(int(user["id"]), email)
        except Exception:
            pass
    payload = {
        "ok": True,
        "message": "If an account exists for that email, a reset link was sent.",
    }
    if debug.get("debug_token"):
        payload["debug_token"] = debug["debug_token"]
        payload["debug_link"] = debug.get("debug_link")
    return payload


@router.post("/reset-password")
async def auth_reset_password(body: AuthResetPasswordBody):
    from auth_service import create_session, hash_password
    from database import (
        delete_user_sessions_for_user,
        fetch_user_by_id,
        update_user_profile_fields,
    )
    from identity_service import consume_auth_token, validate_password

    try:
        user_id = await consume_auth_token(body.token, "password_reset")
        user = await fetch_user_by_id(user_id)
        if not user:
            raise ValueError("Invalid or expired link")
        email = str(user["email"])
        validate_password(body.password, email=email)
        await update_user_profile_fields(
            user_id,
            {
                "password_hash": hash_password(body.password),
                "password_is_set": 1,
            },
        )
        await delete_user_sessions_for_user(user_id)
        session = await create_session(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    resp = JSONResponse(
        {
            "ok": True,
            "message": "Password updated. You are signed in.",
            "token": session["token"],
            "expires_at": session["expires_at"],
            "user": {"id": user_id, "email": email, "name": user.get("name") or ""},
        }
    )
    _attach_session_cookie(resp, session["token"])
    return resp


@router.post("/change-password")
async def auth_change_password(
    body: AuthChangePasswordBody,
    user: dict | None = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from auth_service import hash_password, verify_password
    from database import (
        delete_user_sessions_for_user,
        fetch_user_by_id,
        update_user_profile_fields,
    )
    from identity_service import validate_password

    row = await fetch_user_by_id(int(user["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    password_is_set = bool(int(row.get("password_is_set") if row.get("password_is_set") is not None else 1))
    if password_is_set and not verify_password(
        body.current_password, str(row.get("password_hash") or "")
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    try:
        validate_password(body.new_password, email=str(row["email"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await update_user_profile_fields(
        int(user["id"]),
        {"password_hash": hash_password(body.new_password), "password_is_set": 1},
    )
    await delete_user_sessions_for_user(int(user["id"]))
    from auth_service import create_session

    session = await create_session(int(user["id"]))
    resp = JSONResponse({"ok": True, "token": session["token"], "expires_at": session["expires_at"]})
    _attach_session_cookie(resp, session["token"])
    return resp


@router.get("/verify-email")
async def auth_verify_email(token: str = Query(...)):
    from database import mark_email_verified
    from identity_service import consume_auth_token

    safe = "".join(ch for ch in str(token) if ch.isalnum() or ch in "-_.")
    if len(safe) < 16:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    try:
        user_id = await consume_auth_token(safe, "email_verify")
        await mark_email_verified(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token") from None
    return RedirectResponse(url="/profile?verified=1", status_code=302)


@router.post("/resend-verification")
async def auth_resend_verification(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    if user.get("email_verified"):
        return {"ok": True, "message": "Email already verified"}
    from identity_service import send_verification_email

    result = await send_verification_email(int(user["id"]), str(user["email"]))
    payload = {"ok": True, "message": "Verification email sent if still pending."}
    if result.get("debug_token"):
        payload["debug_token"] = result["debug_token"]
        payload["debug_link"] = result.get("debug_link")
    return payload


@router.post("/forgot-username")
async def auth_forgot_username(body: AuthForgotPasswordBody, request: Request):
    """Remind the user that login uses email (no separate username secret)."""
    from database import fetch_user_by_email
    from identity_service import enqueue_identity_email, validate_email
    from security_auth import check_login_rate_limit

    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or "unknown"
    check_login_rate_limit(f"forgot-user:{ip}")
    try:
        email = validate_email(body.email)
    except ValueError:
        return {"ok": True, "message": "If an account exists, a reminder was sent."}
    user = await fetch_user_by_email(email)
    if user:
        handle = user.get("username") or "(not set)"
        await enqueue_identity_email(
            email,
            "Your BLACKDARK login reminder",
            (
                "BLACKDARK login uses your email address.\n\n"
                f"Email: {email}\n"
                f"Public username (optional): @{handle}\n\n"
                "Use Forgot password if you need to reset access.\n"
            ),
        )
    return {"ok": True, "message": "If an account exists, a reminder was sent."}


@router.get("/oauth/status")
async def auth_oauth_status():
    from oauth_service import oauth_status

    return oauth_status()


@router.get("/oauth/{provider}/start")
async def auth_oauth_start(provider: str):
    from identity_service import store_oauth_state_async
    from oauth_service import build_authorize_url

    try:
        payload = build_authorize_url(provider)
        await store_oauth_state_async(provider, payload["state"])
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
    from identity_service import validate_oauth_state_async
    from oauth_service import exchange_code, login_or_link_oauth_user

    try:
        await validate_oauth_state_async(provider, state)
        profile = await exchange_code(provider, code)
        result = await login_or_link_oauth_user(profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OAuth provider failure: {exc}") from exc

    token = result.get("token")
    base = (os.getenv("APP_BASE_URL") or "").rstrip("/")
    if base and token:
        resp = RedirectResponse(url=f"{base}/dashboard?oauth=1", status_code=302)
        _attach_session_cookie(resp, str(token))
        return resp
    resp = JSONResponse(result)
    _attach_session_cookie(resp, token)
    return resp


@router.post("/logout")
async def auth_logout(
    token: str | None = Depends(raw_bearer_or_cookie),
):
    from auth_service import logout_user

    if token:
        await logout_user(str(token))
    resp = JSONResponse({"success": True})
    _clear_session_cookie(resp)
    return resp


@router.post("/logout-all")
async def auth_logout_all(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import delete_user_sessions_for_user

    await delete_user_sessions_for_user(int(user["id"]))
    resp = JSONResponse({"ok": True, "message": "All sessions revoked. Please log in again."})
    _clear_session_cookie(resp)
    return resp


@router.get("/me")
async def auth_me(user: dict | None = Depends(optional_user)):
    from auth_service import tier_payload
    from database import fetch_active_subscription_for_email, fetch_user_profile
    from identity_service import avatar_initials, identity_architecture
    from mfa_service import mfa_status_for_user
    from oauth_service import oauth_status

    if user is None:
        return {
            "authenticated": False,
            "tier": tier_payload(None),
            "oauth": oauth_status(),
            "identity": identity_architecture(),
        }
    sub = await fetch_active_subscription_for_email(user["email"])
    profile = await fetch_user_profile(user["email"]) or {}
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
    profile_out = dict(profile)
    profile_out["initials"] = avatar_initials(
        str(profile.get("name") or ""), str(profile.get("email") or user["email"])
    )
    profile_out["avatar_url"] = profile.get("avatar_url") or f"/api/auth/avatar/{user['id']}.svg"
    profile_out["email_verified"] = bool(profile.get("email_verified_at"))
    return {
        "authenticated": True,
        "user": user,
        "profile": profile_out,
        "tier": tier_payload(user, sub),
        "subscription": sub,
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "retention_hint": retention_hint,
        "mfa": mfa,
        "oauth": oauth_status(),
        "identity": identity_architecture(),
    }


@router.patch("/profile")
async def auth_profile_update(
    body: AuthProfileUpdateBody,
    user: dict | None = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import fetch_user_by_username, update_user_profile_fields
    from identity_service import validate_display_name, validate_username

    fields: dict[str, Any] = {}
    try:
        if body.name is not None:
            fields["name"] = validate_display_name(body.name)
        if body.username is not None:
            if body.username.strip() == "":
                fields["username"] = None
            else:
                handle = validate_username(body.username)
                existing = await fetch_user_by_username(handle)
                if existing and int(existing["id"]) != int(user["id"]):
                    raise ValueError("Username already taken")
                fields["username"] = handle
        if body.telegram_chat_id is not None:
            fields["telegram_chat_id"] = body.telegram_chat_id.strip() or None
        if body.ui_lang is not None:
            fields["ui_lang"] = body.ui_lang.strip().lower()[:12] or "en"
        if body.ux_mode_pref is not None:
            fields["ux_mode_pref"] = body.ux_mode_pref
        if body.timezone is not None:
            fields["timezone"] = (body.timezone.strip() or "UTC")[:64]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await update_user_profile_fields(int(user["id"]), fields)
    return {"success": True, "updated": list(fields.keys())}


@router.post("/avatar")
async def auth_avatar_upload(
    user: dict | None = Depends(optional_user),
    file: UploadFile = File(...),
):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import update_user_profile_fields
    from identity_service import save_avatar_bytes

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    data = await file.read()
    try:
        url = save_avatar_bytes(int(user["id"]), content_type, data)
        await update_user_profile_fields(int(user["id"]), {"avatar_url": url})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "avatar_url": url}


@router.delete("/avatar")
async def auth_avatar_delete(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import update_user_profile_fields
    from identity_service import AVATAR_DIR

    uid = int(user["id"])
    for ext in (".jpg", ".png", ".webp"):
        path = AVATAR_DIR / f"{uid}{ext}"
        if path.is_file():
            path.unlink()
    url = f"/api/auth/avatar/{uid}.svg"
    await update_user_profile_fields(uid, {"avatar_url": url})
    return {"ok": True, "avatar_url": url}


@router.get("/avatar/{filename}")
async def auth_avatar_get(filename: str):
    from identity_service import default_avatar_svg, resolve_avatar_file

    # filename: "{id}.svg" or "{id}.jpg"
    stem = Path(filename).stem
    try:
        user_id = int(stem)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc
    if filename.endswith(".svg"):
        from database import fetch_user_by_id

        row = await fetch_user_by_id(user_id)
        name = (row or {}).get("name") or ""
        email = (row or {}).get("email") or "user"
        svg = default_avatar_svg(str(name), str(email))
        return RawResponse(content=svg, media_type="image/svg+xml")
    path = resolve_avatar_file(user_id)
    if not path:
        raise HTTPException(status_code=404, detail="Avatar not found")
    media = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")
    return RawResponse(content=path.read_bytes(), media_type=media)
