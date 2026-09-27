"""HMAC-SHA256 tags for envelope DEK wrap/unwrap (authentication, not password storage)."""

from __future__ import annotations

import hmac


def dek_authentication_tag(kek: bytes, dek: bytes) -> bytes:
    return hmac.digest(kek, dek, "sha256")
