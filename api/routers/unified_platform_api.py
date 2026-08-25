"""Unified API Platform v1 router — Features #162, #174, #176."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import optional_user_from_request

router = APIRouter(prefix="/api/v1/platform", tags=["unified-api"], responses=COMMON_ERROR_RESPONSES)


def _rate_limit(request: Request) -> None:
    from bd_platform.unified_api_platform import check_api_rate_limit

    client = request.client.host if request.client else "unknown"
    blocked = check_api_rate_limit(f"api:{client}")
    if blocked:
        raise HTTPException(status_code=429, detail=blocked)


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
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_sentiment

    return await fetch_sentiment(asset)


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
    _rl: None = Depends(_rate_limit),
):
    from bd_platform.unified_api_platform import fetch_contract_safety

    return await fetch_contract_safety(address, chain=chain)


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
