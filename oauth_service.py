"""
BLACKDARK — OAuth2 social login (Google + GitHub) via authlib.
"""

from __future__ import annotations

import logging
import os
import secrets
from typing import Any, Literal
from urllib.parse import urlencode

logger = logging.getLogger("BLACKDARK.OAuth")

Provider = Literal["google", "github"]

_PROVIDERS: dict[str, dict[str, str]] = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
        "client_id_env": "OAUTH_GOOGLE_CLIENT_ID",
        "client_secret_env": "OAUTH_GOOGLE_CLIENT_SECRET",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "scope": "read:user user:email",
        "client_id_env": "OAUTH_GITHUB_CLIENT_ID",
        "client_secret_env": "OAUTH_GITHUB_CLIENT_SECRET",
    },
}

# Short-lived CSRF state store (process-local; fine for single-web replica / soft launch).
_oauth_states: dict[str, dict[str, Any]] = {}


def oauth_configured(provider: str | None = None) -> bool:
    if provider:
        meta = _PROVIDERS.get(provider.lower())
        if not meta:
            return False
        return bool(os.getenv(meta["client_id_env"], "").strip() and os.getenv(meta["client_secret_env"], "").strip())
    return any(oauth_configured(p) for p in _PROVIDERS)


def oauth_status() -> dict[str, Any]:
    return {
        "google": oauth_configured("google"),
        "github": oauth_configured("github"),
        "any": oauth_configured(),
        "callback_base": _callback_base(),
    }


def _callback_base() -> str:
    return os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")


def _client_creds(provider: str) -> tuple[str, str]:
    meta = _PROVIDERS[provider]
    cid = os.getenv(meta["client_id_env"], "").strip()
    secret = os.getenv(meta["client_secret_env"], "").strip()
    if not cid or not secret:
        raise ValueError(f"OAuth provider '{provider}' is not configured")
    return cid, secret


def build_authorize_url(provider: str) -> dict[str, str]:
    provider = provider.lower().strip()
    if provider not in _PROVIDERS:
        raise ValueError("Unsupported OAuth provider")
    if not oauth_configured(provider):
        raise ValueError(f"OAuth provider '{provider}' is not configured")

    meta = _PROVIDERS[provider]
    client_id, _ = _client_creds(provider)
    state = secrets.token_urlsafe(24)
    _oauth_states[state] = {"provider": provider}
    redirect_uri = f"{_callback_base()}/api/auth/oauth/{provider}/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": meta["scope"],
        "state": state,
    }
    if provider == "google":
        params["access_type"] = "online"
        params["prompt"] = "select_account"
    return {
        "provider": provider,
        "authorize_url": f"{meta['authorize_url']}?{urlencode(params)}",
        "state": state,
    }


async def exchange_code(provider: str, code: str, state: str) -> dict[str, Any]:
    """Exchange authorization code for profile {email, name, sub, provider}."""
    provider = provider.lower().strip()
    if provider not in _PROVIDERS:
        raise ValueError("Unsupported OAuth provider")
    stored = _oauth_states.pop(state, None)
    if not stored or stored.get("provider") != provider:
        raise ValueError("Invalid or expired OAuth state")

    meta = _PROVIDERS[provider]
    client_id, client_secret = _client_creds(provider)
    redirect_uri = f"{_callback_base()}/api/auth/oauth/{provider}/callback"

    from authlib.integrations.httpx_client import AsyncOAuth2Client

    async with AsyncOAuth2Client(client_id, client_secret) as client:
        token = await client.fetch_token(
            meta["token_url"],
            code=code,
            redirect_uri=redirect_uri,
            grant_type="authorization_code",
        )
        headers = {"Accept": "application/json"}
        if provider == "github":
            headers["Authorization"] = f"Bearer {token['access_token']}"
            resp = await client.get(meta["userinfo_url"], headers=headers)
            resp.raise_for_status()
            profile = resp.json()
            email = (profile.get("email") or "").strip().lower()
            if not email:
                eresp = await client.get(meta["emails_url"], headers=headers)
                eresp.raise_for_status()
                emails = eresp.json()
                primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                email = ((primary or (emails[0] if emails else {})).get("email") or "").strip().lower()
            name = (profile.get("name") or profile.get("login") or "").strip()
            sub = str(profile.get("id") or "")
        else:
            resp = await client.get(meta["userinfo_url"], token=token)
            resp.raise_for_status()
            profile = resp.json()
            email = (profile.get("email") or "").strip().lower()
            name = (profile.get("name") or profile.get("given_name") or "").strip()
            sub = str(profile.get("sub") or "")
            if profile.get("email_verified") is False:
                raise ValueError("Google email is not verified")

    if not email or "@" not in email:
        raise ValueError("OAuth provider did not return a verified email")
    if not sub:
        raise ValueError("OAuth provider did not return a stable subject id")

    return {
        "provider": provider,
        "email": email,
        "name": name,
        "oauth_sub": sub,
        "raw": {"id": sub},
    }


async def login_or_register_oauth(
    profile: dict[str, Any],
    *,
    referral_code: str | None = None,
) -> dict[str, Any]:
    """Create session for OAuth identity; provision user + trial on first login."""
    from auth_service import create_session, resolve_user_tier
    from database import (
        create_oauth_user,
        fetch_user_by_email,
        fetch_user_by_oauth,
        insert_pro_trial,
        link_user_oauth,
        touch_user_login,
        update_user_oauth_profile,
    )
    from referral_service import apply_referral_on_signup, ensure_user_referral_code

    email = str(profile["email"]).strip().lower()
    provider = str(profile["provider"])
    sub = str(profile["oauth_sub"])
    name = str(profile.get("name") or "")
    is_new = False

    user = await fetch_user_by_oauth(provider, sub)
    if user is None:
        user = await fetch_user_by_email(email)
        if user is None:
            user_id = await create_oauth_user(email, provider, sub, name)
            await insert_pro_trial(email)
            user = {"id": user_id, "email": email, "name": name}
            is_new = True
        else:
            await link_user_oauth(int(user["id"]), provider, sub)
            if name and not user.get("name"):
                await update_user_oauth_profile(int(user["id"]), name=name)

    my_code = await ensure_user_referral_code(int(user["id"]), email)
    referral: dict[str, Any] = {"applied": False}
    if is_new:
        referral = await apply_referral_on_signup(
            new_user_id=int(user["id"]),
            new_email=email,
            referral_code=referral_code,
        )

    await touch_user_login(int(user["id"]))
    session = await create_session(int(user["id"]))
    tier = await resolve_user_tier(email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "referral": referral,
        "user": {
            "id": user["id"],
            "email": email,
            "name": user.get("name") or name,
            "tier": tier,
            "oauth_provider": provider,
            "referral_code": my_code,
        },
        "auth_method": "oauth2",
        "provider": provider,
    }
