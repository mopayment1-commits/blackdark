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
from api.openapi_responses import COMMON_ERROR_RESPONSES
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

import logging

logger = logging.getLogger("BLACKDARK.AuthAPI")

router = APIRouter(prefix="/api/auth", tags=["auth"], responses=COMMON_ERROR_RESPONSES)


def _attach_session_cookie(response: Response, token: str | None) -> None:
    if not token:
        return
    from security_middleware import attach_session_cookie

    # Opaque session bearer (secrets.token_urlsafe) — never a password.
    attach_session_cookie(response, str(token))


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie("bd_token", path="/")


def _session_response_body(result: dict[str, Any]) -> dict[str, Any]:
    """Prefer HttpOnly cookie session; omit reusable bearer from JSON in production.

    Set AUTH_TOKEN_IN_BODY=true only for legacy clients that cannot use cookies.
    """
    body = dict(result)
    explicit = os.getenv("AUTH_TOKEN_IN_BODY", "").strip().lower()
    include = explicit in {"1", "true", "yes"}
    if explicit in {"0", "false", "no"}:
        include = False
    elif not explicit:
        tokens = [
            (os.getenv("ENV") or "").strip().lower(),
            (os.getenv("APP_ENV") or "").strip().lower(),
            (os.getenv("ENVIRONMENT") or "").strip().lower(),
            (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
        ]
        # Any explicit production marker → omit bearer from JSON body.
        include = not any(t in {"production", "prod"} for t in tokens)
    if not include:
        body.pop("token", None)
        body["session"] = "cookie"
    return body


@router.get("/identity")
async def auth_identity_architecture():
    from identity_service import identity_architecture

    return identity_architecture()


@router.post("/register", responses=COMMON_ERROR_RESPONSES)
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
        resp = JSONResponse(_session_response_body(result))
        _attach_session_cookie(resp, result.get("token"))
        return resp
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", responses=COMMON_ERROR_RESPONSES)
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
        resp = JSONResponse(_session_response_body(result))
        _attach_session_cookie(resp, result.get("token"))
        return resp
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/mfa/complete", responses=COMMON_ERROR_RESPONSES)
async def auth_mfa_complete(body: AuthMfaChallengeBody, background_tasks: BackgroundTasks):
    from auth_service import complete_mfa_login

    try:
        result = await complete_mfa_login(body.challenge, body.code)
        background_tasks.add_task(record_behavior, "auth_login_mfa", user=result.get("user"))
        from observability import increment_metric

        increment_metric("auth_logins_total")
        resp = JSONResponse(_session_response_body(result))
        _attach_session_cookie(resp, result.get("token"))
        return resp
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/mfa/status", responses=COMMON_ERROR_RESPONSES)
async def auth_mfa_status(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from mfa_service import mfa_status_for_user

    return await mfa_status_for_user(int(user["id"]))


@router.post("/mfa/enroll", responses=COMMON_ERROR_RESPONSES)
async def auth_mfa_enroll(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from mfa_service import begin_mfa_enroll

    try:
        return await begin_mfa_enroll(int(user["id"]), str(user["email"]))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("MFA enroll failed")
        raise HTTPException(
            status_code=503,
            detail=f"MFA enrollment unavailable: {exc}",
        ) from exc


@router.post("/mfa/confirm", responses=COMMON_ERROR_RESPONSES)
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


@router.post("/mfa/disable", responses=COMMON_ERROR_RESPONSES)
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


@router.post("/reset-password", responses=COMMON_ERROR_RESPONSES)
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
    from auth_service import client_user_payload
    from database import fetch_user_by_id

    user_row = await fetch_user_by_id(user_id) or user
    resp = JSONResponse(
        _session_response_body(
            {
                "ok": True,
                "message": "Password updated. You are signed in.",
                "token": session["token"],
                "expires_at": session["expires_at"],
                "user": client_user_payload(user_row),
            }
        )
    )
    _attach_session_cookie(resp, session["token"])
    return resp


@router.post("/change-password", responses=COMMON_ERROR_RESPONSES)
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
    resp = JSONResponse(
        _session_response_body(
            {"ok": True, "token": session["token"], "expires_at": session["expires_at"]}
        )
    )
    _attach_session_cookie(resp, session["token"])
    return resp


@router.get("/verify-email", responses=COMMON_ERROR_RESPONSES)
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


@router.post("/resend-verification", responses=COMMON_ERROR_RESPONSES)
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


@router.get("/oauth/{provider}/start", responses=COMMON_ERROR_RESPONSES)
async def auth_oauth_start(provider: str):
    from identity_service import store_oauth_state_async
    from oauth_service import build_authorize_url

    try:
        payload = build_authorize_url(provider)
        await store_oauth_state_async(provider, payload["state"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return payload


@router.get("/oauth/{provider}/callback", responses=COMMON_ERROR_RESPONSES)
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


@router.post("/logout-all", responses=COMMON_ERROR_RESPONSES)
async def auth_logout_all(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import delete_user_sessions_for_user

    await delete_user_sessions_for_user(int(user["id"]))
    resp = JSONResponse({"ok": True, "message": "All sessions revoked. Please log in again."})
    _clear_session_cookie(resp)
    return resp


@router.get("/me")
async def auth_me(request: Request, user: dict | None = Depends(optional_user)):
    from auth_service import client_user_payload, tier_payload
    from database import fetch_active_subscription_for_email, fetch_user_profile
    from identity.public_user_id import default_avatar_url
    from identity_service import avatar_initials, identity_architecture
    from mfa_service import mfa_status_for_user
    from oauth_service import oauth_status
    from timezone.iana import COMMON_IANA_TIMEZONES
    from timezone.request_context import resolve_from_request
    from timezone.resolver import time_context_payload

    resolved = resolve_from_request(request, user=user)
    time_ctx = time_context_payload(resolved)
    if user is None:
        return {
            "authenticated": False,
            "tier": tier_payload(None),
            "oauth": oauth_status(),
            "identity": identity_architecture(),
            "time": time_ctx,
            "timezone_options": list(COMMON_IANA_TIMEZONES),
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
    profile_out["avatar_url"] = profile.get("avatar_url") or default_avatar_url(str(user.get("public_user_id") or ""))
    profile_out["email_verified"] = bool(profile.get("email_verified_at"))
    profile_out.pop("id", None)
    return {
        "authenticated": True,
        "user": client_user_payload(user),
        "profile": profile_out,
        "tier": tier_payload(user, sub),
        "subscription": sub,
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "retention_hint": retention_hint,
        "mfa": mfa,
        "oauth": oauth_status(),
        "identity": identity_architecture(),
        "time": time_ctx,
        "timezone_options": list(COMMON_IANA_TIMEZONES),
    }


@router.patch("/profile", responses=COMMON_ERROR_RESPONSES)
async def auth_profile_update(
    body: AuthProfileUpdateBody,
    user: dict | None = Depends(optional_user),
):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    try:
        fields = await _profile_update_fields(body, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    from database import fetch_user_by_id, update_user_profile_fields
    from timezone.audit import record_timezone_change

    old_row = await fetch_user_by_id(int(user["id"])) or user
    await update_user_profile_fields(int(user["id"]), fields)
    if "timezone" in fields:
        await record_timezone_change(
            int(user["id"]),
            old_timezone=str(old_row.get("timezone") or "UTC"),
            new_timezone=str(fields["timezone"]),
            source="profile",
            actor=str(user.get("public_user_id") or user["id"]),
        )
    return {"success": True, "updated": list(fields.keys())}


async def _profile_update_fields(
    body: AuthProfileUpdateBody,
    user: dict,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    await _set_profile_name_and_username(fields, body, user)
    if body.telegram_chat_id is not None:
        fields["telegram_chat_id"] = body.telegram_chat_id.strip() or None
    if body.ui_lang is not None:
        fields["ui_lang"] = body.ui_lang.strip().lower()[:12] or "en"
    if body.ux_mode_pref is not None:
        fields["ux_mode_pref"] = body.ux_mode_pref
    if body.timezone is not None:
        fields["timezone"] = body.timezone
    return fields


async def _set_profile_name_and_username(
    fields: dict[str, Any],
    body: AuthProfileUpdateBody,
    user: dict,
) -> None:
    from database import fetch_user_by_username
    from identity_service import validate_display_name, validate_username

    if body.name is not None:
        fields["name"] = validate_display_name(body.name)
    if body.username is None:
        return
    if body.username.strip() == "":
        fields["username"] = None
        return
    handle = validate_username(body.username)
    existing = await fetch_user_by_username(handle)
    if existing and int(existing["id"]) != int(user["id"]):
        raise ValueError("Username already taken")
    fields["username"] = handle


@router.post("/avatar", responses=COMMON_ERROR_RESPONSES)
async def auth_avatar_upload(
    user: dict | None = Depends(optional_user),
    file: UploadFile = File(...),
):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import fetch_user_by_id, update_user_profile_fields
    from identity_service import save_avatar_bytes

    row = await fetch_user_by_id(int(user["id"])) or user
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    data = await file.read()
    try:
        url = save_avatar_bytes(
            content_type=content_type,
            data=data,
            previous_avatar_url=str(row.get("avatar_url") or ""),
        )
        await update_user_profile_fields(int(user["id"]), {"avatar_url": url})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "avatar_url": url}


@router.delete("/avatar", responses=COMMON_ERROR_RESPONSES)
async def auth_avatar_delete(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail=STR_LOGIN_REQUIRED)
    from database import fetch_user_by_id, update_user_profile_fields
    from identity_service import delete_avatar_file, reset_avatar_url

    uid = int(user["id"])
    row = await fetch_user_by_id(uid) or user
    delete_avatar_file(str(row.get("avatar_url") or ""))
    url = reset_avatar_url(str(row.get("public_user_id") or user.get("public_user_id") or ""))
    await update_user_profile_fields(uid, {"avatar_url": url})
    return {"ok": True, "avatar_url": url}


@router.get("/avatar/{filename}", responses=COMMON_ERROR_RESPONSES)
async def auth_avatar_get(filename: str):
    from database import fetch_user_by_public_id
    from identity.public_user_id import is_valid_public_user_id
    from identity_service import default_avatar_svg, resolve_avatar_file

    suffix = Path(filename).suffix.lower()
    stem = Path(filename).stem
    if suffix == ".svg":
        if not is_valid_public_user_id(stem):
            raise HTTPException(status_code=404, detail="Not found")
        row = await fetch_user_by_public_id(stem)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        name = (row or {}).get("name") or ""
        email = (row or {}).get("email") or "user"
        svg = default_avatar_svg(str(name), str(email))
        return RawResponse(content=svg, media_type="image/svg+xml")
    if suffix not in {".jpg", ".png", ".webp"}:
        raise HTTPException(status_code=404, detail="Not found")
    path = resolve_avatar_file(stem, suffix)
    if not path:
        raise HTTPException(status_code=404, detail="Avatar not found")
    media = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(suffix, "application/octet-stream")
    return RawResponse(content=path.read_bytes(), media_type=media)


@router.get("/sessions", responses=COMMON_ERROR_RESPONSES)
async def auth_list_sessions(request: Request, user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    from identity.session_service import list_user_sessions
    from timezone.format import format_activity_log_user_view
    from timezone.request_context import resolve_from_request

    resolved = resolve_from_request(request, user=user)
    lang = str(user.get("ui_lang") or "en")
    rows = await list_user_sessions(int(user["id"]))
    sessions = []
    for row in rows:
        item = dict(row)
        for key in ("created_at", "last_seen_at", "expires_at", "idle_expires_at"):
            if item.get(key):
                item[f"{key}_display"] = format_activity_log_user_view(
                    str(item[key]), lang=lang, tz_name=resolved.timezone
                )
                item[f"{key}_utc"] = str(item[key])
        sessions.append(item)
    return {"sessions": sessions, "display_timezone": resolved.timezone}


@router.post("/sessions/{session_id}/revoke", responses=COMMON_ERROR_RESPONSES)
async def auth_revoke_session(session_id: str, user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    from identity.session_service import revoke_session

    ok = await revoke_session(int(user["id"]), session_id, actor_user_id=int(user["id"]))
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"revoked": True}


@router.post("/secure-account", responses=COMMON_ERROR_RESPONSES)
async def auth_secure_account(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    from identity.secure_account import secure_my_account

    return await secure_my_account(int(user["id"]), actor=user)


@router.get("/passkeys", responses=COMMON_ERROR_RESPONSES)
async def auth_list_passkeys(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    from identity.webauthn_service import list_passkeys

    return {"passkeys": await list_passkeys(int(user["id"]))}


@router.post("/account/delete", responses=COMMON_ERROR_RESPONSES)
async def auth_request_deletion(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    from identity.account_deletion import request_account_deletion

    return await request_account_deletion(int(user["id"]), actor=user)


@router.get("/recovery/options", responses=COMMON_ERROR_RESPONSES)
async def auth_recovery_options(user: dict | None = Depends(optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    from identity.account_recovery import recovery_options

    return await recovery_options(int(user["id"]))


@router.post("/timezone/detect", responses=COMMON_ERROR_RESPONSES)
async def auth_timezone_detect(body: dict[str, Any]):
    from timezone.iana import validate_iana_timezone
    from timezone.request_context import DETECTED_TZ_COOKIE

    raw = str(body.get("detected_timezone") or "").strip()
    detected = validate_iana_timezone(raw)
    if detected == "UTC" and raw.upper() != "UTC":
        raise HTTPException(status_code=400, detail="Invalid detected timezone")
    resp = JSONResponse({"ok": True, "detected_timezone": detected})
    resp.set_cookie(DETECTED_TZ_COOKIE, detected, max_age=60 * 60 * 24 * 365, httponly=False, samesite="lax")
    return resp


@router.post("/timezone/session", responses=COMMON_ERROR_RESPONSES)
async def auth_timezone_session(body: dict[str, Any]):
    from timezone.iana import validate_iana_timezone
    from timezone.request_context import SESSION_TZ_COOKIE

    tz = validate_iana_timezone(str(body.get("timezone") or ""))
    resp = JSONResponse({"ok": True, "session_timezone": tz})
    resp.set_cookie(SESSION_TZ_COOKIE, tz, max_age=60 * 60 * 24 * 365, httponly=False, samesite="lax")
    return resp

