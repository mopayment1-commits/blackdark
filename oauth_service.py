"""
BLACKDARK — OAuth2 / OIDC login scaffolding (Authlib).

Configured via env; disabled when client credentials are unset.
Supports Google and GitHub as common identity providers.
"""

from __future__ import annotations

import os
import secrets
from typing import Any
from urllib.parse import urlencode


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
    }


def oauth_status() -> dict[str, Any]:
    configured = oauth_providers_configured()
    return {
        "enabled": any(configured.values()),
        "providers": configured,
        "callback_path": "/api/auth/oauth/{provider}/callback",
        "start_path": "/api/auth/oauth/{provider}/start",
        "note": (
            "Set OAUTH_GOOGLE_CLIENT_ID/SECRET and/or OAUTH_GITHUB_CLIENT_ID/SECRET "
            "plus APP_BASE_URL to enable social login."
        ),
    }


def _base_url() -> str:
    return (os.getenv("APP_BASE_URL") or "http://127.0.0.1:8080").rstrip("/")


def _provider_config(provider: str) -> dict[str, str]:
    key = provider.strip().lower()
    if key == "google":
        return {
            "client_id": os.getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "").strip(),
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile",
        }
    if key == "github":
        return {
            "client_id": os.getenv("OAUTH_GITHUB_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "").strip(),
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scope": "read:user user:email",
        }
    raise ValueError(f"Unsupported OAuth provider: {provider}")


def build_authorize_url(provider: str, *, state: str | None = None) -> dict[str, str]:
    cfg = _provider_config(provider)
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise ValueError(f"OAuth provider {provider} is not configured")
    state_val = state or secrets.token_urlsafe(24)
    redirect_uri = f"{_base_url()}/api/auth/oauth/{provider}/callback"
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state_val,
    }
    if provider.lower() == "google":
        params["access_type"] = "online"
        params["include_granted_scopes"] = "true"
    return {
        "provider": provider.lower(),
        "state": state_val,
        "authorize_url": f"{cfg['authorize_url']}?{urlencode(params)}",
        "redirect_uri": redirect_uri,
    }


async def _oauth_token(client: Any, cfg: dict[str, str], code: str, redirect_uri: str) -> str:
    token_resp = await client.post(
        cfg["token_url"],
        data={
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        headers={"Accept": "application/json"},
    )
    token_resp.raise_for_status()
    access = token_resp.json().get("access_token")
    if not access:
        raise ValueError("OAuth token exchange failed")
    return access


async def _oauth_userinfo(client: Any, cfg: dict[str, str], headers: dict[str, str]) -> dict[str, Any]:
    info_resp = await client.get(cfg["userinfo_url"], headers=headers)
    info_resp.raise_for_status()
    return info_resp.json()


async def _github_primary_email(client: Any, headers: dict[str, str]) -> str:
    emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
    if emails_resp.status_code != 200:
        return ""
    for row in emails_resp.json():
        if row.get("primary") and row.get("verified"):
            return str(row.get("email") or "").lower()
    return ""


async def exchange_code(provider: str, code: str) -> dict[str, Any]:
    """Exchange authorization code for profile {email, name, subject, provider}."""
    import httpx

    cfg = _provider_config(provider)
    if not cfg["client_id"] or not cfg["client_secret"]:
        raise ValueError(f"OAuth provider {provider} is not configured")
    redirect_uri = f"{_base_url()}/api/auth/oauth/{provider}/callback"
    async with httpx.AsyncClient(timeout=20.0) as client:
        access = await _oauth_token(client, cfg, code, redirect_uri)
        headers = {"Authorization": f"Bearer {access}", "Accept": "application/json"}
        info = await _oauth_userinfo(client, cfg, headers)
        email = (info.get("email") or "").strip().lower()
        name = (info.get("name") or info.get("login") or "").strip()
        subject = str(info.get("sub") or info.get("id") or "")
        if provider.lower() == "github" and not email:
            email = await _github_primary_email(client, headers)
        if not email:
            raise ValueError("OAuth provider did not return a verified email")
        return {
            "provider": provider.lower(),
            "subject": subject,
            "email": email,
            "name": name,
        }


async def login_or_link_oauth_user(profile: dict[str, Any]) -> dict[str, Any]:
    """Create or link user from OAuth profile and issue a session."""
    from auth_service import create_session, normalize_email, resolve_user_tier
    from database import (
        create_oauth_user,
        fetch_user_by_email,
        fetch_user_by_oauth,
        link_user_oauth,
        touch_user_login,
    )

    email = normalize_email(str(profile["email"]))
    provider = str(profile["provider"])
    subject = str(profile.get("subject") or "")
    name = str(profile.get("name") or "")

    user = await fetch_user_by_oauth(provider, subject) if subject else None
    if user is None:
        user = await fetch_user_by_email(email)
        if user is None:
            user_id = await create_oauth_user(email, name, provider, subject)
            user = await fetch_user_by_email(email)
        else:
            user_id = int(user["id"])
            await link_user_oauth(user_id, provider, subject)
    else:
        user_id = int(user["id"])

    assert user is not None
    await touch_user_login(user_id)
    session = await create_session(user_id)
    tier = await resolve_user_tier(email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": {
            "id": user_id,
            "email": email,
            "name": user.get("name") or name,
            "tier": tier,
            "auth_method": f"oauth:{provider}",
        },
    }
