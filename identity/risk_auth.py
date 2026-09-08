"""Risk-based authentication signals — ID-031."""

from __future__ import annotations

from typing import Any


async def assess_login_risk(
    *,
    user_id: int | None,
    ip: str = "",
    country: str = "",
    device_fingerprint: str = "",
    action: str = "login",
) -> dict[str, Any]:
    from database import fetch_recent_login_countries

    signals: list[str] = []
    score = 0
    if user_id and country:
        recent = await fetch_recent_login_countries(user_id)
        if recent and country not in recent:
            signals.append("new_country")
            score += 30
    if device_fingerprint:
        signals.append("device_fingerprint_observed")
    if action in {"password_reset", "account.recovery"}:
        signals.append("sensitive_recovery")
        score += 20
    return {
        "score": score,
        "signals": signals,
        "require_bot_challenge": score >= 40,
        "require_step_up": score >= 60,
    }
