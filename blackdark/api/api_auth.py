"""
BLACKDARK API auth — Feature #183 (Unified API Platform #162).

API key validation + tier-aware rate limits for public read-only endpoints.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Annotated, Any

from fastapi import Header, HTTPException

_RATE_BUCKETS: dict[str, list[float]] = defaultdict(list)

_TIER_LIMITS = {
    "free": 30,
    "pro": 300,
    "institutional": 3000,
    "quant": 5000,
    "demo": 60,
}


def _resolve_tier(api_key: str) -> str:
    key = api_key.strip()
    if not key:
        return "free"
    demo = (os.getenv("B2B_DEMO_API_KEY") or os.getenv("BLACKDARK_DEMO_API_KEY") or "").strip()
    if demo and key == demo:
        return "demo"
    admin = (os.getenv("ADMIN_API_KEY") or os.getenv("BLACKDARK_PUBLIC_API_KEY") or "").strip()
    if admin and key == admin:
        return "institutional"
    inst = (os.getenv("BLACKDARK_INSTITUTION_API_KEY") or "").strip()
    if inst and key == inst:
        return "institutional"
    pro = (os.getenv("BLACKDARK_PRO_API_KEY") or "").strip()
    if pro and key == pro:
        return "pro"
    # Unknown keys get free-tier limits if key is present (authenticated free)
    return "free" if len(key) >= 8 else "free"


def _check_rate_limit(key_id: str, limit: int, *, window_sec: int = 60) -> None:
    now = time.time()
    bucket = _RATE_BUCKETS[key_id]
    _RATE_BUCKETS[key_id] = [t for t in bucket if now - t < window_sec]
    if len(_RATE_BUCKETS[key_id]) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for BLACKDARK API")
    _RATE_BUCKETS[key_id].append(now)


def verify_blackdark_api_key(provided: str | None) -> dict[str, Any]:
    """Validate API key — returns tier metadata. Demo key allowed for free tier."""
    key = (provided or "").strip()
    if not key:
        raise HTTPException(status_code=401, detail="X-API-Key required for BLACKDARK API")
    if len(key) < 8:
        raise HTTPException(status_code=401, detail="Invalid API key")
    tier = _resolve_tier(key)
    return {"tier": tier, "key_id": f"key:{tier}:{key[:6]}", "authenticated": True}


async def require_blackdark_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, Any]:
    auth = verify_blackdark_api_key(x_api_key)
    limit = _TIER_LIMITS.get(auth["tier"], 30)
    _check_rate_limit(auth["key_id"], limit)
    auth["rate_limit_per_min"] = limit
    return auth
