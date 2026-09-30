"""Admin billing monitoring API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from api.openapi_responses import COMMON_ERROR_RESPONSES
from privileged_access.deps import require_financial_privilege
from privileged_access.operations import ProtectedOperation
from security_auth import require_admin

router = APIRouter(prefix="/api/admin/billing", tags=["admin-billing"], responses=COMMON_ERROR_RESPONSES)


async def _require_billing_admin_metrics(
    admin: Annotated[dict, Depends(require_admin)],
    x_step_up_token: Annotated[str | None, Header(alias="X-Step-Up-Token")] = None,
    x_actor_email: Annotated[str | None, Header(alias="X-Actor-Email")] = None,
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
) -> dict:
    return await require_financial_privilege(
        ProtectedOperation.BILLING_ADMIN_METRICS,
        user=admin,
        x_step_up_token=x_step_up_token,
        x_actor_email=x_actor_email,
        x_admin_key=x_admin_key,
        x_admin_totp=x_admin_totp,
    )


async def _require_billing_admin_sweep(
    admin: Annotated[dict, Depends(require_admin)],
    x_step_up_token: Annotated[str | None, Header(alias="X-Step-Up-Token")] = None,
    x_actor_email: Annotated[str | None, Header(alias="X-Actor-Email")] = None,
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
) -> dict:
    return await require_financial_privilege(
        ProtectedOperation.BILLING_ADMIN_SWEEP,
        user=admin,
        x_step_up_token=x_step_up_token,
        x_actor_email=x_actor_email,
        x_admin_key=x_admin_key,
        x_admin_totp=x_admin_totp,
    )


@router.get("/metrics")
async def admin_billing_metrics(_admin: Annotated[dict, Depends(_require_billing_admin_metrics)]):
    from billing.admin_metrics import billing_metrics

    return await billing_metrics()


@router.get("/anomalies")
async def admin_billing_anomalies(
    _admin: Annotated[dict, Depends(_require_billing_admin_metrics)],
    limit: int = 50,
):
    from billing.admin_metrics import list_anomalies

    return {"anomalies": await list_anomalies(limit=limit)}


@router.post("/sweep")
async def admin_billing_sweep(_admin: Annotated[dict, Depends(_require_billing_admin_sweep)]):
    from billing.sweeper import run_billing_sweep

    return await run_billing_sweep()
