"""Unified API Platform v1 router — Features #162, #174, #176."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import optional_user_from_request

router = APIRouter(prefix="/api/v1/platform", tags=["unified-api"], responses=COMMON_ERROR_RESPONSES)


def _client_key(request: Request, user: dict | None) -> str:
    if user and user.get("id"):
        return f"user:{user['id']}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


def _user_tier(user: dict | None) -> str:
    return str((user or {}).get("tier") or "free")


def _rate_limit(request: Request, user: dict | None = Depends(optional_user_from_request)) -> None:
    from bd_platform.unified_api_platform import check_api_rate_limit, check_daily_quota

    key = _client_key(request, user)
    blocked = check_api_rate_limit(key)
    if blocked:
        raise HTTPException(status_code=429, detail=blocked)
    daily = check_daily_quota(key, _user_tier(user))
    if daily:
        raise HTTPException(status_code=429, detail=daily)


@router.get("/status")
async def unified_api_status_route():
    from bd_platform.unified_api_platform import unified_api_status

    return unified_api_status()


@router.get("/price")
async def unified_api_price_route(
    request: Request,
    asset: str = Query("BTC"),
    exchange: str | None = Query(None),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_price

    return await fetch_price(asset, exchange=exchange)


@router.get("/oracle")
async def unified_api_oracle_route(
    request: Request,
    asset: str = Query("BTC"),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_oracle

    return await fetch_oracle(asset)


@router.get("/sentiment")
async def unified_api_sentiment_route(
    request: Request,
    asset: str = Query("BTC"),
    _user: dict | None = Depends(optional_user_from_request),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_sentiment

    return await fetch_sentiment(asset)


@router.get("/social-volume")
async def unified_api_social_volume_route(
    request: Request,
    asset: str = Query("BTC"),
    _user: dict | None = Depends(optional_user_from_request),
    _rl: None = Depends(_rate_limit),
):
    """Unique social volume (#195) — same metric semantics as UI."""
    from bd_platform.unified_api_platform import fetch_social_volume

    return await fetch_social_volume(asset)


@router.get("/onchain")
async def unified_api_onchain_route(
    request: Request,
    asset: str = Query("BTC"),
    _user: dict | None = Depends(optional_user_from_request),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_onchain

    return await fetch_onchain(asset)


@router.get("/financial")
async def unified_api_financial_route(
    request: Request,
    asset: str = Query("BTC"),
    notional: float = Query(10000, ge=100),
    _user: dict | None = Depends(optional_user_from_request),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_financial

    return await fetch_financial(asset, notional=notional)


@router.get("/liquidity")
async def unified_api_liquidity_route(
    request: Request,
    asset: str = Query("ETH"),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_liquidity

    return await fetch_liquidity(asset)


@router.get("/events")
async def unified_api_events_route(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_events

    return await fetch_events(limit=limit)


@router.get("/exit-zone")
async def unified_api_exit_zone_route(
    request: Request,
    asset: str = Query("BTC"),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_exit_zone

    return await fetch_exit_zone(asset)


@router.get("/contract-safety")
async def unified_api_contract_safety_route(
    request: Request,
    address: str = Query(..., min_length=42, max_length=42),
    chain: str = Query("ethereum"),
    _user: dict | None = Depends(optional_user_from_request),
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_contract_safety

    return await fetch_contract_safety(address, chain=chain)


@router.post("/graphql")
async def unified_api_graphql_route(
    request: Request,
    body: dict = Body(...),
    user: dict | None = Depends(optional_user_from_request),
    _rl: None = Depends(_rate_limit),
):
    """Optional GraphQL for Pro+ — wraps canonical REST metrics (#188)."""
    from bd_platform.unified_api_platform import execute_graphql_query

    result = await execute_graphql_query(
        str(body.get("query") or ""),
        variables=body.get("variables") if isinstance(body.get("variables"), dict) else {},
        tier=_user_tier(user),
    )
    if not result.get("ok"):
        code = 403 if result.get("error") == "graphql_pro_required" else 400
        raise HTTPException(status_code=code, detail=result)
    return result


@router.get("/quotas")
async def unified_api_quotas_route(
    user: dict | None = Depends(optional_user_from_request),
):
    from bd_platform.unified_api_platform import get_tier_quota

    return {"ok": True, **get_tier_quota(_user_tier(user))}


@router.get("/coverage")
async def unified_api_coverage_route():
    """Connector coverage map with live parity (#194 + #200)."""
    from bd_platform.connector_coverage_map import build_coverage_map

    return await build_coverage_map()


@router.get("/coverage/status")
async def unified_api_coverage_status_route():
    from bd_platform.connector_coverage_map import connector_coverage_status

    return connector_coverage_status()


# ── Feature #205 — Community Freemium Layer (merged #162) ────────────────────


def _community_rate_limit(request: Request, user: dict | None = Depends(optional_user_from_request)) -> None:
    from bd_platform.community_freemium_layer import check_community_daily_quota

    key = _client_key(request, user)
    blocked = check_community_daily_quota(key)
    if blocked:
        raise HTTPException(status_code=429, detail=blocked)


@router.get("/community/status")
async def community_freemium_status_route():
    from bd_platform.community_freemium_layer import community_freemium_status

    return community_freemium_status()


@router.get("/community/chart")
async def community_chart_route(
    request: Request,
    asset: str = Query("BTC"),
    resolution: str = Query("1D"),
    _rl: None = Depends(_community_rate_limit),
):
    """Community chart with watermark — same engine, freemium limits (#205)."""
    from bd_platform.community_freemium_layer import fetch_community_chart

    return await fetch_community_chart(asset, resolution=resolution)


@router.get("/community/oracle")
async def community_oracle_route(
    request: Request,
    asset: str = Query("BTC"),
    _rl: None = Depends(_community_rate_limit),
):
    from bd_platform.community_freemium_layer import fetch_community_oracle

    return await fetch_community_oracle(asset)


# ── Spreadsheet Integration #174 + #176 ──────────────────────────────────────


@router.get("/sheets/BLACKDARK")
async def spreadsheet_blackdark_route(
    request: Request,
    ticker: str = Query(..., description="Asset ticker e.g. BTC"),
    metric: str = Query(..., description="price, sentiment, exit_zone_low, etc."),
    exchange: str | None = Query(None),
    _user: dict | None = Depends(optional_user_from_request),
):
    """=BLACKDARK(ticker, metric, [exchange]) for Google Sheets / Excel."""
    from bd_platform.spreadsheet_integration import evaluate_blackdark_function

    client = request.client.host if request.client else "sheets"
    return await evaluate_blackdark_function(ticker, metric, exchange, client_key=client)


@router.get("/sheets/status")
async def spreadsheet_status_route():
    from bd_platform.spreadsheet_integration import spreadsheet_integration_status

    return spreadsheet_integration_status()
