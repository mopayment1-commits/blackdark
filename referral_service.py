"""
BLACKDARK — Viral referral / invite growth loop.
"""

from __future__ import annotations

import logging
import re
import secrets
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("BLACKDARK.Referral")

_CODE_RE = re.compile(r"^[A-Z0-9]{4,16}$")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_referral_code(raw: str | None) -> str:
    code = (raw or "").strip().upper().replace("-", "").replace(" ", "")
    if not _CODE_RE.match(code):
        return ""
    return code


def generate_referral_code(seed: str = "") -> str:
    base = re.sub(r"[^A-Z0-9]", "", (seed or "").upper())[:4]
    if len(base) < 2:
        base = "BD"
    return f"{base}{secrets.token_hex(3).upper()}"


async def ensure_user_referral_code(user_id: int, email: str = "") -> str:
    from database import fetch_user_by_id, set_user_referral_code

    user = await fetch_user_by_id(int(user_id))
    if not user:
        raise ValueError("User not found")
    existing = normalize_referral_code(str(user.get("referral_code") or ""))
    if existing:
        return existing
    # Prefer email local-part prefix
    local = (email or str(user.get("email") or "")).split("@")[0]
    for _ in range(8):
        code = generate_referral_code(local)
        try:
            await set_user_referral_code(int(user_id), code)
            return code
        except Exception:
            continue
    code = generate_referral_code("BD")
    await set_user_referral_code(int(user_id), code)
    return code


async def resolve_referrer(code: str) -> dict[str, Any] | None:
    from database import fetch_user_by_referral_code

    cleaned = normalize_referral_code(code)
    if not cleaned:
        return None
    return await fetch_user_by_referral_code(cleaned)


async def apply_referral_on_signup(
    *,
    new_user_id: int,
    new_email: str,
    referral_code: str | None,
) -> dict[str, Any]:
    """Attribute signup to referrer; extend trial bonus for both sides when valid."""
    from database import insert_referral_event, set_user_referred_by

    cleaned = normalize_referral_code(referral_code)
    if not cleaned:
        return {"applied": False, "reason": "no_code"}

    referrer = await resolve_referrer(cleaned)
    if not referrer:
        return {"applied": False, "reason": "unknown_code"}
    if int(referrer["id"]) == int(new_user_id):
        return {"applied": False, "reason": "self_referral"}

    await set_user_referred_by(int(new_user_id), cleaned, int(referrer["id"]))
    await insert_referral_event(
        referrer_user_id=int(referrer["id"]),
        referred_user_id=int(new_user_id),
        referral_code=cleaned,
        event_type="signup",
    )

    # Growth reward: +3 trial days for both sides (best-effort)
    bonus: dict[str, Any] = {"referred_bonus_days": 0, "referrer_bonus_days": 0}
    try:
        from database import extend_pro_trial

        await extend_pro_trial(new_email, 3)
        bonus["referred_bonus_days"] = 3
        ref_email = str(referrer.get("email") or "")
        if ref_email:
            await extend_pro_trial(ref_email, 3)
            bonus["referrer_bonus_days"] = 3
    except Exception:
        logger.debug("referral trial bonus skipped", exc_info=True)

    return {
        "applied": True,
        "referral_code": cleaned,
        "referrer_user_id": int(referrer["id"]),
        **bonus,
        "at": _utcnow(),
    }


async def referral_stats(user_id: int) -> dict[str, Any]:
    import os

    from database import count_referrals_for_user, fetch_user_by_id

    user = await fetch_user_by_id(int(user_id))
    if not user:
        return {"authenticated": False}
    code = await ensure_user_referral_code(int(user_id), str(user.get("email") or ""))
    count = await count_referrals_for_user(int(user_id))
    path = f"/?ref={code}"
    base = (os.getenv("APP_BASE_URL") or "").rstrip("/")
    share_url = f"{base}{path}" if base else path
    return {
        "authenticated": True,
        "code": code,
        "referral_code": code,
        "invite_url_path": path,
        "share_url": share_url,
        "successful_referrals": count,
        "signups": count,
        "reward": "+3 Pro trial days for you and your invitee on each successful signup",
    }
