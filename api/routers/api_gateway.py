"""API Gateway REST router — Feature #876 (/api/v1/)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/v1", tags=["api-gateway"], responses=COMMON_ERROR_RESPONSES)


class AlertSubscribeBody(BaseModel):
    channel: str = Field(default="defi_risk_spike", description="Alert channel name")
    asset: str | None = Field(default=None, description="Optional asset filter")


def _handle(result: dict[str, Any]) -> Any:
    status = result.get("status_code", 200)
    if status == 401:
        raise HTTPException(status_code=401, detail=result.get("error", "unauthorized"))
    if status == 403:
        raise HTTPException(status_code=403, detail=result.get("error", "forbidden"))
    if status == 429:
        raise HTTPException(status_code=429, detail=result.get("error", "quota_exceeded"))
    return result.get("data", result)


@router.get("/gateway/status")
async def gateway_status():
    from bd_platform.api_gateway import api_gateway_status

    return api_gateway_status()


@router.get("/openapi.json")
async def gateway_openapi():
    from bd_platform.api_gateway import build_openapi_spec

    return build_openapi_spec()


@router.get("/metrics")
async def gateway_prometheus_metrics():
    from bd_platform.api_gateway import prometheus_metrics_text

    return Response(content=prometheus_metrics_text(), media_type="text/plain; version=0.0.4")


@router.get("/market/overview")
async def market_overview(x_api_key: str = Header(..., alias="X-API-Key")):
    from bd_platform.api_gateway import gateway_handle_request

    return _handle(gateway_handle_request(endpoint_id="market_overview", api_key=x_api_key))


@router.get("/onchain/metrics/{asset}")
async def onchain_metrics(asset: str, x_api_key: str = Header(..., alias="X-API-Key")):
    from bd_platform.api_gateway import gateway_handle_request

    return _handle(gateway_handle_request(
        endpoint_id="onchain_metrics", api_key=x_api_key, path_params={"asset": asset},
    ))


@router.get("/risk/protocol/{protocol_id}")
async def risk_protocol(protocol_id: str, x_api_key: str = Header(..., alias="X-API-Key")):
    from bd_platform.api_gateway import gateway_handle_request

    return _handle(gateway_handle_request(
        endpoint_id="risk_protocol", api_key=x_api_key, path_params={"protocol_id": protocol_id},
    ))


@router.post("/alerts/subscribe", status_code=201)
async def alerts_subscribe(
    body: AlertSubscribeBody,
    x_api_key: str = Header(..., alias="X-API-Key"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    from bd_platform.api_gateway import gateway_handle_request

    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header required")
    return _handle(gateway_handle_request(
        endpoint_id="alerts_subscribe",
        api_key=x_api_key,
        method="POST",
        body=body.model_dump(),
        idempotency_key=idempotency_key,
    ))


@router.get("/usage")
async def usage(x_api_key: str = Header(..., alias="X-API-Key")):
    from bd_platform.api_gateway import gateway_handle_request

    return _handle(gateway_handle_request(endpoint_id="usage", api_key=x_api_key))


@router.get("/sla")
async def sla_metrics(x_api_key: str = Header(..., alias="X-API-Key")):
    from bd_platform.api_gateway import gateway_handle_request

    return _handle(gateway_handle_request(endpoint_id="sla_metrics", api_key=x_api_key))


@router.get("/audit/export")
async def audit_export(
    x_api_key: str = Header(..., alias="X-API-Key"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    from bd_platform.api_gateway import authenticate_api_key, export_audit_logs, paginate_cursor

    auth = authenticate_api_key(x_api_key)
    if not auth.get("ok"):
        raise HTTPException(status_code=401, detail=auth.get("error"))
    from bd_platform.api_gateway import check_endpoint_access, gateway_handle_request

    result = gateway_handle_request(endpoint_id="audit_export", api_key=x_api_key)
    if result.get("status_code") != 200:
        return _handle(result)
    data = result.get("data") or {}
    if cursor or limit != 50:
        with_items = data.get("items", [])
        return paginate_cursor(with_items, cursor=cursor, limit=limit)
    return data


@router.get("/gateway/authz-tests")
async def authz_tests():
    from bd_platform.api_gateway import run_authz_matrix_tests

    return run_authz_matrix_tests()


@router.get("/gateway/reconciliation-tests")
async def reconciliation_tests():
    from bd_platform.api_gateway import run_reconciliation_tests

    return run_reconciliation_tests()
