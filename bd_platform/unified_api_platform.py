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
_MERGED_FEATURE_IDS = (162, 163, 171, 188, 205)
_API_VERSION = "v1"
_RATE_LIMIT_PER_MIN = 60

# Daily quotas — #188 SanAPI-style (merged into Unified API)
_DAILY_QUOTAS: dict[str, int] = {
    "free": 100,
    "pro": 1000,
    "elite": 1000,
    "quant": 1000,
    "whale": 1000,
    "institutional": 10000,
}

# UI parity: metric field names must match dashboard/UI exactly
_METRIC_CONTRACTS: dict[str, list[str]] = {
    "price": ["price_usd", "change_24h_pct", "exchange"],
    "oracle": ["verdict", "confidence_score", "headline"],
    "sentiment": ["weighted_sentiment_score", "sentiment_label", "social_volume_display"],
    "social_volume": ["raw_volume", "unique_volume", "weighted_volume", "display"],
    "liquidity": ["concentration", "health_score"],
    "onchain": ["mvrv_proxy", "sopr_proxy", "nvt"],
    "financial": ["var", "nvt", "mvrv_proxy", "sopr_proxy"],
}

# Core endpoint catalog
_ENDPOINTS: tuple[dict[str, str], ...] = (
    {"path": "/api/v1/platform/price", "method": "GET", "metric": "price"},
    {"path": "/api/v1/platform/oracle", "method": "GET", "metric": "oracle"},
    {"path": "/api/v1/platform/sentiment", "method": "GET", "metric": "sentiment"},
    {"path": "/api/v1/platform/social-volume", "method": "GET", "metric": "social_volume"},
    {"path": "/api/v1/platform/liquidity", "method": "GET", "metric": "liquidity"},
    {"path": "/api/v1/platform/onchain", "method": "GET", "metric": "onchain"},
    {"path": "/api/v1/platform/financial", "method": "GET", "metric": "financial"},
    {"path": "/api/v1/platform/events", "method": "GET", "metric": "events"},
    {"path": "/api/v1/platform/exit-zone", "method": "GET", "metric": "exit_zone"},
    {"path": "/api/v1/platform/contract-safety", "method": "GET", "metric": "contract_safety"},
    {"path": "/api/v1/platform/graphql", "method": "POST", "metric": "graphql", "tier": "pro+"},
    {"path": "/api/v1/platform/community/chart", "method": "GET", "metric": "community_chart", "tier": "community"},
    {"path": "/api/v1/platform/community/oracle", "method": "GET", "metric": "community_oracle", "tier": "community"},
    {"path": "/api/v1/platform/community/status", "method": "GET", "metric": "community_status"},
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
    tier: str = "free",
    cached: bool = False,
    endpoint: str | None = None,
) -> dict[str, Any]:
    """Consistent API response envelope with freshness metadata."""
    envelope = {
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
    if endpoint:
        try:
            from bd_platform.b2b_sla_monitoring import build_response_headers, get_cache_policy

            policy = get_cache_policy(tier)
            envelope["metadata"]["cache_policy"] = policy
            envelope["metadata"]["response_headers"] = build_response_headers(
                tier, cached=cached,
            )
            envelope["metadata"]["update_frequency"] = policy["update_frequency_display"]
        except Exception:
            pass
    return envelope


def check_api_rate_limit(client_key: str) -> dict[str, Any] | None:
    """Per-minute rate limit check — returns error dict if blocked."""
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


def check_daily_quota(client_key: str, tier: str = "free") -> dict[str, Any] | None:
    """Daily quota check — #188 tier entitlements (Pro 1000, Institution 10000)."""
    from auth_service import normalize_tier

    normalized = normalize_tier(tier)
    limit = _DAILY_QUOTAS.get(normalized, _DAILY_QUOTAS["free"])
    try:
        from viral_capacity import check_rate_limit

        check_rate_limit(
            f"daily:{client_key}",
            limit=limit,
            window_sec=86400,
            prefix="unified_api_daily",
        )
        return None
    except Exception as exc:
        if hasattr(exc, "status_code") or "rate" in str(exc).lower():
            return {
                "ok": False,
                "error": "daily_quota_exceeded",
                "message": f"Daily API quota exceeded ({limit}/day for {normalized})",
                "tier": normalized,
                "daily_limit": limit,
                "api_version": _API_VERSION,
            }
        return None


def get_tier_quota(tier: str) -> dict[str, Any]:
    from auth_service import normalize_tier

    normalized = normalize_tier(tier)
    return {
        "tier": normalized,
        "daily_limit": _DAILY_QUOTAS.get(normalized, _DAILY_QUOTAS["free"]),
        "per_minute_limit": _RATE_LIMIT_PER_MIN,
    }


async def fetch_price(asset: str, *, exchange: str | None = None, tier: str = "free") -> dict[str, Any]:
    from bd_platform.b2b_sla_monitoring import B2BSLAMiddleware
    from bd_platform.free_market_data import binance_futures_snapshot

    sym = asset.upper().replace("/USDT", "")
    endpoint = "/api/v1/platform/price"
    with B2BSLAMiddleware(endpoint, tier=tier):
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
        tier=tier,
        endpoint=endpoint,
    )


