"""Oracle Sealed Prediction Markets API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from dashboard import require_authenticated
from security_auth import optional_user_from_request

router = APIRouter(tags=["sealed-markets"], responses=COMMON_ERROR_RESPONSES)


class PlaceBetBody(BaseModel):
    side: str = Field(..., description="yes = decision will be correct on ledger; no = miss")
    stake_usdt: float = Field(..., gt=0)
    funding: str = Field(default="internal", pattern="^(internal|usdt)$")


@router.get("/api/sealed-markets/public")
async def sealed_markets_public(limit: int = Query(40, ge=1, le=100)):
    from sealed_prediction_market import public_markets_payload

    return await public_markets_payload(limit=limit)


@router.get("/api/sealed-markets/prediction/{prediction_id}")
async def sealed_market_for_prediction(prediction_id: int):
    from sealed_prediction_market import market_detail

    detail = await market_detail(prediction_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Sealed market not found")
    return detail


@router.post("/api/sealed-markets/prediction/{prediction_id}/bets")
async def sealed_market_place_bet(
    prediction_id: int,
    body: PlaceBetBody,
    user: dict = Depends(require_authenticated),
):
    from sealed_prediction_market import place_market_bet

    try:
        return await place_market_bet(
            user_id=int(user["id"]),
            prediction_id=prediction_id,
            side=body.side,
            stake_usdt=body.stake_usdt,
            funding=body.funding,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/sealed-markets/balance")
async def sealed_market_balance(user: dict = Depends(require_authenticated)):
    from sealed_market_store import get_user_balance

    return {"balance_usdt": await get_user_balance(int(user["id"]))}
