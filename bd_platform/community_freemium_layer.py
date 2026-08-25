"""
Community Freemium Layer — Feature #205 (merged into #162 Unified API).

Free/community access with clear limits, chart watermark, and upsell path.
Uses same engine as Unified API — no separate charts engine.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.CommunityFreemium")

_FEATURE_ID = 205
_MERGED_INTO = 162
_WATERMARK = "Powered by BLACKDARK"
_SIGNUP_URL = "/create-checkout-session?tier=pro"

_COMMUNITY_LIMITS = {
    "daily_calls": 100,
    "max_assets": 5,
    "resolution": "1D",
    "realtime": False,
    "sub_second": False,
}

_ALLOWED_ASSETS = frozenset({"BTC", "ETH", "SOL", "BNB", "XRP"})
_ALLOWED_RESOLUTIONS = frozenset({"1D", "1d", "D"})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def community_tier_limits() -> dict[str, Any]:
    return {
        "tier": "community",
        "display": "Community Tier: 100 calls/day | 5 assets | 1D resolution",
        "daily_calls": _COMMUNITY_LIMITS["daily_calls"],
        "max_assets": _COMMUNITY_LIMITS["max_assets"],
        "allowed_assets": sorted(_ALLOWED_ASSETS),
        "resolution": _COMMUNITY_LIMITS["resolution"],
        "watermark": _WATERMARK,
        "upsell": "Upgrade for real-time + sub-second",
        "upsell_url": _SIGNUP_URL,
        "parity_engine": "unified_api_platform",
        "separate_charts_engine": False,
    }


def validate_community_request(
    asset: str,
    *,
    resolution: str = "1D",
) -> dict[str, Any] | None:
    """Return error dict if community limits violated."""
    sym = asset.upper().replace("/USDT", "")
    if sym not in _ALLOWED_ASSETS:
        return {
            "ok": False,
            "error": "asset_not_in_community_tier",
            "message": f"Community tier supports: {', '.join(sorted(_ALLOWED_ASSETS))}",
            "upsell": "Upgrade for real-time + sub-second",
            "upsell_url": _SIGNUP_URL,
        }
    if resolution.upper() not in {r.upper() for r in _ALLOWED_RESOLUTIONS}:
        return {
            "ok": False,
            "error": "resolution_not_allowed",
            "message": "Community tier: 1D resolution only",
            "upsell": "Upgrade for real-time + sub-second",
        }
    return None


def check_community_daily_quota(client_key: str) -> dict[str, Any] | None:
    try:
        from viral_capacity import check_rate_limit

        check_rate_limit(
            f"community:{client_key}",
            limit=_COMMUNITY_LIMITS["daily_calls"],
            window_sec=86400,
            prefix="community_freemium",
        )
        return None
    except Exception as exc:
        if hasattr(exc, "status_code") or "rate" in str(exc).lower():
            return {
                "ok": False,
                "error": "community_quota_exceeded",
                "message": f"Community tier limit: {_COMMUNITY_LIMITS['daily_calls']} calls/day",
                "upsell": "Upgrade for real-time + sub-second",
                "upsell_url": _SIGNUP_URL,
            }
        return None


async def fetch_community_chart(asset: str, *, resolution: str = "1D") -> dict[str, Any]:
    """Community chart — same engine as platform charts with watermark + limits."""
    t0 = time.perf_counter()
    blocked = validate_community_request(asset, resolution=resolution)
    if blocked:
        return blocked

    sym = asset.upper().replace("/USDT", "")
    from bd_platform.tradingview_bridge import chart_config
    from bd_platform.unified_api_platform import fetch_price

    chart = chart_config(f"{sym}USDT")
    price_env = await fetch_price(sym)
    price_data = price_env.get("data") or {}

    elapsed = (time.perf_counter() - t0) * 1000
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "tier": "community",
        "asset": sym,
        "resolution": "1D",
        "chart": chart,
        "price": price_data.get("price_usd"),
        "change_24h_pct": price_data.get("change_24h_pct"),
        "watermark": _WATERMARK,
        "watermark_required": True,
        "upsell": "Upgrade for real-time + sub-second",
        "upsell_url": _SIGNUP_URL,
        "limits": community_tier_limits(),
        "latency_ms": round(elapsed, 1),
        "timestamp": _utcnow(),
    }


async def fetch_community_oracle(asset: str) -> dict[str, Any]:
    """Community oracle — same unified API engine with freemium limits."""
    blocked = validate_community_request(asset)
    if blocked:
        return blocked

    sym = asset.upper().replace("/USDT", "")
    from bd_platform.unified_api_platform import fetch_oracle

    result = await fetch_oracle(sym)
    data = result.get("data") or {}
    return {
        "ok": result.get("ok", True),
        "feature_id": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "tier": "community",
        "asset": sym,
        "oracle": data,
        "watermark": _WATERMARK,
        "upsell": "Upgrade for real-time + sub-second",
        "upsell_url": _SIGNUP_URL,
        "limits": community_tier_limits(),
        "timestamp": _utcnow(),
    }


def community_freemium_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "layer": "freemium",
        "limits": community_tier_limits(),
        "watermark": _WATERMARK,
        "parity_with_unified_api": True,
        "separate_charts_engine": False,
        "timestamp": _utcnow(),
    }
