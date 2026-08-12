"""
BLACKDARK — Enterprise SSO (SAML 2.0 / OIDC) + SCIM-ready identity.

Real JWKS id_token verification for OIDC. Real SAML AuthnRequest + Response
crypto verification. Demo login is OPT-IN only and never product_complete.
SCIM provisioning is implemented via scim_service (scim_ready=True).
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

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("enterprise_sso.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"
_STATES: dict[str, dict[str, Any]] = {}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _demo_mode_enabled() -> bool:
    return os.getenv("ENTERPRISE_SSO_DEMO", "false").lower() in {"1", "true", "yes"}


def _env_oidc_ready() -> bool:
    return bool(
        os.getenv("ENTERPRISE_OIDC_ISSUER", "").strip()
        and os.getenv("ENTERPRISE_OIDC_CLIENT_ID", "").strip()
        and os.getenv("ENTERPRISE_OIDC_CLIENT_SECRET", "").strip()
    )


def _env_jwks_uri() -> str:
    return os.getenv("ENTERPRISE_OIDC_JWKS_URI", "").strip()


def _provider_live_ready(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    if row.get("protocol") == "saml":
        return bool(
            str(row.get("issuer") or "").strip()
            and str(row.get("authorize_url") or row.get("metadata_url") or "").strip()
            and str(row.get("idp_cert_pem") or "").strip()
        )
    return bool(
        str(row.get("issuer") or "").strip()
        and str(row.get("client_id") or "").strip()
        and (
            bool(row.get("client_secret_configured"))
            or bool(str(row.get("client_secret_enc") or "").strip())
            or _env_oidc_ready()
        )
        and str(row.get("authorize_url") or "").strip()
        and (
            str(row.get("jwks_uri") or "").strip()
            or _env_jwks_uri()
            or str(row.get("issuer") or "").strip()
        )
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
    jwks_uri: str = "",
    idp_cert_pem: str = "",
) -> dict[str, Any]:
    protocol = protocol.strip().lower()
    if protocol not in {"oidc", "saml"}:
        raise ValueError("protocol must be oidc or saml")
    with _LOCK:
        data = _load()
        providers = data.setdefault("providers", {})
        configured = bool(issuer.strip() and (client_id.strip() or protocol == "saml"))
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
            "jwks_uri": jwks_uri.strip() or _env_jwks_uri(),
            "idp_cert_pem": idp_cert_pem.strip(),
            "audiences": audiences or ([client_id.strip()] if client_id.strip() else []),
            "jit_provisioning": True,
            "scim_ready": __import__("scim_service", fromlist=["scim_ready"]).scim_ready(),
            "updated_at": _utcnow(),
        }
        if client_secret.strip():
            try:
                from secrets_vault import encrypt_secret

                row["client_secret_enc"] = encrypt_secret(client_secret.strip())
            except Exception:
                row["client_secret_enc"] = ""
        live_ready = _provider_live_ready(row)
        row["status"] = "live_ready" if live_ready else ("configured" if configured else "incomplete")
        row["institutional_complete"] = live_ready
        providers[org_id] = row
        _save(data)
        return {k: v for k, v in row.items() if k not in {"client_secret_enc", "idp_cert_pem"} or k == "idp_cert_pem"}


def get_provider(org_id: str) -> dict[str, Any] | None:
    row = _load().get("providers", {}).get(org_id)
    if not row:
        return None
    # Keep idp_cert_pem available for SAML verify (not logged).
    return {k: v for k, v in row.items() if k != "client_secret_enc"}


def build_sso_authorize_url(org_id: str, *, redirect_uri: str, email_hint: str = "") -> dict[str, Any]:
    provider = get_provider(org_id)
    if not provider:
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
                        "ENTERPRISE_OIDC_JWKS_URI",
                    ],
                },
            }
        provider = {
            "protocol": "oidc",
            "issuer": issuer,
            "client_id": client_id,
            "authorize_url": authorize_url or f"{issuer.rstrip('/')}/oauth2/v1/authorize",
            "jwks_uri": _env_jwks_uri(),
            "status": "env_configured",
            "audiences": [client_id],
        }
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(16)
    _STATES[state] = {
        "org_id": org_id,
        "exp": time.time() + 600,
        "email_hint": email_hint,
        "redirect_uri": redirect_uri,
        "nonce": nonce,
        "protocol": provider.get("protocol"),
    }
    if provider.get("protocol") == "saml":
        from saml_service import build_authn_request, build_redirect_url

        sso_url = provider.get("authorize_url") or provider.get("metadata_url") or ""
        req = build_authn_request(
            acs_url=redirect_uri,
            destination=sso_url,
            issuer=f"blackdark:{org_id}",
        )
        _STATES[state]["saml_request_id"] = req["id"]
        url = build_redirect_url(sso_url=sso_url, saml_request=req["SAMLRequest"], relay_state=state)
        return {
            "ready": True,
            "authorize_url": url,
            "state": state,
            "protocol": "saml",
            "org_id": org_id,
            "institutional_complete": _provider_live_ready(provider),
            "saml_request_id": req["id"],
        }
    from urllib.parse import urlencode

    params = urlencode(
        {
            "response_type": "code",
            "client_id": provider["client_id"],
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "login_hint": email_hint,
        }
    )
    url = f"{provider['authorize_url']}?{params}"
    return {
        "ready": True,
        "authorize_url": url,
        "state": state,
        "nonce": nonce,
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
    id_token: str = "",
    saml_response: str = "",
) -> dict[str, Any]:
    """Finalize SSO callback with cryptographic IdP verification (non-demo)."""
    row = _STATES.pop(state, None)
    if not row or float(row.get("exp") or 0) < time.time():
        raise ValueError("sso_state_expired")
    org_id = str(row["org_id"])
    code = (code or "").strip()
    id_token = (id_token or "").strip()
    saml_response = (saml_response or "").strip()
    demo = _demo_mode_enabled() and code == "demo_sso_ok"
    verified_claims: dict[str, Any] = {}
    protocol = str(row.get("protocol") or "oidc")

    if not demo:
        provider = get_provider(org_id)
        if not (_provider_live_ready(provider) or _env_oidc_ready()):
            raise ValueError(
                "sso_live_idp_required: configure OIDC/SAML with JWKS or IdP cert "
                "(or set ENTERPRISE_SSO_DEMO=true with code=demo_sso_ok for non-prod demos only)"
            )
        if protocol == "saml" or saml_response:
            if not saml_response:
                raise ValueError("saml_response_required")
            from saml_service import verify_saml_response

            cert = str((provider or {}).get("idp_cert_pem") or "")
            if not cert:
                raise ValueError("saml_idp_cert_required")
            audience = f"blackdark:{org_id}"
            verified_claims = verify_saml_response(
                saml_response_b64=saml_response,
                idp_cert_pem=cert,
                expected_audience=audience,
                expected_destination=str(row.get("redirect_uri") or ""),
            )
            email = verified_claims["email"]
            subject = verified_claims["subject"]
            protocol = "saml"
        else:
            # OIDC: require cryptographic id_token (JWT). Authorization code alone is insufficient.
            token = id_token or (code if code.count(".") == 2 else "")
            if not token:
                raise ValueError("oidc_id_token_required")
            from oidc_jwks_verify import verify_id_token

            issuer = str((provider or {}).get("issuer") or os.getenv("ENTERPRISE_OIDC_ISSUER", "")).rstrip("/")
            audience = (provider or {}).get("audiences") or [
                str((provider or {}).get("client_id") or os.getenv("ENTERPRISE_OIDC_CLIENT_ID", ""))
            ]
            jwks_uri = str((provider or {}).get("jwks_uri") or _env_jwks_uri())
            verified_claims = verify_id_token(
                token,
                issuer=issuer,
                audience=audience if len(audience) > 1 else audience[0],
                jwks_uri=jwks_uri,
                nonce=row.get("nonce"),
            )
            email = str(verified_claims.get("email") or verified_claims.get("preferred_username") or email).lower()
            subject = str(verified_claims.get("sub") or subject)
            if not email:
                raise ValueError("oidc_email_claim_missing")
            protocol = "oidc"

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
    live_complete = (not demo) and (
        _provider_live_ready(get_provider(org_id)) or _env_oidc_ready()
    )
    return {
        "org_id": org_id,
        "email": email,
        "subject": subject,
        "protocol": protocol,
        "jit_provisioned": True,
        "demo_or_live": "demo" if demo else "live",
        "crypto_verified": (not demo),
        "token": session["token"],
        "expires_at": session["expires_at"],
        # product_complete never self-certs from config alone; institutional_complete tracks readiness.
        "product_complete": False,
        "institutional_complete": live_complete,
        "scim_ready": __import__("scim_service", fromlist=["scim_ready"]).scim_ready(),
        "verified_claims_keys": sorted(verified_claims.keys()),
    }


def sso_status(org_id: str | None = None) -> dict[str, Any]:
    from scim_service import scim_ready as _scim_ready

    providers = _load().get("providers", {})
    env_ready = _env_oidc_ready()
    row = providers.get(org_id) if org_id else None
    if org_id:
        complete = _provider_live_ready(row) or env_ready
    else:
        complete = env_ready
    return {
        "surface": "enterprise_sso",
        "product_complete": False,
        "institutional_complete": complete,
        "protocols": ["oidc", "saml"],
        "idp_targets": ["okta", "azure_ad", "generic_oidc", "generic_saml"],
        "jit_provisioning": True,
        "scim_ready": bool(_scim_ready()),
        "scim_note": "SCIM 2.0 User/Group API shipped via scim_service.",
        "jwks_verification": True,
        "saml_verification": True,
        "demo_mode_enabled": _demo_mode_enabled(),
        "demo_mode_default": False,
        "saml_binding": "HTTP-Redirect AuthnRequest + signed Response verify",
        "org_configured": bool(row),
        "org_live_ready": _provider_live_ready(row) if row else False,
        "env_oidc_ready": env_ready,
        "providers_count": len(providers),
        "api": {
            "configure": "POST /api/institutional/sso/configure",
            "authorize": "GET /api/institutional/sso/authorize",
            "callback": "POST /api/institutional/sso/callback",
            "scim_users": "/api/institutional/scim/v2/Users",
        },
        "note": (
            "Consumer OAuth ≠ Enterprise SSO. "
            "Live OIDC requires JWKS-verified id_token. "
            "Live SAML requires IdP X.509-verified Response. "
            "Demo SSO is opt-in (ENTERPRISE_SSO_DEMO=true)."
        ),
    }
