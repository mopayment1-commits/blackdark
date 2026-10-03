"""Envelope encryption for sensitive financial secrets (SDG-05)."""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from secrets_crypto.kms import _METHODOLOGY_VERSION, wrap_dek, unwrap_dek

_ENVELOPE_PREFIX = "bdenv1:"


def is_envelope_blob(value: str) -> bool:
    return bool(value) and str(value).startswith(_ENVELOPE_PREFIX)


def encrypt_envelope(plaintext: str, *, aad: bytes = b"blackdark-financial-secret") -> str:
    if not plaintext:
        return ""
    dek = os.urandom(32)
    nonce = os.urandom(12)
    ciphertext = AESGCM(dek).encrypt(nonce, plaintext.encode("utf-8"), aad)
    wrapped = wrap_dek(dek)
    blob = {
        "v": 1,
        "alg": wrapped["algorithm"],
        "methodology": wrapped["methodology_version"],
        "key_id": wrapped["key_id"],
        "key_version": wrapped["key_version"],
        "provider": wrapped["provider"],
        "wrapped_dek": wrapped["wrapped_dek"],
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "aad": aad.decode("ascii"),
    }
    return _ENVELOPE_PREFIX + base64.b64encode(json.dumps(blob, separators=(",", ":")).encode("utf-8")).decode("ascii")


def decrypt_envelope(token: str, *, aad: bytes | None = None) -> str:
    if not token:
        return ""
    if not is_envelope_blob(token):
        raise ValueError("not_envelope_blob")
    raw = base64.b64decode(token[len(_ENVELOPE_PREFIX) :].encode("ascii"))
    blob: dict[str, Any] = json.loads(raw.decode("utf-8"))
    dek = unwrap_dek(
        blob["wrapped_dek"],
        key_id=str(blob.get("key_id") or ""),
        key_version=int(blob.get("key_version") or 1),
        provider=str(blob.get("provider") or ""),
    )
    nonce = base64.b64decode(str(blob.get("nonce") or ""))
    ciphertext = base64.b64decode(str(blob.get("ciphertext") or ""))
    use_aad = aad if aad is not None else str(blob.get("aad") or "blackdark-financial-secret").encode("utf-8")
    return AESGCM(dek).decrypt(nonce, ciphertext, use_aad).decode("utf-8")


def envelope_metadata(token: str) -> dict[str, Any]:
    if not is_envelope_blob(token):
        return {}
    raw = base64.b64decode(token[len(_ENVELOPE_PREFIX) :].encode("ascii"))
    blob: dict[str, Any] = json.loads(raw.decode("utf-8"))
    return {
        "key_id": blob.get("key_id"),
        "key_version": blob.get("key_version"),
        "algorithm": blob.get("alg"),
        "methodology": blob.get("methodology"),
        "provider": blob.get("provider"),
        "has_wrapped_dek": bool(blob.get("wrapped_dek")),
        "has_ciphertext": bool(blob.get("ciphertext")),
    }
