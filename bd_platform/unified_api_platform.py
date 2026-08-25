"""
Unified API Platform — Feature #162 (Wave 2).

Versioned REST API with consistent schema, rate limits, freshness metadata.
Merged scope: #162 + #163 + #171 foundations — 5-10 core endpoints only.

NOT 50 endpoints — start small, contract-tested.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.UnifiedAPI")

_FEATURE_ID = 162
_API_VERSION = "v1"
_RATE_LIMIT_PER_MIN = 60

# Core endpoint catalog
_ENDPOINTS: tuple[dict[str, str], ...] = (
    {"path": "/api/v1/platform/price", "method": "GET", "metric": "price"},
    {"path": "/api/v1/platform/oracle", "method": "GET", "metric": "oracle"},
    {"path": "/api/v1/platform/sentiment", "method": "GET", "metric": "sentiment"},
    {"path": "/api/v1/platform/liquidity", "method": "GET", "metric": "liquidity"},
    {"path": "/api/v1/platform/events", "method": "GET", "metric": "events"},
    {"path": "/api/v1/platform/exit-zone", "method": "GET", "metric": "exit_zone"},
    {"path": "/api/v1/platform/contract-safety", "method": "GET", "metric": "contract_safety"},
    {"path": "/api/v1/platform/status", "method": "GET", "metric": "status"},
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _envelope(
    data: dict[str, Any],
    *,
    asset: str | None = None,
    source: str = "blackdark",
    fetched_at: str | None = None,
) -> dict[str, Any]:
    """Consistent API response envelope with freshness metadata."""
    return {
        "ok": data.get("ok", True),
        "api_version": _API_VERSION,
        "feature_id": _FEATURE_ID,
        "asset": asset,
        "data": data,
        "metadata": {
            "source": source,
            "fetched_at": fetched_at or data.get("timestamp") or _utcnow(),
            "freshness_tz": "UTC",
            "idempotent_read": True,
            "schema": "canonical_v1",
        },
        "timestamp": _utcnow(),
    }


def check_api_rate_limit(client_key: str) -> dict[str, Any] | None:
    """Rate limit check — returns error dict if blocked."""
    try:
        from viral_capacity import check_rate_limit

        check_rate_limit(
            client_key,
            limit=_RATE_LIMIT_PER_MIN,
            window_sec=60,
            prefix="unified_api",
        )
        return None
    except Exception as exc:
        if hasattr(exc, "status_code") or "rate" in str(exc).lower():
            return {
                "ok": False,
                "error": "rate_limited",
                "message": "Rate limit exceeded — retry in 60 seconds",
                "api_version": _API_VERSION,
            }
        return None


async def fetch_price(asset: str, *, exchange: str | None = None) -> dict[str, Any]:
    from bd_platform.free_market_data import binance_futures_snapshot

    sym = asset.upper().replace("/USDT", "")
    snap = await binance_futures_snapshot(sym)
    return _envelope(
        {
            "ok": bool(snap.get("mark_price")),
            "metric": "price",
            "price_usd": snap.get("mark_price"),
            "change_24h_pct": snap.get("change_24h_pct"),
            "exchange": exchange or "binance",
            "timestamp": snap.get("timestamp"),
        },
        asset=sym,
        source=snap.get("source", "binance_futures_public"),
        fetched_at=snap.get("timestamp"),
    )


async def fetch_oracle(asset: str) -> dict[str, Any]:
    from bd_platform.decision_intelligence_engine import generate_decision_signal

    signal = await generate_decision_signal(asset, include_backtest=False)
    sig = signal.get("signal") or {}
    return _envelope(
        {
            "ok": signal.get("ok", True),
            "metric": "oracle",
            "verdict": sig.get("verdict"),
            "headline": f"{sig.get('verdict')} — confidence {sig.get('confidence', 0):.0f}%",
            "confidence_score": sig.get("confidence"),
            "timestamp": signal.get("timestamp"),
        },
        asset=asset.upper(),
        source="decision_intelligence_engine",
        fetched_at=signal.get("timestamp"),
    )


async def fetch_sentiment(asset: str) -> dict[str, Any]:
    from bd_platform.sentiment_intelligence import analyze_asset_sentiment

    result = await analyze_asset_sentiment(asset)
    return _envelope(result, asset=asset.upper(), source="sentiment_intelligence")


async def fetch_liquidity(asset: str) -> dict[str, Any]:
    from bd_platform.liquidity_health_check import analyze_liquidity_health

    result = await analyze_liquidity_health(asset)
    return _envelope(result, asset=asset.upper(), source="liquidity_health_check")


async def fetch_events(limit: int = 20) -> dict[str, Any]:
    from bd_platform.industry_event_monitor import get_event_feed

    feed = get_event_feed(limit=limit)
    return _envelope(feed, source="industry_event_monitor")


async def fetch_exit_zone(asset: str) -> dict[str, Any]:
    from bd_platform.exit_strategy_assistant import compute_recommended_exit_zone

    result = await compute_recommended_exit_zone(asset)
    return _envelope(result, asset=asset.upper(), source="exit_strategy_assistant")


async def fetch_contract_safety(address: str, *, chain: str = "ethereum") -> dict[str, Any]:
    from bd_platform.defi_safety_layer import scan_contract_risk

    result = await scan_contract_risk(address, chain=chain)
    return _envelope(result, source="defi_safety_layer")


def unified_api_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Unified API Platform",
        "api_version": _API_VERSION,
        "endpoint_count": len(_ENDPOINTS),
        "endpoints": list(_ENDPOINTS),
        "rate_limit_per_min": _RATE_LIMIT_PER_MIN,
        "idempotent_reads": True,
        "freshness_metadata": True,
        "contract_tests": "tests/test_unified_api_platform.py",
        "integrated_features": ["#163", "#171"],
        "timestamp": _utcnow(),
    }
