"""Pluggable bot protection — ID-033."""

from __future__ import annotations

import os
from typing import Any


def bot_provider_name() -> str:
    if os.getenv("TURNSTILE_SECRET_KEY", "").strip():
        return "turnstile"
    if os.getenv("RECAPTCHA_SECRET_KEY", "").strip():
        return "recaptcha"
    return "none"


async def verify_bot_challenge(token: str | None, *, remote_ip: str = "") -> dict[str, Any]:
    provider = bot_provider_name()
    if provider == "none":
        return {"verified": True, "provider": "none", "skipped": True}
    if not token:
        return {"verified": False, "provider": provider, "error": "missing_token"}
    secret = os.getenv("TURNSTILE_SECRET_KEY") or os.getenv("RECAPTCHA_SECRET_KEY") or ""
    try:
        import httpx

        url = (
            "https://challenges.cloudflare.com/turnstile/v0/siteverify"
            if provider == "turnstile"
            else "https://www.google.com/recaptcha/api/siteverify"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, data={"secret": secret, "response": token, "remoteip": remote_ip})
        data = resp.json()
        return {"verified": bool(data.get("success")), "provider": provider}
    except Exception:
        return {"verified": False, "provider": provider, "error": "verify_failed"}