async def fetch_oracle(asset: str, *, tier: str = "free") -> dict[str, Any]:
    from bd_platform.b2b_sla_monitoring import B2BSLAMiddleware
    from bd_platform.decision_intelligence_engine import generate_decision_signal
    from bd_platform.verifiable_ai_engine import enrich_oracle_envelope

    endpoint = "/api/v1/platform/oracle"
    with B2BSLAMiddleware(endpoint, tier=tier):
        signal = await generate_decision_signal(asset, include_backtest=False)
    sig = signal.get("signal") or {}
    envelope = _envelope(
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
        tier=tier,
        endpoint=endpoint,
    )
    return await enrich_oracle_envelope(envelope, asset)


async def fetch_sentiment(asset: str) -> dict[str, Any]:
    from bd_platform.sentiment_intelligence import analyze_asset_sentiment

    result = await analyze_asset_sentiment(asset)
    return _envelope(result, asset=asset.upper(), source="sentiment_intelligence")


async def fetch_social_volume(asset: str) -> dict[str, Any]:
    """#195 unique social volume — same fields as UI sentiment panel."""
    from bd_platform.unique_social_volume import analyze_unique_social_volume

    result = await analyze_unique_social_volume(asset)
    return _envelope(result, asset=asset.upper(), source="unique_social_volume")


async def fetch_onchain(asset: str) -> dict[str, Any]:
    """On-chain metrics — UI parity via research_lab financial models."""
    from research_lab import compute_financial_models

    models = await compute_financial_models(asset)
    payload = {
        "ok": "error" not in models,
        "metric": "onchain",
        "mvrv_proxy": models.get("mvrv_proxy"),
        "sopr_proxy": models.get("sopr_proxy"),
        "nvt": models.get("nvt"),
        "price": models.get("price"),
        "timestamp": models.get("timestamp"),
    }
    return _envelope(payload, asset=asset.upper(), source="research_lab")


async def fetch_financial(asset: str, *, notional: float = 10_000) -> dict[str, Any]:
    """Financial metrics — VaR, NVT, MVRV, SOPR same as Research Lab UI."""
    from research_lab import compute_financial_models

    models = await compute_financial_models(asset, notional=notional)
    payload = {
        "ok": "error" not in models,
        "metric": "financial",
        "var": models.get("var"),
        "nvt": models.get("nvt"),
        "mvrv_proxy": models.get("mvrv_proxy"),
        "sopr_proxy": models.get("sopr_proxy"),
        "notional_for_var": models.get("notional_for_var"),
        "timestamp": models.get("timestamp"),
    }
    return _envelope(payload, asset=asset.upper(), source="research_lab")


async def execute_graphql_query(
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    tier: str = "free",
) -> dict[str, Any]:
    """
    Optional GraphQL for Pro+ — wraps canonical REST metrics.
    Principle: what you see in UI = what you get in API.
    """
    from auth_service import normalize_tier, tier_meets

    if not tier_meets("pro", normalize_tier(tier)):
        return {
            "ok": False,
            "error": "graphql_pro_required",
            "message": "GraphQL access requires Pro tier or above",
        }

    variables = variables or {}
    asset = str(variables.get("asset") or "BTC")
    q = query.lower().strip()

    data: dict[str, Any] = {}
    if "price" in q:
        data["price"] = (await fetch_price(asset))["data"]
    if "sentiment" in q or "social" in q:
        data["sentiment"] = (await fetch_sentiment(asset))["data"]
    if "socialvolume" in q.replace("_", "").replace(" ", "") or "social_volume" in q:
        data["social_volume"] = (await fetch_social_volume(asset))["data"]
    if "oracle" in q:
        data["oracle"] = (await fetch_oracle(asset))["data"]
    if "liquidity" in q:
        data["liquidity"] = (await fetch_liquidity(asset))["data"]
    if "onchain" in q or "financial" in q:
        data["financial"] = (await fetch_financial(asset))["data"]

    if not data:
        return {"ok": False, "error": "unsupported_query", "hint": "Try: { price sentiment oracle }"}

    return {
        "ok": True,
        "api_version": _API_VERSION,
        "feature_id": _FEATURE_ID,
        "graphql": True,
        "asset": asset.upper(),
        "data": data,
        "ui_parity": True,
        "timestamp": _utcnow(),
    }


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
        "merged_feature_ids": list(_MERGED_FEATURE_IDS),
        "title": "Unified API Platform",
        "principle": "What you see in UI = what you get in API",
        "api_version": _API_VERSION,
        "endpoint_count": len(_ENDPOINTS),
        "endpoints": list(_ENDPOINTS),
        "rate_limit_per_min": _RATE_LIMIT_PER_MIN,
        "daily_quotas": _DAILY_QUOTAS,
        "metric_contracts": _METRIC_CONTRACTS,
        "rest_required": True,
        "graphql_optional": "Pro+ tier at /api/v1/platform/graphql",
        "idempotent_reads": True,
        "freshness_metadata": True,
        "contract_tests": "tests/test_research_sentiment_api.py",
        "integrated_features": ["#163", "#171", "#188", "#195", "#205", "#231"],
        "b2b_sla_monitoring": {
            "feature_id": 231,
            "merged_into": 219,
            "middleware": True,
            "enterprise_dashboard": True,
        },
        "timestamp": _utcnow(),
    }
