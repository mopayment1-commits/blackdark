"""Institutional closure HMAC guard — FFIEC separation of duties."""

from __future__ import annotations

import hashlib
import hmac
import os


class ClosureGuardError(RuntimeError):
    pass


def assert_owner_approval_for_closure(*, requested_status: str) -> None:
    if requested_status != "INSTITUTIONAL_CLOSED":
        return
    secret = os.environ.get("INSTITUTIONAL_OWNER_APPROVAL_SECRET")
    token = os.environ.get("INSTITUTIONAL_OWNER_APPROVAL_TOKEN")
    if not secret:
        raise ClosureGuardError(
            "INSTITUTIONAL_OWNER_APPROVAL_SECRET is required to set closure_status=INSTITUTIONAL_CLOSED"
        )
    if not token:
        raise ClosureGuardError(
            "INSTITUTIONAL_OWNER_APPROVAL_TOKEN is required to set closure_status=INSTITUTIONAL_CLOSED"
        )
    expected = hmac.new(secret.encode(), b"INSTITUTIONAL_CLOSED", hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token, expected):
        raise ClosureGuardError("owner approval token mismatch for INSTITUTIONAL_CLOSED")


def write_closure_status(path: str, status: str) -> None:
    """Write closure status to JSON manifest only after HMAC guard passes."""
    assert_owner_approval_for_closure(requested_status=status)
    from pathlib import Path
    import json

    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    data["closure_status"] = status
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
