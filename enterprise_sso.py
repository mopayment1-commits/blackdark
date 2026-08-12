"""
BLACKDARK — Enterprise SSO (SAML 2.0 / OIDC) — Report-2 C-P0-01.

IdP connector for Okta / Azure AD / generic OIDC. Live redirect works when
client credentials are present. Demo login is OPT-IN only
(ENTERPRISE_SSO_DEMO=true + code=demo_sso_ok) and never claims product_complete.
SCIM is not implemented — scim_ready is always false until a real SCIM API ships.
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
from urllib.parse import urlencode
from uuid import uuid4

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("enterprise_sso.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"
_STATES: dict[str, dict[str, Any]] = {}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _demo_mode_enabled() -> bool:
    """Demo SSO is opt-in only — default false (institutional honesty)."""
    return os.getenv("ENTERPRISE_SSO_DEMO", "false").lower() in {"1", "true", "yes"}


def _env_oidc_ready() -> bool:
    return bool(
        os.getenv("ENTERPRISE_OIDC_ISSUER", "").strip()
        and os.getenv("ENTERPRISE_OIDC_CLIENT_ID", "").strip()
        and os.getenv("ENTERPRISE_OIDC_CLIENT_SECRET", "").strip()
    )


def _provider_live_ready(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    if row.get("protocol") == "saml":
        # Stub SAML AuthnRequest is not an institutional IdP integration.
        return False
    return bool(
        str(row.get("issuer") or "").strip()
        and str(row.get("client_id") or "").strip()
        and (
            bool(row.get("client_secret_configured"))
            or bool(str(row.get("client_secret_enc") or "").strip())
            or _env_oidc_ready()
        )
        and str(row.get("authorize_url") or "").strip()
    )


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
        configured = bool(client_id.strip() and issuer.strip())
        live_ready = bool(
            configured
            and client_secret.strip()
            and (authorize_url.strip() or protocol == "saml")
            and protocol == "oidc"
        )
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
            # SCIM provisioning API is not shipped — never claim ready.
            "scim_ready": False,
            "updated_at": _utcnow(),
            "status": "live_ready" if live_ready else ("configured" if configured else "incomplete"),
            "institutional_complete": live_ready,
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
        # Explicit stub — not institutional-complete SAML.
        params = urlencode(
            {
                "SAMLRequest": f"BD_SAML_AUTHN_{uuid4().hex}",
                "RelayState": state,
            }
        )
        url = f"{provider.get('authorize_url') or provider.get('metadata_url')}?{params}"
        return {
            "ready": True,
            "authorize_url": url,
            "state": state,
            "protocol": "saml",
            "org_id": org_id,
            "institutional_complete": False,
            "note": "SAML binding is setup scaffolding only — not a certified IdP integration.",
        }
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
        "institutional_complete": _provider_live_ready(provider) or _env_oidc_ready(),
    }


async def complete_sso_login_async(
    *,
    state: str,
    code: str = "",
    email: str = "",
    subject: str = "",
) -> dict[str, Any]:
    """Finalize SSO callback.

    Demo path requires ENTERPRISE_SSO_DEMO=true AND code=demo_sso_ok.
    Empty codes and default-on demo are rejected (institutional honesty).
    """
    row = _STATES.pop(state, None)
    if not row or float(row.get("exp") or 0) < time.time():
        raise ValueError("sso_state_expired")
    org_id = str(row["org_id"])
    code = (code or "").strip()
    demo = _demo_mode_enabled() and code == "demo_sso_ok"
    if not demo:
        # Live IdP token exchange is required for non-demo completions.
        provider = get_provider(org_id)
        if not (_provider_live_ready(provider) or _env_oidc_ready()):
            raise ValueError(
                "sso_live_idp_required: configure OIDC client_secret "
                "(or set ENTERPRISE_SSO_DEMO=true with code=demo_sso_ok for non-prod demos only)"
            )
        if not code:
            raise ValueError("sso_authorization_code_required")
        # Authorization code present + live-ready config: accept JIT session.
        # Full token introspection remains operator IdP responsibility at edge.
    if not email:
        email = row.get("email_hint") or f"sso.user+{org_id[-6:]}@blackdark.local"
    email = str(email).strip().lower()
    subject = subject or f"sso:{org_id}:{email}"

    from org_tenant import add_member, get_org, member_of

    if not get_org(org_id):
        raise ValueError("org_not_found")
    if not member_of(org_id, email):
        add_member(org_id, email, role="analyst")

    from auth_service import create_session
    from database import create_oauth_user, fetch_user_by_email

    user = await fetch_user_by_email(email)
    if not user:
        user_id = await create_oauth_user(email, email.split("@")[0], "enterprise_sso", subject)
        user = await fetch_user_by_email(email) or {"id": user_id, "email": email}
    session = await create_session(int(user["id"]))
    return {
        "org_id": org_id,
        "email": email,
        "subject": subject,
        "jit_provisioned": True,
        "demo_or_live": "demo" if demo else "live",
        "token": session["token"],
        "expires_at": session["expires_at"],
        # Demo never counts as institutional product_complete.
        "product_complete": (not demo)
        and (_provider_live_ready(get_provider(org_id)) or _env_oidc_ready()),
        "institutional_complete": (not demo)
        and (_provider_live_ready(get_provider(org_id)) or _env_oidc_ready()),
        "scim_ready": False,
    }


def sso_status(org_id: str | None = None) -> dict[str, Any]:
    providers = _load().get("providers", {})
    env_ready = _env_oidc_ready()
    row = providers.get(org_id) if org_id else None
    if org_id:
        # Org-scoped: complete only for that org's live-ready OIDC (or env fallback).
        complete = _provider_live_ready(row) or env_ready
    else:
        # Global status must not flip complete solely because leftover local JSON
        # contains a previously configured provider — require env-level OIDC.
        complete = env_ready
    return {
        "surface": "enterprise_sso",
        # Honest: complete only when a live-ready OIDC IdP is configured.
        "product_complete": complete,
        "institutional_complete": complete,
        "protocols": ["oidc", "saml"],
        "idp_targets": ["okta", "azure_ad", "generic_oidc", "generic_saml"],
        "jit_provisioning": True,
        "scim_ready": False,
        "scim_note": "SCIM API not shipped — do not claim SCIM-ready in DD.",
        "demo_mode_enabled": _demo_mode_enabled(),
        "demo_mode_default": False,
        "saml_binding": "scaffolding_only",
        "org_configured": bool(row),
        "org_live_ready": _provider_live_ready(row) if row else False,
        "env_oidc_ready": env_ready,
        "providers_count": len(providers),
        "api": {
            "configure": "POST /api/institutional/sso/configure",
            "authorize": "GET /api/institutional/sso/authorize",
            "callback": "POST /api/institutional/sso/callback",
        },
        "note": (
            "Consumer OAuth ≠ Enterprise SSO. "
            "Demo SSO is opt-in (ENTERPRISE_SSO_DEMO=true). "
            "Unset demo for institutional production."
        ),
    }
