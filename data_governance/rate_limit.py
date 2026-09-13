"""Rate limit quota governance (DIG-026)."""

from __future__ import annotations

from typing import Any

_LIMITS: dict[str, int] = {"default": 1000, "live_trading": 100}


def quota_for_purpose(purpose: str) -> int:
    return _LIMITS.get(purpose, _LIMITS["default"])


def check_rate_quota(source_id: str, purpose: str) -> dict[str, Any]:
    return {"allowed": True, "quota": quota_for_purpose(purpose), "source_id": source_id}
