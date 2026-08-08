"""
BLACKDARK — Explicit Terms / Disclaimer acceptance gate (SEC/MiCA posture).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger("BLACKDARK.TermsConsent")

TERMS_VERSION = os.getenv("TERMS_VERSION", "2026-03-28-v2").strip() or "2026-03-28-v2"
TERMS_COOKIE = "bd_terms_v"
ACCEPTANCE_REQUIRED = os.getenv("TERMS_ACCEPTANCE_REQUIRED", "true").lower() in {
    "1",
    "true",
    "yes",
}


def terms_required() -> bool:
    return ACCEPTANCE_REQUIRED


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cookie_accepted(request: Request) -> bool:
    raw = (request.cookies.get(TERMS_COOKIE) or "").strip()
    return raw == TERMS_VERSION


async def user_accepted(user: dict | None) -> bool:
    if not user or not user.get("id"):
        return False
    from database import fetch_user_by_id

    row = await fetch_user_by_id(int(user["id"]))
    if not row:
        return False
    accepted_at = row.get("terms_accepted_at")
    version = str(row.get("terms_version") or "")
    return bool(accepted_at) and version == TERMS_VERSION


async def has_accepted_terms(request: Request, user: dict | None = None) -> bool:
    if not terms_required():
        return True
    if cookie_accepted(request):
        return True
    if await user_accepted(user):
        return True
    return False


async def record_terms_acceptance(
    *,
    user: dict | None = None,
    source: str = "web",
    ip: str = "",
) -> dict[str, Any]:
    from security_auth import persist_auth_audit

    accepted_at = _utcnow_iso()
    if user and user.get("id"):
        from database import set_user_terms_acceptance

        await set_user_terms_acceptance(int(user["id"]), accepted_at, TERMS_VERSION)
    persist_auth_audit(
        event="terms_accepted",
        subject=str((user or {}).get("email") or "anonymous"),
        reason=source,
        ip=ip,
        meta={"terms_version": TERMS_VERSION, "accepted_at": accepted_at},
    )
    return {
        "accepted": True,
        "terms_version": TERMS_VERSION,
        "accepted_at": accepted_at,
        "cookie": TERMS_COOKIE,
    }


async def enforce_terms_acceptance(request: Request, user: dict | None = None) -> None:
    """Raise 403 if Oracle/AI surfaces are used without Terms acceptance."""
    if await has_accepted_terms(request, user):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error": "terms_not_accepted",
            "message": "You must accept the Terms of Service and Risk Disclaimer before using the Oracle.",
            "redirect_url": "/terms",
            "terms_version": TERMS_VERSION,
            "accept_api": "POST /api/legal/accept-terms",
        },
    )


def terms_status_payload(accepted: bool) -> dict[str, Any]:
    return {
        "required": terms_required(),
        "accepted": accepted,
        "terms_version": TERMS_VERSION,
        "cookie_name": TERMS_COOKIE,
        "terms_url": "/terms",
        "privacy_url": "/privacy",
        "disclaimer_url": "/disclaimer",
        "deletion_url": "/request-deletion",
    }
