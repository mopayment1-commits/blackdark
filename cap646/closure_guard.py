"""Institutional closure HMAC guard — FFIEC separation of duties."""

from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

from path_safety import read_json_mapping, resolve_under, write_json_mapping

_ROOT = Path(__file__).resolve().parents[1]
_ALLOWED_CLOSURE_STATUSES = frozenset({"PENDING_CLOSURE", "INSTITUTIONAL_CLOSED"})


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


def _validated_closure_status(status: str) -> str:
    cleaned = str(status).strip()
    if cleaned not in _ALLOWED_CLOSURE_STATUSES:
        raise ClosureGuardError(f"unsupported closure_status: {status!r}")
    return cleaned


def closure_manifest_path() -> Path:
    """Single SSOT closure manifest under docs/ (no caller-supplied paths)."""
    return resolve_under(_ROOT, "docs", "INSTITUTIONAL_CLOSURE_FINAL.json")


def write_closure_status(status: str) -> None:
    """Write closure status to the institutional manifest only after HMAC guard passes."""
    validated = _validated_closure_status(status)
    assert_owner_approval_for_closure(requested_status=validated)
    manifest = closure_manifest_path()
    data = read_json_mapping(manifest) if manifest.exists() else {}
    data["closure_status"] = validated
    write_json_mapping(manifest, data)
