"""Break-glass emergency privileged access (FDS-22 / SDG-14)."""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

_DEFAULT_TTL_SEC = int(os.getenv("BREAK_GLASS_TTL_SEC", "900"))
_ACTIVE: dict[str, dict[str, Any]] = {}


def _ledger_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "break_glass_events.jsonl"


def break_glass_enabled() -> bool:
    return os.getenv("BREAK_GLASS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def activate_break_glass(
    *,
    actor_id: str,
    actor_email: str,
    reason: str,
    scope: str = "financial_read",
) -> dict[str, Any]:
    if not break_glass_enabled():
        raise PermissionError("break_glass_disabled")
    cleaned_reason = (reason or "").strip()
    if len(cleaned_reason) < 12:
        raise ValueError("break_glass_reason_required")
    now = time.time()
    grant_id = secrets.token_hex(12)
    rec = {
        "grant_id": grant_id,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "reason": cleaned_reason,
        "scope": scope,
        "activated_at": now,
        "expires_at": now + _DEFAULT_TTL_SEC,
        "revoked": False,
        "post_use_review_required": True,
        "post_use_review_completed": False,
    }
    _ACTIVE[grant_id] = rec
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"event": "activated", **rec}) + "\n")
    return rec


def active_break_glass_for_actor(actor_id: str) -> dict[str, Any] | None:
    now = time.time()
    for grant_id, rec in list(_ACTIVE.items()):
        if rec.get("revoked"):
            continue
        if str(rec.get("actor_id")) != str(actor_id):
            continue
        if now >= float(rec.get("expires_at") or 0):
            rec["expired"] = True
            continue
        return rec
    return None


def expire_break_glass_grants() -> int:
    now = time.time()
    expired = 0
    for rec in _ACTIVE.values():
        if not rec.get("revoked") and now >= float(rec.get("expires_at") or 0):
            rec["expired"] = True
            expired += 1
    return expired


def revoke_break_glass(grant_id: str, *, actor_id: str) -> bool:
    rec = _ACTIVE.get(grant_id)
    if not rec:
        return False
    rec["revoked"] = True
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"event": "revoked", "grant_id": grant_id, "actor_id": actor_id, "ts": time.time()}) + "\n")
    return True


def complete_post_use_review(grant_id: str, *, reviewer: str, outcome: str, notes: str = "") -> dict[str, Any]:
    rec = _ACTIVE.get(grant_id)
    if not rec:
        raise ValueError("grant_not_found")
    rec["post_use_review_completed"] = True
    rec["post_use_review_outcome"] = outcome
    rec["post_use_review_reviewer"] = reviewer
    rec["post_use_review_notes"] = notes
    rec["post_use_review_at"] = time.time()
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"event": "post_use_review", "grant_id": grant_id, "reviewer": reviewer, "outcome": outcome}) + "\n")
    return rec


def break_glass_status() -> dict[str, Any]:
    expire_break_glass_grants()
    pending_review = [
        g for g in _ACTIVE.values() if g.get("post_use_review_required") and not g.get("post_use_review_completed")
    ]
    return {
        "enabled": break_glass_enabled(),
        "active_grants": len([g for g in _ACTIVE.values() if not g.get("revoked") and not g.get("expired")]),
        "pending_post_use_review": len(pending_review),
        "default_ttl_sec": _DEFAULT_TTL_SEC,
    }
