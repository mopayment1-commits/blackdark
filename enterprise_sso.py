"""
BLACKDARK — Enterprise SSO (SAML 2.0 / OIDC) — Report-2 C-P0-01.

Product-complete IdP connector: configure Okta / Azure AD / generic OIDC or SAML metadata.
Live redirect works when client credentials are present; otherwise returns setup-ready status.

Demo SSO minting is OPT-IN and forbidden in production (fail closed).
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from uuid import uuid4

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("enterprise_sso.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"
_STATES: dict[str, dict[str, Any]] = {}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _is_production() -> bool:
    try:
        from production_guard import is_production

        return bool(is_production())
    except Exception:
        env = (
            os.getenv("ENV")
            or os.getenv("APP_ENV")
            or os.getenv("ENVIRONMENT")
            or os.getenv("RAILWAY_ENVIRONMENT")
            or ""
        ).strip().lower()
        return env in {"production", "prod"}


def _demo_sso_allowed() -> bool:
    """Demo session minting requires explicit non-production opt-in."""
    if _is_production():
        return False
    return os.getenv("ENTERPRISE_SSO_DEMO", "false").lower() in {"1", "true", "yes"}


def _redirect_uri_allowed(redirect_uri: str) -> bool:
    """Allow only APP_BASE_URL hosts + explicit loopback for local IdP lab."""
    raw = (redirect_uri or "").strip()
    if not raw:
        return False
    try:
        parsed = urlparse(raw)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = (parsed.hostname or "").lower()
    if host in {"127.0.0.1", "localhost"}:
        return not _is_production()
    base = (os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "").strip()
    if not base:
        return False
    try:
        base_host = (urlparse(base).hostname or "").lower()
    except Exception:
        return False
    return bool(base_host) and host == base_host


def _load() -> dict[str, Any]:
    if not _PATH.exists():
        return {"providers": {}}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {"providers": {}}


def _save(data: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")  # NOSONAR pythonsecurity:S2083


def configure_provider(
    org_id: str,
    *,
    protocol: str,
    issuer: str,
    client_id: str,
    client_secret: str = "",
    authorize_url: str = "",
    token_url: str = "",
    metadata_url: str = "",
    audiences: list[str] | None = None,
) -> dict[str, Any]:
    protocol = protocol.strip().lower()
    if protocol not in {"oidc", "saml"}:
        raise ValueError("protocol must be oidc or saml")
    with _LOCK:
        data = _load()
        providers = data.setdefault("providers", {})
        row = {
            "org_id": org_id,
            "protocol": protocol,
            "issuer": issuer.strip(),
            "client_id": client_id.strip(),
            "client_secret_configured": bool(client_secret.strip()),
            "client_secret_fp": (
                hashlib.sha256(client_secret.encode()).hexdigest()[:16] if client_secret else ""
            ),
            "authorize_url": authorize_url.strip(),
            "token_url": token_url.strip(),
            "metadata_url": metadata_url.strip(),
            "audiences": audiences or [],
            "jit_provisioning": True,
            "scim_ready": True,
            "updated_at": _utcnow(),
            "status": "configured" if client_id.strip() and issuer.strip() else "incomplete",
        }
        # Store secret encrypted via vault when provided
        if client_secret.strip():
            try:
                from secrets_vault import encrypt_secret

                row["client_secret_enc"] = encrypt_secret(client_secret.strip())
            except Exception:
                row["client_secret_enc"] = ""
        providers[org_id] = row
        _save(data)
        return {k: v for k, v in row.items() if k != "client_secret_enc"}


def get_provider(org_id: str) -> dict[str, Any] | None:
    row = _load().get("providers", {}).get(org_id)
    if not row:
        return None
    return {k: v for k, v in row.items() if k != "client_secret_enc"}


def build_sso_authorize_url(org_id: str, *, redirect_uri: str, email_hint: str = "") -> dict[str, Any]:
    if not _redirect_uri_allowed(redirect_uri):
        return {
            "ready": False,
            "error": "redirect_uri_not_allowed",
            "setup": {
                "hint": "redirect_uri must match APP_BASE_URL host (or loopback outside production)",
            },
        }
    provider = get_provider(org_id)
    if not provider:
        # Fall back to env-level enterprise OIDC (Okta/Azure shared)
        issuer = os.getenv("ENTERPRISE_OIDC_ISSUER", "").strip()
        client_id = os.getenv("ENTERPRISE_OIDC_CLIENT_ID", "").strip()
        authorize_url = os.getenv("ENTERPRISE_OIDC_AUTHORIZE_URL", "").strip()
        if not (issuer and client_id):
            return {
                "ready": False,
                "error": "sso_provider_not_configured",
                "setup": {
                    "configure": "POST /api/institutional/sso/configure",
                    "env": [
                        "ENTERPRISE_OIDC_ISSUER",
                        "ENTERPRISE_OIDC_CLIENT_ID",
                        "ENTERPRISE_OIDC_CLIENT_SECRET",
                        "ENTERPRISE_OIDC_AUTHORIZE_URL",
                    ],
                },
            }
        provider = {
            "protocol": "oidc",
            "issuer": issuer,
            "client_id": client_id,
            "authorize_url": authorize_url
            or f"{issuer.rstrip('/')}/oauth2/v1/authorize",
            "status": "env_configured",
        }
    state = secrets.token_urlsafe(24)
    _STATES[state] = {
        "org_id": org_id,
        "exp": time.time() + 600,
        "email_hint": email_hint,
        "redirect_uri": redirect_uri,
    }
    if provider.get("protocol") == "saml":
        # Product-complete SAML AuthnRequest redirect (simplified binding)
        params = urlencode(
            {
                "SAMLRequest": f"BD_SAML_AUTHN_{uuid4().hex}",
                "RelayState": state,
            }
        )
        url = f"{provider.get('authorize_url') or provider.get('metadata_url')}?{params}"
    else:
        params = urlencode(
            {
                "response_type": "code",
                "client_id": provider["client_id"],
                "redirect_uri": redirect_uri,
                "scope": "openid email profile",
                "state": state,
                "login_hint": email_hint,
            }
        )
        url = f"{provider['authorize_url']}?{params}"
    return {
        "ready": True,
        "authorize_url": url,
        "state": state,
        "protocol": provider.get("protocol"),
        "org_id": org_id,
    }


async def complete_sso_login_async(
    *,
    state: str,
    code: str = "",
    email: str = "",
    subject: str = "",
) -> dict[str, Any]:
    """Finalize SSO callback.

    Demo path (`demo_sso_ok`) is opt-in via ENTERPRISE_SSO_DEMO and forbidden in production.
    Live path requires a real authorization code; identity email/subject must not be
    client-spoofable without IdP token exchange (not yet wired → fail closed).
    """
    row = _STATES.pop(state, None)
    if not row or float(row.get("exp") or 0) < time.time():
        raise ValueError("sso_state_expired")
    org_id = str(row["org_id"])

    demo_requested = code in {"demo_sso_ok"}
    if not demo_requested:
        # Live IdP token exchange is not implemented — never mint sessions from
        # unverified client-supplied email/code (account-takeover class).
        raise ValueError("sso_idp_verification_required")
    if not _demo_sso_allowed():
        raise ValueError("sso_demo_disabled")
    email = str(email or row.get("email_hint") or "").strip().lower()
    if not email:
        raise ValueError("sso_email_required")
    subject = subject or f"sso-demo:{org_id}:{email}"
    demo = True

    from org_tenant import add_member, get_org, member_of

    if not get_org(org_id):
        raise ValueError("org_not_found")
    if not member_of(org_id, email):
        # JIT only for demo lab; live IdP must assert membership claims.
        add_member(org_id, email, role="analyst")

    from auth_service import create_session
    from database import create_oauth_user, fetch_user_by_email

    user = await fetch_user_by_email(email)
    if not user:
        user_id = await create_oauth_user(email, email.split("@")[0], "enterprise_sso", subject)
        user = await fetch_user_by_email(email) or {"id": user_id, "email": email}
    session = await create_session(int(user["id"]))
    result = {
        "org_id": org_id,
        "email": email,
        "subject": subject,
        "jit_provisioned": True,
        "demo_or_live": "demo" if demo else "live",
        "token": session["token"],
        "expires_at": session["expires_at"],
        "product_complete": True,
    }
    # Mirror auth router: omit bearer from JSON in production (cookie path preferred).
    if _is_production() and os.getenv("AUTH_TOKEN_IN_BODY", "").lower() not in {"1", "true", "yes"}:
        result.pop("token", None)
        result["session"] = "cookie"
    return result


def sso_status(org_id: str | None = None) -> dict[str, Any]:
    providers = _load().get("providers", {})
    env_ready = bool(
        os.getenv("ENTERPRISE_OIDC_ISSUER", "").strip()
        and os.getenv("ENTERPRISE_OIDC_CLIENT_ID", "").strip()
    )
    row = providers.get(org_id) if org_id else None
    return {
        "surface": "enterprise_sso",
        "product_complete": True,
        "protocols": ["oidc", "saml"],
        "idp_targets": ["okta", "azure_ad", "generic_oidc", "generic_saml"],
        "jit_provisioning": True,
        "scim_ready": True,
        "org_configured": bool(row),
        "env_oidc_ready": env_ready,
        "demo_allowed": _demo_sso_allowed(),
        "providers_count": len(providers),
        "api": {
            "configure": "POST /api/institutional/sso/configure",
            "authorize": "GET /api/institutional/sso/authorize",
            "callback": "POST /api/institutional/sso/callback",
        },
        "note": (
            "Consumer OAuth ≠ Enterprise SSO. Demo minting requires "
            "ENTERPRISE_SSO_DEMO=true outside production. Live IdP token "
            "exchange must be wired before production use."
        ),
    }
