"""WebAuthn / Passkeys — ID-009, ID-010."""

from __future__ import annotations

import json
import os
import secrets
from typing import Any

_RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
_RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "BLACKDARK")
_ORIGIN = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")

_challenges: dict[str, dict[str, Any]] = {}


def _base_url() -> str:
    return _ORIGIN


async def begin_passkey_registration(user_id: int, email: str) -> dict[str, Any]:
    from webauthn import generate_registration_options
    from webauthn.helpers.cose import COSEAlgorithmIdentifier
    from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement

    from database import list_passkey_credentials

    existing = await list_passkey_credentials(user_id)
    exclude = [{"id": c["credential_id"], "transports": json.loads(c.get("transports") or "[]")} for c in existing]
    options = generate_registration_options(
        rp_id=_RP_ID,
        rp_name=_RP_NAME,
        user_id=str(user_id).encode(),
        user_name=email,
        user_display_name=email,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[COSEAlgorithmIdentifier.ECDSA_SHA_256, COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256],
    )
    challenge = secrets.token_urlsafe(32)
    _challenges[f"reg:{user_id}"] = {"challenge": options.challenge, "user_id": user_id, "expires": secrets.randbelow(999999)}
    return {"publicKey": json.loads(options.model_dump_json()), "challenge_key": f"reg:{user_id}"}


async def complete_passkey_registration(user_id: int, credential: dict[str, Any], *, label: str = "Passkey") -> dict[str, Any]:
    from webauthn import verify_registration_response

    from database import insert_passkey_credential
    from identity.identity_audit import record_identity_event
    from identity.step_up import mark_step_up

    state = _challenges.pop(f"reg:{user_id}", None)
    if not state:
        raise ValueError("Registration challenge expired")
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=state["challenge"],
        expected_rp_id=_RP_ID,
        expected_origin=_base_url(),
        require_user_verification=True,
    )
    cred_id = verification.credential_id.hex()
    await insert_passkey_credential(
        user_id,
        credential_id=cred_id,
        public_key=verification.credential_public_key.hex(),
        sign_count=int(verification.sign_count),
        label=label,
        transports=json.dumps(credential.get("transports") or []),
    )
    await mark_step_up(user_id)
    await record_identity_event(event_type="passkey.add", user_id=user_id, detail={"label": label})
    return {"registered": True, "credential_id": cred_id}


async def begin_passkey_authentication(*, email: str | None = None, user_id: int | None = None) -> dict[str, Any]:
    from webauthn import generate_authentication_options

    from database import list_passkey_credentials

    if user_id is None and email:
        from database import fetch_user_by_email

        user = await fetch_user_by_email(email.strip().lower())
        user_id = int(user["id"]) if user else None
    if not user_id:
        raise ValueError("Unknown account")
    creds = await list_passkey_credentials(user_id)
    if not creds:
        raise ValueError("No passkeys registered")
    allow = [{"id": bytes.fromhex(c["credential_id"]), "transports": json.loads(c.get("transports") or "[]")} for c in creds]
    options = generate_authentication_options(rp_id=_RP_ID, allow_credentials=allow)
    key = f"auth:{user_id}"
    _challenges[key] = {"challenge": options.challenge, "user_id": user_id}
    return {"publicKey": json.loads(options.model_dump_json()), "challenge_key": key}


async def complete_passkey_authentication(user_id: int, credential: dict[str, Any]) -> dict[str, Any]:
    from webauthn import verify_authentication_response

    from auth_service import create_session, resolve_user_tier
    from database import fetch_passkey_by_credential_id, touch_user_login, update_passkey_sign_count
    from identity.identity_audit import record_identity_event

    state = _challenges.pop(f"auth:{user_id}", None)
    if not state:
        raise ValueError("Authentication challenge expired")
    cred_id = credential.get("rawId") or credential.get("id")
    if isinstance(cred_id, str):
        try:
            import base64

            raw = base64.urlsafe_b64decode(cred_id + "==")
            cred_hex = raw.hex()
        except Exception:
            cred_hex = cred_id
    else:
        cred_hex = bytes(cred_id).hex()
    stored = await fetch_passkey_by_credential_id(cred_hex)
    if not stored or int(stored["user_id"]) != user_id:
        raise ValueError("Unknown passkey")
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=state["challenge"],
        expected_rp_id=_RP_ID,
        expected_origin=_base_url(),
        credential_public_key=bytes.fromhex(stored["public_key"]),
        credential_current_sign_count=int(stored["sign_count"]),
        require_user_verification=True,
    )
    from auth_service import client_user_payload, resolve_user_tier
    from database import fetch_user_by_id

    await update_passkey_sign_count(stored["id"], int(verification.new_sign_count))
    await touch_user_login(user_id)
    session = await create_session(user_id)
    tier = await resolve_user_tier(str(stored.get("email") or ""))
    await record_identity_event(event_type="login.success", user_id=user_id, detail={"method": "passkey"})
    user_row = await fetch_user_by_id(user_id) or {"public_user_id": ""}
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": {**client_user_payload(user_row), "tier": tier},
    }


async def list_passkeys(user_id: int) -> list[dict[str, Any]]:
    from database import list_passkey_credentials

    rows = await list_passkey_credentials(user_id)
    return [
        {
            "id": r["id"],
            "label": r.get("label") or "Passkey",
            "created_at": r.get("created_at"),
            "last_used_at": r.get("last_used_at"),
        }
        for r in rows
    ]


async def rename_passkey(user_id: int, credential_row_id: str, label: str, *, actor: dict[str, Any]) -> dict[str, Any]:
    from database import rename_passkey_credential
    from identity.step_up import require_step_up

    await require_step_up(actor, action="passkey.add")
    ok = await rename_passkey_credential(user_id, credential_row_id, label)
    if not ok:
        raise ValueError("Passkey not found")
    return {"label": label}


async def remove_passkey(user_id: int, credential_row_id: str, *, actor: dict[str, Any]) -> dict[str, Any]:
    from database import count_user_auth_methods, delete_passkey_credential
    from identity.identity_audit import record_identity_event
    from identity.step_up import require_step_up

    await require_step_up(actor, action="passkey.remove")
    methods = await count_user_auth_methods(user_id)
    if methods.get("passkeys", 0) <= 1 and methods.get("total", 0) <= 1:
        raise ValueError("Cannot remove last login method")
    ok = await delete_passkey_credential(user_id, credential_row_id)
    if not ok:
        raise ValueError("Passkey not found")
    await record_identity_event(event_type="passkey.remove", user_id=user_id, detail={"credential_row_id": credential_row_id})
    return {"removed": True}
