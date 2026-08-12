"""OIDC JWKS cryptographic verification — fail-closed enterprise IdP proof.

Verifies id_token signatures against issuer JWKS. No claim trust without crypto.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urljoin

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

# Allow small clock skew for IdP/client drift
CLOCK_SKEW_SEC = 60
_JWKS_CACHE: dict[str, tuple[float, PyJWKClient]] = {}
_JWKS_TTL_SEC = 300.0


class OidcVerificationError(ValueError):
    """Fail-closed OIDC/JWKS verification failure."""


def jwks_uri_for_issuer(issuer: str, explicit_jwks_uri: str = "") -> str:
    if explicit_jwks_uri.strip():
        return explicit_jwks_uri.strip()
    base = issuer.rstrip("/") + "/"
    # OIDC discovery is preferred when available; fallback to common JWKS path.
    return urljoin(base, ".well-known/jwks.json")


def _client_for(jwks_uri: str) -> PyJWKClient:
    now = time.time()
    cached = _JWKS_CACHE.get(jwks_uri)
    if cached and (now - cached[0]) < _JWKS_TTL_SEC:
        return cached[1]
    client = PyJWKClient(jwks_uri, cache_keys=True, lifespan=_JWKS_TTL_SEC)
    _JWKS_CACHE[jwks_uri] = (now, client)
    return client


def clear_jwks_cache() -> None:
    _JWKS_CACHE.clear()


def verify_id_token(
    id_token: str,
    *,
    issuer: str,
    audience: str | list[str],
    jwks_uri: str = "",
    nonce: str | None = None,
    leeway_sec: int = CLOCK_SKEW_SEC,
    now: int | None = None,
) -> dict[str, Any]:
    """Cryptographically verify an OIDC id_token against JWKS.

    Fail closed on: invalid signature, wrong iss/aud, expired, nbf, unknown kid,
    JWKS outage, tampered payload, missing required claims.
    """
    if not id_token or not str(id_token).strip():
        raise OidcVerificationError("id_token_required")
    if not issuer or not str(issuer).strip():
        raise OidcVerificationError("issuer_required")
    if not audience:
        raise OidcVerificationError("audience_required")

    uri = jwks_uri_for_issuer(issuer, jwks_uri)
    try:
        jwks_client = _client_for(uri)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
    except PyJWKClientError as exc:
        raise OidcVerificationError(f"jwks_unavailable:{exc}") from exc
    except Exception as exc:  # noqa: BLE001 — fail closed on any JWKS path error
        raise OidcVerificationError(f"jwks_key_selection_failed:{exc}") from exc

    options = {
        "require": ["exp", "iat", "iss", "aud", "sub"],
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_aud": True,
        "verify_iss": True,
    }
    try:
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
            audience=audience,
            issuer=issuer.rstrip("/"),
            leeway=leeway_sec,
            options=options,
        )
    except InvalidTokenError as exc:
        raise OidcVerificationError(f"token_invalid:{exc}") from exc

    if nonce is not None:
        if claims.get("nonce") != nonce:
            raise OidcVerificationError("nonce_mismatch")

    # Extra explicit nbf/exp checks with optional injected "now" for tests
    if now is not None:
        if int(claims.get("exp", 0)) < (now - leeway_sec):
            raise OidcVerificationError("token_expired")
        nbf = claims.get("nbf")
        if nbf is not None and int(nbf) > (now + leeway_sec):
            raise OidcVerificationError("token_not_yet_valid")

    return dict(claims)


async def discover_jwks_uri(issuer: str, *, timeout_sec: float = 5.0) -> str:
    """Resolve JWKS URI via OIDC discovery document; fail closed on outage."""
    url = issuer.rstrip("/") + "/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise OidcVerificationError(f"oidc_discovery_failed:{exc}") from exc
    jwks = str(data.get("jwks_uri") or "").strip()
    if not jwks:
        raise OidcVerificationError("jwks_uri_missing_in_discovery")
    return jwks


def verification_status() -> dict[str, Any]:
    return {
        "surface": "oidc_jwks_verify",
        "algorithms": ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
        "checks": [
            "jwks_retrieval",
            "kid_selection",
            "signature",
            "issuer",
            "audience",
            "exp",
            "nbf",
            "iat",
            "nonce",
            "clock_skew",
        ],
        "fail_closed": True,
        "product_complete": True,
    }
