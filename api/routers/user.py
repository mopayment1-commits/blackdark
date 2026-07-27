"""User settings API router (keys, risk)."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends

import config
from security_auth import require_whale
from security_models import UserApiKeyBody

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/exchange-keys")
async def store_exchange_keys(body: UserApiKeyBody, user: dict = Depends(require_whale)):
    from user_keys_service import store_user_exchange_keys

    return await store_user_exchange_keys(
        int(user["id"]), body.exchange, body.api_key, body.api_secret, label=body.label
    )


@router.get("/exchange-keys")
async def list_exchange_keys(user: dict = Depends(require_whale)):
    from user_keys_service import list_user_exchange_keys

    return {"keys": await list_user_exchange_keys(int(user["id"]))}


@router.delete("/exchange-keys/{exchange}")
async def delete_exchange_keys(exchange: str, user: dict = Depends(require_whale)):
    from user_keys_service import remove_user_exchange_keys

    return await remove_user_exchange_keys(int(user["id"]), exchange)


@router.get("/risk-settings")
async def get_user_risk_settings(user: dict = Depends(require_whale)):
    from database import fetch_user_risk_settings

    return await fetch_user_risk_settings(int(user["id"]))


@router.post("/risk-settings")
async def update_user_risk_settings(data: dict = Body(...), user: dict = Depends(require_whale)):
    from database import upsert_user_risk_settings

    return await upsert_user_risk_settings(
        int(user["id"]),
        max_slippage_bps=float(data["max_slippage_bps"]) if data.get("max_slippage_bps") is not None else None,
        max_risk_score=float(data["max_risk_score"]) if data.get("max_risk_score") is not None else None,
        max_daily_loss_usd=float(data["max_daily_loss_usd"]) if data.get("max_daily_loss_usd") is not None else None,
    )
