"""Admin billing monitoring API."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/admin/billing", tags=["admin-billing"], responses=COMMON_ERROR_RESPONSES)


def _admin_token_ok(token: str | None) -> bool:
    expected = os.getenv("ADMIN_OPS_TOKEN", "").strip()
    if not expected:
        return os.getenv("SOFT_LAUNCH", "false").lower() in {"1", "true", "yes"}
    return bool(token) and token == expected


async def require_admin_ops(
    authorization: str | None = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
) -> None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not _admin_token_ok(token):
        raise HTTPException(status_code=403, detail="Admin ops token required")
    from financial_data_security.mfa import assert_admin_financial_mfa

    await assert_admin_financial_mfa(x_admin_totp=x_admin_totp)


@router.get("/metrics")
async def admin_billing_metrics(
    authorization: str | None = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
):
    await require_admin_ops(authorization, x_admin_totp)
    from billing.admin_metrics import billing_metrics

    return await billing_metrics()


@router.get("/anomalies")
async def admin_billing_anomalies(
    authorization: str | None = None,
    limit: int = 50,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
):
    await require_admin_ops(authorization, x_admin_totp)
    from billing.admin_metrics import list_anomalies

    return {"anomalies": await list_anomalies(limit=limit)}


@router.post("/sweep")
async def admin_billing_sweep(
    authorization: str | None = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
):
    await require_admin_ops(authorization, x_admin_totp)
    from billing.sweeper import run_billing_sweep

    return await run_billing_sweep()
