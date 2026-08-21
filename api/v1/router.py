"""Decision API v1 commercial router — sales-led keys + customer contract."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from api.v1.contract import (
    API_VERSION,
    CONTRACT_NAME,
    DEFAULT_CUSTOMER_SCOPES,
    DISCLAIMER,
    LEGACY_B2B_HEADERS,
    SUNSET_LEGACY_B2B,
)
from api.v1.deps import DecisionAPIRoute, require_decision_api_key, require_scope
from api.v1.keys import issue_decision_api_key, public_key_view, revoke_decision_api_key
from security_auth import require_admin

discovery = APIRouter(prefix="/api/v1", tags=["decision-api-v1"], responses=COMMON_ERROR_RESPONSES)
issuance = APIRouter(
    prefix="/api/v1",
    tags=["decision-api-v1-issuance"],
    responses=COMMON_ERROR_RESPONSES,
    route_class=DecisionAPIRoute,
)
commercial = APIRouter(
    prefix="/api/v1",
    tags=["decision-api-v1"],
    responses=COMMON_ERROR_RESPONSES,
    route_class=DecisionAPIRoute,
)


class IssueKeyBody(BaseModel):
    org_id: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=2, max_length=80)
    environment: str = Field(default="live")
    plan: str = Field(default="institutional")
    scopes: list[str] = Field(default_factory=lambda: list(DEFAULT_CUSTOMER_SCOPES))
    rpm_limit: int | None = Field(default=None, ge=1, le=10_000)
    rpd_limit: int | None = Field(default=None, ge=1, le=5_000_000)


class RegisterWebhookBody(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048)
    events: list[str] | None = None


class TestWebhookBody(BaseModel):
    webhook_id: str | None = Field(default=None, max_length=64)


@discovery.get("")
@discovery.get("/")
async def decision_api_discover() -> dict[str, Any]:
    return {
        "contract": CONTRACT_NAME,
        "api_version": API_VERSION,
        "auth": {
            "header": "X-API-Key or Authorization: Bearer bd_live_… / bd_test_…",
            "issuance": "sales-led POST /api/v1/keys (admin). Not self-serve.",
        },
        "endpoints": {
            "oracle": "GET /api/v1/oracle/{symbol}",
            "certificate": "POST /api/v1/oracle/{symbol}/certificate",
            "accuracy": "GET /api/v1/accuracy",
            "audit_chain": "GET /api/v1/accuracy/audit-chain",
            "feed": "GET /api/v1/feed",
            "feed_ws": "WS /api/v1/feed/ws (Authorization header — query keys rejected)",
            "me": "GET /api/v1/me",
            "audit": "GET /api/v1/audit",
            "usage": "GET /api/v1/usage",
            "webhooks": "POST/GET /api/v1/webhooks",
            "webhook_test": "POST /api/v1/webhooks/test",
            "openapi": "GET /api/v1/openapi.json",
        },
        "not_included": [
            "admin",
            "live_execution",
            "exchange_key_vault",
            "ml_training",
            "prometheus_metrics",
        ],
        "legacy_b2b": {
            "path": "/api/b2b/feed",
            "deprecated": True,
            "sunset": SUNSET_LEGACY_B2B,
            "successor": "/api/v1/feed",
        },
        "disclaimer": DISCLAIMER,
    }


@discovery.get("/changelog")
async def decision_api_changelog() -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "deprecation_policy": (
            "Breaking changes require a new URL version (/api/v2). "
            "Deprecated v1 paths receive Deprecation + Sunset headers with ≥12 months notice."
        ),
        "legacy_house_key_feed": {
            "path": "/api/b2b/feed",
            "sunset": SUNSET_LEGACY_B2B,
            "successor": "/api/v1/feed",
        },
        "headers": LEGACY_B2B_HEADERS,
    }


@discovery.get("/openapi.json")
async def decision_api_openapi(request: Request) -> dict[str, Any]:
    schema = request.app.openapi()
    paths = schema.get("paths") or {}
    allow = {p: spec for p, spec in paths.items() if p.startswith("/api/v1") and not p.startswith("/api/v1/keys")}
    return {
        "openapi": schema.get("openapi") or "3.1.0",
        "info": {
            "title": "BLACKDARK Decision API",
            "version": API_VERSION,
            "description": DISCLAIMER,
        },
        "paths": allow,
        "x-blackdark": {
            "contract": CONTRACT_NAME,
            "auth": "X-API-Key",
            "not_included": ["keys_issuance", "admin", "execution", "vault"],
        },
    }


@issuance.post("/keys")
async def issue_key(body: IssueKeyBody, admin: dict = Depends(require_admin)) -> dict[str, Any]:
    try:
        return await issue_decision_api_key(
            org_id=body.org_id,
            name=body.name,
            created_by=str(admin.get("email") or "admin"),
            environment=body.environment,
            plan=body.plan,
            scopes=body.scopes,
            rpm_limit=body.rpm_limit,
            rpd_limit=body.rpd_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_request", "message": str(exc)}) from exc


@issuance.get("/keys")
async def list_keys(
    org_id: str | None = Query(default=None),
    _admin: dict = Depends(require_admin),
) -> dict[str, Any]:
    from database import list_decision_api_keys

    rows = await list_decision_api_keys(org_id=org_id)
    return {"keys": [public_key_view(r) for r in rows]}


@issuance.post("/keys/{public_id}/revoke")
@issuance.delete("/keys/{public_id}")
async def revoke_key(public_id: str, admin: dict = Depends(require_admin)) -> dict[str, Any]:
    row = await revoke_decision_api_key(public_id, revoked_by=str(admin.get("email") or "admin"))
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "API key not found"})
    return row


@commercial.get("/me")
async def decision_api_me(principal: dict = Depends(require_decision_api_key)) -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "key": public_key_view(principal),
        "disclaimer": DISCLAIMER,
    }


@commercial.get("/oracle/{symbol}")
async def v1_oracle(
    symbol: str,
    principal: dict = Depends(require_scope("oracle:read")),
) -> dict[str, Any]:
    from api.v1.oracle_adapter import build_v1_oracle_decision
    from api.v1.webhooks import schedule_webhook_delivery

    decision = await build_v1_oracle_decision(symbol, principal=principal)
    schedule_webhook_delivery(
        principal,
        "oracle.decision",
        {
            "asset": decision.get("asset"),
            "verdict": decision.get("verdict"),
            "opportunity_score": decision.get("opportunity_score"),
        },
    )
    return decision


@commercial.post("/oracle/{symbol}/certificate")
async def v1_oracle_certificate(
    symbol: str,
    principal: dict = Depends(require_scope("oracle:read")),
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    from api.v1.oracle_adapter import build_v1_oracle_decision
    from decision_certificate import build_decision_certificate

    decision = await build_v1_oracle_decision(symbol, principal=principal)
    extra = dict(body or {})
    extra.pop("tier", None)
    merged = {**decision, **extra, "tier": "whale"}
    return {
        "api_version": API_VERSION,
        "asset": decision.get("asset"),
        "decision_certificate": build_decision_certificate(merged),
        "disclaimer": DISCLAIMER,
    }


@commercial.get("/accuracy")
async def v1_accuracy(
    recent_limit: int = Query(default=20, ge=1, le=100),
    _principal: dict = Depends(require_scope("accuracy:read")),
) -> dict[str, Any]:
    from api.v1.oracle_adapter import build_v1_accuracy

    return await build_v1_accuracy(recent_limit=recent_limit)


@commercial.get("/accuracy/audit-chain")
async def v1_audit_chain(
    limit: int = Query(default=20, ge=1, le=100),
    _principal: dict = Depends(require_scope("accuracy:read")),
) -> dict[str, Any]:
    from oracle_audit_chain import chain_summary, verify_chain

    return {
        "api_version": API_VERSION,
        "chain": chain_summary(limit=limit),
        "verify": verify_chain(),
        "disclaimer": DISCLAIMER,
    }


@commercial.get("/feed")
async def v1_feed(
    limit: int | None = Query(default=None, ge=1, le=250),
    principal: dict = Depends(require_scope("feed:read")),
) -> dict[str, Any]:
    from api.v1.oracle_adapter import build_v1_feed

    return await build_v1_feed(principal=principal, limit=limit)


@commercial.get("/audit")
async def v1_audit(
    limit: int = Query(default=50, ge=1, le=500),
    mine: bool = Query(default=False),
    principal: dict = Depends(require_scope("audit:read")),
) -> dict[str, Any]:
    from database import fetch_decision_api_audit

    org_id = str(principal.get("org_id") or "")
    key_filter = str(principal.get("public_id") or "") if mine else None
    rows = await fetch_decision_api_audit(org_id=org_id, key_public_id=key_filter, limit=limit)
    return {
        "api_version": API_VERSION,
        "org_id": org_id,
        "mine": mine,
        "events": rows,
        "disclaimer": DISCLAIMER,
    }


@commercial.get("/usage")
async def v1_usage(
    days: int = Query(default=31, ge=1, le=90),
    principal: dict = Depends(require_decision_api_key),
) -> dict[str, Any]:
    from database import fetch_decision_api_usage_history

    key_id = str(principal.get("public_id") or "")
    history = await fetch_decision_api_usage_history(key_id, days=days)
    return {
        "api_version": API_VERSION,
        "key_id": key_id,
        "org_id": principal.get("org_id"),
        "days": days,
        "history": history,
        "disclaimer": DISCLAIMER,
    }


@commercial.post("/webhooks")
async def v1_register_webhook(
    body: RegisterWebhookBody,
    principal: dict = Depends(require_scope("webhooks:write")),
) -> dict[str, Any]:
    from api.v1.webhooks import register_webhook

    try:
        hook = await register_webhook(principal=principal, url=body.url, events=body.events)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc), "message": str(exc)}) from exc
    return {"api_version": API_VERSION, "webhook": hook, "disclaimer": DISCLAIMER}


@commercial.get("/webhooks")
async def v1_list_webhooks(
    principal: dict = Depends(require_scope("webhooks:write")),
) -> dict[str, Any]:
    from api.v1.webhooks import public_webhook_view
    from database import list_decision_api_webhooks

    rows = await list_decision_api_webhooks(org_id=str(principal.get("org_id") or ""))
    return {
        "api_version": API_VERSION,
        "webhooks": [public_webhook_view(row) for row in rows],
        "disclaimer": DISCLAIMER,
    }


@commercial.delete("/webhooks/{webhook_id}")
async def v1_disable_webhook(
    webhook_id: str,
    principal: dict = Depends(require_scope("webhooks:write")),
) -> dict[str, Any]:
    from database import disable_decision_api_webhook

    ok = await disable_decision_api_webhook(webhook_id, org_id=str(principal.get("org_id") or ""))
    if not ok:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Webhook not found"})
    return {"api_version": API_VERSION, "id": webhook_id, "status": "disabled"}


@commercial.post("/webhooks/test")
async def v1_test_webhook(
    body: TestWebhookBody,
    principal: dict = Depends(require_scope("webhooks:write")),
) -> dict[str, Any]:
    from api.v1.webhooks import deliver_webhook_event

    try:
        results = await deliver_webhook_event(
            principal=principal,
            event_type="ping",
            payload={"ok": True},
            webhook_id=body.webhook_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc), "message": str(exc)}) from exc
    return {"api_version": API_VERSION, "deliveries": results, "disclaimer": DISCLAIMER}


async def _ws_reject(websocket: WebSocket, reason: str, *, principal: dict | None = None) -> None:
    from api.v1.audit import persist_decision_api_ws_audit

    await persist_decision_api_ws_audit(
        principal=principal,
        status=401,
        error_code=reason,
        request_id=uuid.uuid4().hex,
    )
    await websocket.close(code=1008, reason=reason)


@commercial.websocket("/feed/ws")
async def v1_feed_ws(websocket: WebSocket):
    """Server-to-server WebSocket. Query-string API keys are rejected."""
    if (websocket.query_params.get("api_key") or "").strip():
        await _ws_reject(websocket, "query_api_key_forbidden")
        return
    presented = (websocket.headers.get("x-api-key") or websocket.headers.get("authorization") or "").strip()
    if not presented:
        await _ws_reject(websocket, "api_key_required")
        return
    from api.v1.audit import persist_decision_api_ws_audit
    from api.v1.keys import authenticate_decision_api_key, principal_has_scope
    from api.v1.oracle_adapter import build_v1_feed

    try:
        principal = await authenticate_decision_api_key(presented)
    except PermissionError:
        await _ws_reject(websocket, "invalid_api_key")
        return
    if not principal_has_scope(principal, "feed:ws"):
        await _ws_reject(websocket, "insufficient_scope", principal=principal)
        return
    await persist_decision_api_ws_audit(
        principal=principal,
        status=101,
        request_id=uuid.uuid4().hex,
    )
    await websocket.accept()
    try:
        snapshot = await build_v1_feed(principal=principal, limit=25)
        await websocket.send_json(
            {
                "type": "connected",
                "api_version": API_VERSION,
                "channel": "decision-api-v1",
                "org_id": principal.get("org_id"),
                "environment": principal.get("environment"),
            }
        )
        await websocket.send_json({"type": "snapshot", **snapshot})
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() == "ping":
                await websocket.send_json({"type": "pong", "api_version": API_VERSION})
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close(code=1011, reason="feed_error")
        except Exception:
            return


def legacy_b2b_json(payload: dict[str, Any], *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(payload, status_code=status_code, headers=dict(LEGACY_B2B_HEADERS))
