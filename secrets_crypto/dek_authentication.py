"""HMAC-SHA256 tags for envelope DEK wrap/unwrap (authentication, not password storage)."""

from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hmac import HMAC


def dek_authentication_tag(kek: bytes, dek: bytes) -> bytes:
    mac = HMAC(kek, hashes.SHA256())
    mac.update(dek)
    return mac.finalize()
