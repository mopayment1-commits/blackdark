"""
WebAuthn / Passkeys (FIDO2) — CISA phishing-resistant authentication track.

Normative: W3C WebAuthn Level 2; FIDO Alliance guidance.
Requires optional dependency: webauthn (see requirements.txt).
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.parse import urlparse

from webauthn_credential_store import (
    add_credential,
    find_credential,
    list_credentials,
    user_ids_with_credential_id,
)

_CHALLENGES: dict[str, dict[str, Any]] = {}


def _library_available() -> bool:
    try:
        import webauthn  # noqa: F401

        return True
    except ImportError:
        return False


def webauthn_enabled() -> bool:
    return _library_available() and bool(rp_id())


def rp_id() -> str:
    explicit = os.getenv("WEBAUTHN_RP_ID", "").strip()
    if explicit:
        return explicit.lower()
    base = os.getenv("APP_BASE_URL", "").strip()
    if base:
        host = (urlparse(base).hostname or "").lower()
        if host:
            return host
    return "localhost"


def rp_origin() -> str:
    base = os.getenv("APP_BASE_URL", "http://localhost:8080").strip().rstrip("/")
    return base


def webauthn_status() -> dict[str, Any]:
    return {
        "enabled": webauthn_enabled(),
        "library_available": _library_available(),
        "rp_id": rp_id() if _library_available() else None,
        "phishing_resistant": webauthn_enabled(),
        "api": {
            "register_options": "POST /api/auth/webauthn/register/options",
            "register_verify": "POST /api/auth/webauthn/register/verify",
            "login_options": "POST /api/auth/webauthn/login/options",
            "login_verify": "POST /api/auth/webauthn/login/verify",
        },
    }


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


async def registration_options(user_id: int, email: str) -> dict[str, Any]:
    if not webauthn_enabled():
        raise RuntimeError("webauthn_not_configured")
    from webauthn import generate_registration_options
    from webauthn.helpers import bytes_to_base64url, options_to_json
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )

    existing = list_credentials(user_id)
    exclude = [
        PublicKeyCredentialDescriptor(id=_b64url_decode(c["credential_id_b64"]))
        for c in existing
        if c.get("credential_id_b64")
    ]
    options = generate_registration_options(
        rp_id=rp_id(),
        rp_name=os.getenv("WEBAUTHN_RP_NAME", "BLACKDARK"),
        user_id=str(user_id).encode("utf-8"),
        user_name=email,
        user_display_name=email,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    challenge = bytes_to_base64url(options.challenge)
    _CHALLENGES[challenge] = {
        "kind": "register",
        "user_id": user_id,
        "email": email,
        "challenge_bytes": options.challenge,
    }
    return json.loads(options_to_json(options))


async def registration_verify(user_id: int, credential: dict[str, Any]) -> dict[str, Any]:
    if not webauthn_enabled():
        raise RuntimeError("webauthn_not_configured")
    from webauthn import verify_registration_response
    from webauthn.helpers import bytes_to_base64url, parse_registration_credential_json

    reg = parse_registration_credential_json(json.dumps(credential))
    cdj = reg.response.client_data_json
    client_data = json.loads(cdj if isinstance(cdj, (bytes, bytearray)) else _b64url_decode(cdj))
    challenge = client_data.get("challenge")
    pending = _CHALLENGES.pop(str(challenge), None)
    if not pending or pending.get("user_id") != user_id:
        raise ValueError("webauthn_challenge_invalid")

    verified = verify_registration_response(
        credential=reg,
        expected_challenge=pending["challenge_bytes"],
        expected_rp_id=rp_id(),
        expected_origin=rp_origin(),
        require_user_verification=True,
    )
    cred_id_b64 = bytes_to_base64url(verified.credential_id)
    stored = add_credential(
        user_id,
        {
            "credential_id": cred_id_b64,
            "credential_id_b64": cred_id_b64,
            "public_key": verified.credential_public_key.hex(),
            "sign_count": verified.sign_count,
            "aaguid": verified.aaguid.hex() if verified.aaguid else None,
        },
    )
    from security_events import record_security_event

    record_security_event("mfa_enroll", severity="info", actor=pending.get("email"), detail={"method": "webauthn"})
    return {"ok": True, "credential": {"id": stored["credential_id"]}}


async def login_options(email: str) -> dict[str, Any]:
    if not webauthn_enabled():
        raise RuntimeError("webauthn_not_configured")
    from database import fetch_user_by_email

    user = await fetch_user_by_email(email.strip().lower())
    if user is None:
        raise ValueError("user_not_found")
    uid = int(user["id"])
    creds = list_credentials(uid)
    if not creds:
        raise ValueError("no_passkeys_registered")
    from webauthn import generate_authentication_options
    from webauthn.helpers import bytes_to_base64url, options_to_json
    from webauthn.helpers.structs import PublicKeyCredentialDescriptor

    allow = [
        PublicKeyCredentialDescriptor(id=_b64url_decode(c["credential_id_b64"])) for c in creds
    ]
    options = generate_authentication_options(rp_id=rp_id(), allow_credentials=allow)
    challenge = bytes_to_base64url(options.challenge)
    _CHALLENGES[challenge] = {
        "kind": "login",
        "user_id": uid,
        "email": email,
        "challenge_bytes": options.challenge,
    }
    return json.loads(options_to_json(options))


async def login_verify(credential: dict[str, Any]) -> dict[str, Any]:
    if not webauthn_enabled():
        raise RuntimeError("webauthn_not_configured")
    from webauthn import verify_authentication_response
    from webauthn.helpers import parse_authentication_credential_json

    auth_cred = parse_authentication_credential_json(json.dumps(credential))
    cred_id_b64 = _b64url_encode(auth_cred.raw_id)
    uids = user_ids_with_credential_id(cred_id_b64)
    if not uids:
        raise ValueError("credential_unknown")
    uid = uids[0]
    row = find_credential(uid, cred_id_b64)
    if not row:
        raise ValueError("credential_unknown")

    cdj = auth_cred.response.client_data_json
    client_data = json.loads(cdj if isinstance(cdj, (bytes, bytearray)) else _b64url_decode(cdj))
    challenge = client_data.get("challenge")
    pending = _CHALLENGES.pop(str(challenge), None) if challenge else None
    if not pending or pending.get("user_id") != uid:
        raise ValueError("webauthn_challenge_invalid")

    verified = verify_authentication_response(
        credential=auth_cred,
        expected_challenge=pending["challenge_bytes"],
        expected_rp_id=rp_id(),
        expected_origin=rp_origin(),
        credential_public_key=bytes.fromhex(row["public_key"]),
        credential_current_sign_count=int(row.get("sign_count") or 0),
        require_user_verification=True,
    )
    row["sign_count"] = verified.new_sign_count
    add_credential(uid, row)

    from auth_service import create_session
    from database import fetch_user_by_id

    user = await fetch_user_by_id(uid)
    session = await create_session(uid)
    from security_events import record_security_event

    record_security_event(
        "login_success",
        severity="info",
        actor=user.get("email"),
        detail={"method": "webauthn"},
    )
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": {"id": uid, "email": user.get("email"), "mfa_enabled": True},
        "auth_method": "webauthn",
    }
