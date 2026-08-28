"""Phase 1 — Immutable audit log & decision registry API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Request, Response

router = APIRouter(tags=["audit"])


@router.get("/api/audit/user-activity")
async def get_user_activity(
    request: Request,
    tenant_id: str | None = Query(None),
    target_user_id: int | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    from security_auth import optional_user_from_request
    from user_activity_audit_trail import query_user_activity

    user = await optional_user_from_request(
        authorization=request.headers.get("Authorization"),
        bd_token=request.cookies.get("bd_token"),
    )
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return query_user_activity(
        viewer_email=str(user.get("email") or ""),
        viewer_user_id=int(user["id"]) if user.get("id") else None,
        tenant_id=tenant_id or request.headers.get("x-tenant-id"),
        target_user_id=target_user_id,
        action=action,
        limit=limit,
    )


@router.get("/api/audit/user-activity/status")
async def user_activity_status_endpoint() -> dict[str, Any]:
    from user_activity_audit_trail import user_activity_status

    return user_activity_status()


@router.get("/api/audit/user-activity/gate")
async def user_activity_gate_endpoint() -> dict[str, Any]:
    from user_activity_audit_trail import check_user_activity_gate

    return check_user_activity_gate()


@router.post("/api/audit/log")
async def post_audit_log(
    request: Request,
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    from audit_registry import hash_payload, record_audit_log, resolve_actor_from_request

    actor = str(body.get("actor") or await resolve_actor_from_request(request))
    action = str(body.get("action") or "manual.log")
    payload = body.get("payload") or body.get("data") or {}
    outcome = str(body.get("outcome") or "logged")
    row = await record_audit_log(
        actor=actor,
        action=action,
        payload_hash=hash_payload(payload),
        outcome=outcome,
        request_method=request.method,
        request_path=request.url.path,
        metadata={"source": "api.audit.log", "payload": payload},
    )
    return {"ok": True, "audit": row}


@router.get("/api/audit/export")
async def export_audit(
    format: str = Query("json", pattern="^(json|csv)$"),
    start: str | None = Query(None),
    end: str | None = Query(None),
    actor: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(1000, ge=1, le=10_000),
) -> Response:
    from audit_registry import export_audit_logs_csv, fetch_audit_logs

    rows = await fetch_audit_logs(
        start=start,
        end=end,
        actor=actor,
        action=action,
        limit=limit,
    )
    if format == "csv":
        content = export_audit_logs_csv(rows)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="audit_logs.csv"'},
        )
    import json

    return Response(
        content=json.dumps(
            {"count": len(rows), "items": rows},
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="audit_logs.json"'},
    )


@router.post("/api/decisions")
async def create_decision_api(
    request: Request,
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    from audit_registry import create_decision, resolve_actor_from_request

    context = body.get("context") or {}
    prediction = body.get("prediction") or {}
    confidence = float(body.get("confidence") or 0.0)
    outcome = str(body.get("outcome") or "pending")
    actor = await resolve_actor_from_request(request)
    decision = await create_decision(
        context=context,
        prediction=prediction,
        confidence=confidence,
        actor=actor,
        decision_id=body.get("decision_id"),
        outcome=outcome,
    )
    return {"ok": True, "decision": decision}


@router.get("/api/decisions/search")
async def search_decisions_api(
    start: str | None = Query(None, description="ISO timestamp lower bound"),
    end: str | None = Query(None, description="ISO timestamp upper bound"),
    outcome: str | None = Query(None),
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    from audit_registry import search_decisions

    items = await search_decisions(
        start=start,
        end=end,
        outcome=outcome,
        symbol=symbol,
        limit=limit,
    )
    return {"count": len(items), "items": items}


@router.get("/api/decisions/{decision_id}")
async def get_decision_api(
    decision_id: str,
    version: int | None = Query(None, ge=1),
) -> dict[str, Any]:
    from audit_registry import create_decision_version, get_decision

    row = await get_decision(decision_id, version=version)
    if not row:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"ok": True, "decision": row}


@router.patch("/api/decisions/{decision_id}")
async def patch_decision_api(
    decision_id: str,
    request: Request,
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """Create a new immutable version when outcome/context/prediction changes."""
    from audit_registry import create_decision_version, get_decision, resolve_actor_from_request

    if not await get_decision(decision_id):
        raise HTTPException(status_code=404, detail="Decision not found")

    actor = await resolve_actor_from_request(request)
    updated = await create_decision_version(
        decision_id=decision_id,
        context=body.get("context"),
        prediction=body.get("prediction"),
        confidence=body.get("confidence"),
        outcome=body.get("outcome"),
        actor=actor,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"ok": True, "decision": updated}
