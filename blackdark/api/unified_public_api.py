"""
BLACKDARK API — Feature #183 (Unified API Platform #162).

Versioned read-only REST contracts with auth, rate limits, and null semantics.
Product name: BLACKDARK API
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Path

from blackdark.api.api_auth import require_blackdark_api_key
from blackdark.api.canonical_intelligence import (
    blackdark_api_status,
    get_market_health_intelligence,
    get_price_intelligence,
    get_risk_score_intelligence,
)

logger = logging.getLogger("BLACKDARK.UnifiedPublicAPI")

_FEATURE_ID = 183
blackdark_api_router = APIRouter(tags=["blackdark-api"])


def _envelope(data: dict[str, Any], *, auth: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": data.get("ok", True),
        "api_version": "v1",
        "product": "BLACKDARK API",
        "feature_id": _FEATURE_ID,
        "parent_feature": 162,
        "read_only": True,
        "auth_tier": auth.get("tier"),
        "data": data,
    }


@blackdark_api_router.get("/api/v1/blackdark/status")
async def blackdark_api_status_route(auth: dict = Depends(require_blackdark_api_key)):
    """BLACKDARK API platform status."""
    return _envelope(blackdark_api_status(), auth=auth)


@blackdark_api_router.get("/api/v1/blackdark/price/{asset}")
async def blackdark_price_route(
    asset: str = Path(..., min_length=1, max_length=16),
    auth: dict = Depends(require_blackdark_api_key),
):
    """Aggregated price with source/freshness metadata."""
    data = await get_price_intelligence(asset)
    return _envelope(data, auth=auth)


@blackdark_api_router.get("/api/v1/blackdark/market-health/{asset}")
async def blackdark_market_health_route(
    asset: str = Path(..., min_length=1, max_length=16),
    auth: dict = Depends(require_blackdark_api_key),
):
    """Market health dashboard intelligence."""
    data = await get_market_health_intelligence(asset)
    return _envelope(data, auth=auth)


@blackdark_api_router.get("/api/v1/blackdark/risk-score/{asset}")
async def blackdark_risk_score_route(
    asset: str = Path(..., min_length=1, max_length=16),
    auth: dict = Depends(require_blackdark_api_key),
):
    """Risk/confidence score (experimental rule-based)."""
    data = await get_risk_score_intelligence(asset)
    return _envelope(data, auth=auth)


CONTRACT_SCHEMAS: dict[str, dict[str, Any]] = {
    "price": {
        "required": ["ok", "asset", "price_usd", "freshness", "timestamp"],
        "nullable": ["price_usd", "vwap_usd", "change_24h_pct", "outlier_count", "source_count"],
    },
    "market_health": {
        "required": ["ok", "asset", "overall_score", "overall_status", "freshness", "timestamp"],
        "nullable": ["overall_score", "classification_reason", "pillar_count"],
    },
    "risk_score": {
        "required": ["ok", "asset", "risk_score", "confidence_score", "freshness", "timestamp"],
        "nullable": ["risk_score", "confidence_score", "confidence_band"],
    },
}
