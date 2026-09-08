"""Phone OTP fallback — ID-013 (provider-pluggable)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

_otp_store: dict[str, dict[str, Any]] = {}


async def send_phone_otp(user_id: int, phone: str) -> dict[str, Any]:
    code = f"{secrets.randbelow(900000) + 100000:06d}"
    _otp_store[f"{user_id}:{phone}"] = {
        "code_hash": __import__("hashlib").sha256(code.encode()).hexdigest(),
        "expires": (datetime.now(UTC) + timedelta(minutes=10)).timestamp(),
        "attempts": 0,
    }
    provider = __import__("os").getenv("SMS_PROVIDER", "stub")
    return {"sent": True, "provider": provider, "debug_code": code if __import__("os").getenv("IDENTITY_DEBUG_TOKENS") == "true" else None}


async def verify_phone_otp(user_id: int, phone: str, code: str) -> bool:
    key = f"{user_id}:{phone}"
    row = _otp_store.get(key)
    if not row or float(row["expires"]) < datetime.now(UTC).timestamp():
        _otp_store.pop(key, None)
        return False
    row["attempts"] = int(row["attempts"]) + 1
    if row["attempts"] > 5:
        _otp_store.pop(key, None)
        return False
    ok = __import__("hashlib").sha256(code.encode()).hexdigest() == row["code_hash"]
    if ok:
        _otp_store.pop(key, None)
        from database import set_user_phone_verified

        await set_user_phone_verified(user_id, phone)
    return ok
