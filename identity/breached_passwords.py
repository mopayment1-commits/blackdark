"""Breached password checking — ID-005 (HIBP k-anonymity)."""

from __future__ import annotations

import hashlib
import os
from typing import Any

_HIBP_ENABLED = os.getenv("IDENTITY_HIBP_CHECK", "true").lower() in {"1", "true", "yes"}


def sha1_prefix_suffix(password: str) -> tuple[str, str]:
    # HIBP k-anonymity range API requires SHA-1 of password (protocol contract, not storage).
    digest = hashlib.sha1(password.encode("utf-8"), usedforsecurity=False).hexdigest().upper()  # nosec B324
    return digest[:5], digest[5:]


def check_breached_password(password: str, *, timeout: float = 5.0) -> dict[str, Any]:
    """Privacy-preserving HIBP range lookup — never sends full password."""
    if not _HIBP_ENABLED:
        return {"checked": False, "breached": False, "source": "disabled"}
    prefix, suffix = sha1_prefix_suffix(password)
    try:
        import httpx

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers={"Add-Padding": "true"})
        if resp.status_code != 200:
            return {"checked": False, "breached": False, "source": "hibp_error"}
        for line in resp.text.splitlines():
            part, _count = line.split(":", 1) if ":" in line else (line, "0")
            if part.strip().upper() == suffix:
                return {"checked": True, "breached": True, "source": "hibp"}
        return {"checked": True, "breached": False, "source": "hibp"}
    except Exception:
        return {"checked": False, "breached": False, "source": "hibp_unavailable"}


def assert_password_not_breached(password: str) -> None:
    result = check_breached_password(password)
    if result.get("checked") and result.get("breached"):
        raise ValueError("This password appears in a public breach — choose another")
