"""Login abuse protection — ID-032, ID-061, ID-069."""

from __future__ import annotations

import os
import time
from typing import Any

from security_auth import check_login_rate_limit, record_login_failure

GENERIC_AUTH_ERROR = "If an account exists, instructions have been sent."
GENERIC_LOGIN_ERROR = "Invalid email or password"


def enforce_login_rate_limit(email: str, *, ip: str = "") -> None:
    check_login_rate_limit(email)
    if ip:
        check_login_rate_limit(f"ip:{ip}")


def record_failed_login(email: str, *, reason: str = "invalid_credentials") -> None:
    record_login_failure(email)
    try:
        from security_events import record_security_event

        record_security_event("login_failure", severity="warning", actor=email, detail={"reason": reason})
    except Exception:
        pass


def generic_forgot_password_response() -> dict[str, Any]:
    return {"status": "ok", "message": GENERIC_AUTH_ERROR}


async def timing_normalized_delay(start: float, *, minimum_ms: int = 250) -> None:
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms < minimum_ms:
        await __import__("asyncio").sleep((minimum_ms - elapsed_ms) / 1000)
