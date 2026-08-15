"""
BLACKDARK — OAuth2 / OIDC login scaffolding (Authlib).

Configured via env; disabled when client credentials are unset.
Supports Google and GitHub as common identity providers.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse


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
    live = any(configured.values())
    return {
        "enabled": live,
        "providers": configured,
        "callback_path": "/api/auth/oauth/{provider}/callback",
        "start_path": "/api/auth/oauth/{provider}/start",
        "unpaid_protocol_complete": True,
        "live_idp": live,
        "unconfigured_http": 503,
        "note": (
            "Protocol is complete. Live Google/GitHub login needs owner client ids. "
            "Start without credentials returns HTTP 503, not a silent success."
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


GOOGLE_CLIENT_ID_SUFFIX = ".apps.googleusercontent.com"
OAUTH_GOOGLE_EVIDENCE_DEFAULT = Path(__file__).resolve().parent / "docs" / "dd" / "BLACKDARK_OAUTH_GOOGLE_EVIDENCE.json"
_GOOGLE_AUTHORIZE_ERRORS = (
    "redirect_uri_mismatch",
    "invalid_client",
    "unauthorized_client",
    "access_denied",
)


def oauth_google_evidence_path() -> Path:
    override = os.getenv("OAUTH_GOOGLE_EVIDENCE_PATH", "").strip()
    return Path(override) if override else OAUTH_GOOGLE_EVIDENCE_DEFAULT


def oauth_google_presence() -> dict[str, Any]:
    """Secret-free presence metadata. Never returns credential values."""
    client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip()
    secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "").strip()
    base = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    return {
        "client_id_present": bool(client_id),
        "client_id_len": len(client_id),
        "client_id_google_suffix": client_id.endswith(GOOGLE_CLIENT_ID_SUFFIX),
        "client_secret_present": bool(secret),
        "client_secret_len": len(secret),
        "app_base_url_set": bool(base),
        "app_base_url_https": base.lower().startswith("https://"),
        "callback_path": "/api/auth/oauth/google/callback",
        "redirect_uri": f"{base}/api/auth/oauth/google/callback" if base else "",
    }


def oauth_google_live_proved() -> bool:
    path = oauth_google_evidence_path()
    if not path.is_file():
        return False
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (
        body.get("verdict") == "PASS"
        and bool(body.get("ok"))
        and body.get("reason") == "ok"
        and body.get("start_ok") is True
        and body.get("authorize_accepted") is True
        and body.get("token_client_accepted") is True
        and bool(body.get("redirect_uri"))
    )


def _google_error_token(url: str, body: str) -> str | None:
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    frag = parse_qs(parsed.fragment)
    for key in ("error", "authError", "autherror"):
        for bucket in (q, frag):
            raw = (bucket.get(key) or [None])[0]
            if raw:
                token = str(raw).lower()
                for known in _GOOGLE_AUTHORIZE_ERRORS:
                    if known in token:
                        return known
    hay = f"{url}\n{body}".lower()
    for known in _GOOGLE_AUTHORIZE_ERRORS:
        if known in hay:
            return known
    return None


def prove_google_oauth_idp() -> dict[str, Any]:
    """Live Google Authorization Code IdP wiring for D28.

    PASS requires BLACKDARK start URL construction plus Google accepting
    client_id+redirect_uri on authorize and client_id+secret on token
    (dummy code → invalid_grant, not invalid_client).

    Does not complete a human consent/callback login. Never logs secrets
    or authorize URLs (they embed client_id).
    """
    import httpx

    presence = oauth_google_presence()
    receipt: dict[str, Any] = {
        "ok": False,
        "reason": "not_started",
        "start_ok": False,
        "authorize_accepted": False,
        "token_client_accepted": False,
        "authorize_http_status": 0,
        "token_http_status": 0,
        "google_error": None,
        "token_error": None,
        "authorize_host": None,
        "human_callback_completed": False,
        **presence,
    }
    if not presence["client_id_present"] or not presence["client_secret_present"]:
        receipt["reason"] = "secrets_missing"
        return receipt
    if not presence["app_base_url_set"]:
        receipt["reason"] = "app_base_url_missing"
        return receipt

    try:
        payload = build_authorize_url("google")
    except ValueError as exc:
        receipt["reason"] = "start_build_failed"
        receipt["error_type"] = type(exc).__name__
        return receipt

    redirect_uri = str(payload.get("redirect_uri") or "")
    authorize_url = str(payload.get("authorize_url") or "")
    receipt["redirect_uri"] = redirect_uri
    receipt["start_ok"] = bool(
        authorize_url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
        and redirect_uri.endswith("/api/auth/oauth/google/callback")
        and payload.get("state")
        and "response_type=code" in authorize_url
    )
    if not receipt["start_ok"]:
        receipt["reason"] = "start_url_invalid"
        return receipt

    headers = {
        "User-Agent": "Mozilla/5.0 BLACKDARK-oauth-idp-probe",
        "Accept": "text/html,application/json",
    }
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as client:
            auth_resp = client.get(authorize_url)
            final_url = str(auth_resp.url)
            auth_text = auth_resp.text or ""
            receipt["authorize_http_status"] = int(auth_resp.status_code)
            receipt["authorize_host"] = urlparse(final_url).hostname
            google_error = _google_error_token(final_url, auth_text)
            receipt["google_error"] = google_error
            host_ok = (receipt["authorize_host"] or "").endswith("google.com")
            receipt["authorize_accepted"] = google_error is None and host_ok and int(auth_resp.status_code) < 500

            token_resp = client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": os.getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip(),
                    "client_secret": os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "").strip(),
                    "code": "blackdark-oauth-probe-invalid",
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            receipt["token_http_status"] = int(token_resp.status_code)
            try:
                token_body = token_resp.json()
            except Exception:
                token_body = {}
            if not isinstance(token_body, dict):
                token_body = {}
            if token_body.get("access_token"):
                receipt["reason"] = "unexpected_token_success"
                return receipt
            token_error = str(token_body.get("error") or "").strip()
            receipt["token_error"] = token_error or None
            receipt["token_client_accepted"] = token_error in {"invalid_grant", "invalid_request"}
    except Exception as exc:
        receipt["reason"] = "idp_network_error"
        receipt["error_type"] = type(exc).__name__
        return receipt

    if not receipt["authorize_accepted"]:
        receipt["reason"] = receipt["google_error"] or "authorize_rejected"
        return receipt
    if not receipt["token_client_accepted"]:
        receipt["reason"] = receipt["token_error"] or "token_client_rejected"
        return receipt

    receipt["ok"] = True
    receipt["reason"] = "ok"
    return receipt
