"""
BLACKDARK — OAuth2 social login (#1019 OAuth Login Option).

Optional Google · GitHub · Twitter/X with limited scope.
Merged into Session/Account Security — disabled when credentials unset.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from typing import Any
from urllib.parse import urlencode

_twitter_pkce_verifiers: dict[str, str] = {}


def _normalize_provider(provider: str) -> str:
    key = provider.strip().lower()
    if key == "x":
        return "twitter"
    return key


def oauth_providers_configured() -> dict[str, bool]:
    return {
        "google": bool(
            os.getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip()
            and os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "").strip()
        ),
        "github": bool(
            os.getenv("OAUTH_GITHUB_CLIENT_ID", "").strip()
            and os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "").strip()
        ),
        "twitter": bool(
            os.getenv("OAUTH_TWITTER_CLIENT_ID", "").strip()
            and os.getenv("OAUTH_TWITTER_CLIENT_SECRET", "").strip()
        ),
    }


def oauth_status() -> dict[str, Any]:
    configured = oauth_providers_configured()
    base = {
        "enabled": any(configured.values()),
        "providers": configured,
        "callback_path": "/api/auth/oauth/{provider}/callback",
        "start_path": "/api/auth/oauth/{provider}/start",
        "optional": True,
        "note": (
            "Set OAUTH_*_CLIENT_ID/SECRET plus APP_BASE_URL to enable optional social login. "
            "Email/password + TOTP always available."
        ),
    }
    try:
        from oauth_login_hardening import oauth_login_status

        hardened = oauth_login_status()
        base["policy"] = hardened.get("policy")
        base["allowed_providers"] = hardened.get("providers", {}).get("allowed")
        base["standalone_rejected"] = hardened.get("standalone_rejected")
    except ImportError:
        pass
    return base


def _base_url() -> str:
    return (os.getenv("APP_BASE_URL") or "http://localhost").rstrip("/")


def _provider_config(provider: str) -> dict[str, str]:
    from oauth_login_hardening import allowed_scopes, assert_provider_allowed, validate_requested_scopes

    key = assert_provider_allowed(_normalize_provider(provider))
    scope = " ".join(sorted(allowed_scopes(key)))
    validate_requested_scopes(key, scope)
    if key == "google":
        return {
            "client_id": os.getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "").strip(),
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": scope,
        }
    if key == "github":
        return {
            "client_id": os.getenv("OAUTH_GITHUB_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "").strip(),
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scope": scope,
        }
    if key == "twitter":
        return {
            "client_id": os.getenv("OAUTH_TWITTER_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("OAUTH_TWITTER_CLIENT_SECRET", "").strip(),
            "authorize_url": "https://twitter.com/i/oauth2/authorize",
            "token_url": "https://api.twitter.com/2/oauth2/token",
            "userinfo_url": "https://api.twitter.com/2/users/me?user.fields=profile_image_url",
            "scope": scope,
        }
    raise ValueError(f"Unsupported OAuth provider: {provider}")


def build_authorize_url(provider: str, *, state: str | None = None) -> dict[str, str]:
    key = _normalize_provider(provider)
    cfg = _provider_config(key)
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise ValueError(f"OAuth provider {provider} is not configured")
    state_val = state or secrets.token_urlsafe(24)
    redirect_uri = f"{_base_url()}/api/auth/oauth/{key}/callback"
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state_val,
    }
    if key == "google":
        params["access_type"] = "online"
    if key == "twitter":
        verifier = secrets.token_urlsafe(32)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("utf-8")).digest()
        ).rstrip(b"=").decode("ascii")
        _twitter_pkce_verifiers[state_val] = verifier
        params["code_challenge"] = challenge
        params["code_challenge_method"] = "S256"
    try:
        from oauth_login_hardening import log_oauth_event

        log_oauth_event("start", provider=key, scope=cfg["scope"])
    except ImportError:
        pass
    return {
        "provider": key,
        "state": state_val,
        "authorize_url": f"{cfg['authorize_url']}?{urlencode(params)}",
        "redirect_uri": redirect_uri,
        "scope": cfg["scope"],
    }


async def _oauth_token_exchange(
    client: Any,
    cfg: dict[str, str],
    code: str,
    redirect_uri: str,
    *,
    provider: str,
    state: str | None = None,
) -> dict[str, Any]:
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    if provider == "twitter":
        verifier = _twitter_pkce_verifiers.pop(str(state or ""), "")
        if not verifier:
            raise ValueError("Missing Twitter PKCE verifier")
        data["code_verifier"] = verifier
    token_resp = await client.post(
        cfg["token_url"],
        data=data,
        headers={"Accept": "application/json"},
    )
    token_resp.raise_for_status()
    payload = token_resp.json()
    access = payload.get("access_token")
    if not access:
        raise ValueError("OAuth token exchange failed")
    return {
        "access_token": str(access),
        "refresh_token": str(payload.get("refresh_token") or ""),
        "expires_in": int(payload.get("expires_in") or 3600),
        "scope": str(payload.get("scope") or cfg["scope"]),
    }


async def _oauth_userinfo(client: Any, cfg: dict[str, str], headers: dict[str, str], *, provider: str) -> dict[str, Any]:
    info_resp = await client.get(cfg["userinfo_url"], headers=headers)
    info_resp.raise_for_status()
    info = info_resp.json()
    if provider == "twitter":
        data = info.get("data") or {}
        return {
            "email": "",
            "name": str(data.get("name") or data.get("username") or ""),
            "sub": str(data.get("id") or ""),
            "login": str(data.get("username") or ""),
        }
    return info


async def _github_primary_email(client: Any, headers: dict[str, str]) -> str:
    emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
    if emails_resp.status_code != 200:
        return ""
    for row in emails_resp.json():
        if row.get("primary") and row.get("verified"):
            return str(row.get("email") or "").lower()
    return ""


async def exchange_code(provider: str, code: str, *, state: str | None = None) -> dict[str, Any]:
    """Exchange authorization code for profile + server-side token bundle (never client-exposed)."""
    import httpx

    from oauth_login_hardening import encrypt_oauth_token, log_oauth_event, validate_requested_scopes

    key = _normalize_provider(provider)
    cfg = _provider_config(key)
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise ValueError(f"OAuth provider {provider} is not configured")
    redirect_uri = f"{_base_url()}/api/auth/oauth/{key}/callback"
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_bundle = await _oauth_token_exchange(
            client, cfg, code, redirect_uri, provider=key, state=state
        )
        validate_requested_scopes(key, token_bundle["scope"])
        headers = {"Authorization": f"Bearer {token_bundle['access_token']}", "Accept": "application/json"}
        info = await _oauth_userinfo(client, cfg, headers, provider=key)
        email = (info.get("email") or "").strip().lower()
        name = (info.get("name") or info.get("login") or "").strip()
        subject = str(info.get("sub") or info.get("id") or "")
        if key == "github" and not email:
            email = await _github_primary_email(client, headers)
        if not email:
            raise ValueError("OAuth provider did not return a verified email")
        log_oauth_event(
            "token_exchange",
            provider=key,
            email=email,
            scope=token_bundle["scope"],
            detail={"subject_prefix": subject[:8]},
        )
        return {
            "provider": key,
            "subject": subject,
            "email": email,
            "name": name,
            "scope": token_bundle["scope"],
            "access_token_enc": encrypt_oauth_token(token_bundle["access_token"]),
            "refresh_token_enc": encrypt_oauth_token(token_bundle["refresh_token"])
            if token_bundle.get("refresh_token")
            else None,
            "expires_in": token_bundle["expires_in"],
        }


_oauth_mfa_challenges: dict[str, dict[str, Any]] = {}


def _oauth_mfa_challenge_response(user_id: int, email: str, provider: str) -> dict[str, Any]:
    from datetime import UTC, datetime, timedelta

    challenge = secrets.token_urlsafe(24)
    _oauth_mfa_challenges[challenge] = {
        "user_id": user_id,
        "email": email,
        "provider": provider,
        "expires": (datetime.now(UTC) + timedelta(minutes=5)).timestamp(),
    }
    return {
        "mfa_required": True,
        "mfa_challenge": challenge,
        "auth_method": f"oauth:{provider}",
        "user": {"id": user_id, "email": email},
    }


async def complete_oauth_mfa_login(
    challenge: str,
    code: str,
    *,
    device_fingerprint: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    accept_language: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    from datetime import UTC, datetime

    from auth_service import create_session, resolve_user_tier
    from database import touch_user_login
    from mfa_service import verify_user_mfa
    from oauth_login_hardening import log_oauth_event, resolve_tenant_id

    row = _oauth_mfa_challenges.get(challenge)
    if not row or float(row.get("expires") or 0) < datetime.now(UTC).timestamp():
        _oauth_mfa_challenges.pop(challenge, None)
        raise ValueError("OAuth MFA challenge expired — login again")
    user_id = int(row["user_id"])
    email = str(row["email"])
    provider = str(row.get("provider") or "")
    if not await verify_user_mfa(user_id, code):
        raise ValueError("Invalid MFA code")
    _oauth_mfa_challenges.pop(challenge, None)
    await touch_user_login(user_id)
    session = await create_session(
        user_id,
        email=email,
        device_fingerprint=device_fingerprint,
        ip=ip,
        user_agent=user_agent,
        accept_language=accept_language,
    )
    tier = await resolve_user_tier(email)
    log_oauth_event(
        "mfa_complete",
        user_id=user_id,
        email=email,
        provider=provider,
        ip=ip,
        tenant_id=resolve_tenant_id(tenant_id),
    )
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "mfa_required": False,
        "user": {
            "id": user_id,
            "email": email,
            "tier": tier,
            "auth_method": f"oauth:{provider}",
        },
    }


async def login_or_link_oauth_user(
    profile: dict[str, Any],
    *,
    ip: str | None = None,
    device_fingerprint: str | None = None,
    user_agent: str | None = None,
    accept_language: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Create or link user from OAuth profile and issue a session (or MFA challenge)."""
    from auth_service import create_session, normalize_email, resolve_user_tier
    from database import (
        create_oauth_user,
        fetch_user_by_email,
        fetch_user_by_oauth,
        touch_user_login,
        upsert_oauth_provider_link,
    )
    from oauth_login_hardening import (
        assert_admin_oauth_forbidden,
        assert_password_backup,
        assert_provider_allowed,
        initiate_oauth_link_confirmation,
        log_oauth_event,
        resolve_tenant_id,
    )

    email = normalize_email(str(profile["email"]))
    provider = assert_provider_allowed(str(profile["provider"]))
    subject = str(profile.get("subject") or "")
    name = str(profile.get("name") or "")
    tenant = resolve_tenant_id(tenant_id)
    scope = str(profile.get("scope") or "")

    assert_admin_oauth_forbidden(email)

    user = await fetch_user_by_oauth(provider, subject, tenant_id=tenant) if subject else None
    link_confirmation: dict[str, Any] | None = None

    if user is None:
        existing = await fetch_user_by_email(email)
        if existing is None:
            user_id = await create_oauth_user(email, name, provider, subject)
            user = await fetch_user_by_email(email)
            assert user is not None
            user_id = int(user["id"])
            await upsert_oauth_provider_link(
                user_id=user_id,
                provider=provider,
                subject=subject,
                tenant_id=tenant,
                scope=scope,
                access_token_enc=profile.get("access_token_enc"),
                refresh_token_enc=profile.get("refresh_token_enc"),
            )
            log_oauth_event("register", user_id=user_id, email=email, provider=provider, ip=ip, tenant_id=tenant)
        else:
            user_id = int(existing["id"])
            link_confirmation = await initiate_oauth_link_confirmation(
                user_id=user_id,
                email=email,
                provider=provider,
                subject=subject,
                tenant_id=tenant,
            )
            return link_confirmation
    else:
        user_id = int(user["id"])
        await upsert_oauth_provider_link(
            user_id=user_id,
            provider=provider,
            subject=subject,
            tenant_id=tenant,
            scope=scope,
            access_token_enc=profile.get("access_token_enc"),
            refresh_token_enc=profile.get("refresh_token_enc"),
        )

    mfa_enabled = bool(int(user.get("mfa_enabled") or 0))
    if mfa_enabled:
        log_oauth_event("mfa_required", user_id=user_id, email=email, provider=provider, ip=ip, tenant_id=tenant)
        return _oauth_mfa_challenge_response(user_id, email, provider)

    await touch_user_login(user_id)
    session = await create_session(
        user_id,
        email=email,
        device_fingerprint=device_fingerprint,
        ip=ip,
        user_agent=user_agent,
        accept_language=accept_language,
    )
    tier = await resolve_user_tier(email)
    password_backup_required = not assert_password_backup(user)
    log_oauth_event("login", user_id=user_id, email=email, provider=provider, ip=ip, tenant_id=tenant, scope=scope)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "password_backup_required": password_backup_required,
        "user": {
            "id": user_id,
            "email": email,
            "name": user.get("name") or name,
            "tier": tier,
            "auth_method": f"oauth:{provider}",
            "mfa_enabled": mfa_enabled,
        },
    }
