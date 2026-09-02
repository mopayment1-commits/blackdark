"""Institutional closure HMAC guard — FFIEC separation of duties."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

from path_safety import resolve_under

_ROOT = Path(__file__).resolve().parents[1]
_ALLOWED_CLOSURE_MANIFESTS = frozenset({"docs/INSTITUTIONAL_CLOSURE_FINAL.json"})


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


def _safe_closure_manifest(path: str) -> Path:
    """Resolve allowlisted closure manifest under project root (blocks path injection)."""
    rel = Path(path)
    if rel.is_absolute():
        raise ClosureGuardError("closure manifest path must be relative to project root")
    normalized = rel.as_posix()
    if normalized not in _ALLOWED_CLOSURE_MANIFESTS:
        raise ClosureGuardError(f"closure manifest path not allowlisted: {normalized}")
    return resolve_under(_ROOT, *rel.parts)


def write_closure_status(path: str, status: str) -> None:
    """Write closure status to JSON manifest only after HMAC guard passes."""
    assert_owner_approval_for_closure(requested_status=status)
    manifest = _safe_closure_manifest(path)
    data = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    data["closure_status"] = status
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
