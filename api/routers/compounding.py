"""Institutional compounding API — Phases 2–8."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Request, Response

router = APIRouter(tags=["compounding"])


# ─── Phase 2: Knowledge Graph ────────────────────────────────────────────────


@router.post("/api/kg/node")
async def kg_create_node(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from knowledge_graph import create_node

    node = await create_node(
        node_type=str(body.get("node_type") or "Asset"),
        label=body.get("label"),
        properties=body.get("properties"),
        node_id=body.get("node_id"),
    )
    return {"ok": True, "node": node}


@router.post("/api/kg/edge")
async def kg_create_edge(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from knowledge_graph import create_edge

    edge = await create_edge(
        source_node_id=str(body.get("source_node_id") or ""),
        target_node_id=str(body.get("target_node_id") or ""),
        edge_type=str(body.get("edge_type") or "influenced_by"),
        properties=body.get("properties"),
        edge_id=body.get("edge_id"),
    )
    return {"ok": True, "edge": edge}


@router.get("/api/kg/query")
async def kg_query(
    symbol: str | None = Query(None),
    node_type: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    decision_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    from knowledge_graph import query_graph

    return await query_graph(symbol=symbol, node_type=node_type, days=days, decision_id=decision_id, limit=limit)


# ─── Phase 3: Signals ──────────────────────────────────────────────────────────


@router.get("/api/signals/correlate")
async def signals_correlate(symbols: str = Query("BTC,ETH")) -> dict[str, Any]:
    from signal_compounding import signal_correlate

    parts = [s.strip() for s in symbols.split(",") if s.strip()]
    return await signal_correlate(parts)


@router.post("/api/signals")
async def signals_store(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from signal_compounding import store_signal

    row = await store_signal(
        symbol=str(body.get("symbol") or "BTC"),
        signal_type=str(body.get("signal_type") or "manual"),
        value=body.get("value"),
        confidence=float(body.get("confidence") or 0.5),
        source=str(body.get("source") or "api"),
        signal_id=body.get("signal_id"),
    )
    return {"ok": True, "signal": row}


@router.get("/api/signals/{symbol}/history")
async def signals_history(symbol: str, limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    from signal_compounding import signal_history

    items = await signal_history(symbol, limit=limit)
    return {"symbol": symbol.upper(), "count": len(items), "items": items}


@router.get("/api/signals/{symbol}/diff")
async def signals_diff(symbol: str, from_ts: str = Query(..., alias="from"), to_ts: str = Query(..., alias="to")) -> dict[str, Any]:
    from signal_compounding import signal_diff

    return await signal_diff(symbol, from_ts=from_ts, to_ts=to_ts)


# ─── Phase 4: Learning ───────────────────────────────────────────────────────


@router.post("/api/learning/predictions")
async def learning_create_prediction(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from learning_compounding import create_prediction

    pred = await create_prediction(
        symbol=str(body.get("symbol") or "BTC"),
        action=str(body.get("action") or "observe"),
        confidence=float(body.get("confidence") or 0.5),
        expiry=body.get("expiry"),
        oracle_prediction_id=body.get("oracle_prediction_id"),
        context=body.get("context"),
        prediction_id=body.get("prediction_id"),
    )
    return {"ok": True, "prediction": pred}


@router.post("/api/learning/outcomes")
async def learning_record_outcome(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from learning_compounding import record_outcome

    out = await record_outcome(
        prediction_id=str(body.get("prediction_id") or ""),
        actual_result=str(body.get("actual_result") or ""),
        accuracy_score=body.get("accuracy_score"),
        counterfactual=body.get("counterfactual"),
    )
    return {"ok": True, "outcome": out}


@router.get("/api/oracle/accuracy")
async def oracle_accuracy_track_record(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    from learning_compounding import accuracy_track_record

    return await accuracy_track_record(limit=limit)


@router.get("/api/opportunities/missed")
async def opportunities_missed(limit: int = Query(40, ge=1, le=200)) -> dict[str, Any]:
    from learning_compounding import missed_opportunities

    return await missed_opportunities(limit=limit)


@router.post("/api/learning/counterfactuals")
async def learning_counterfactual(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from learning_compounding import log_counterfactual

    row = await log_counterfactual(
        prediction_id=str(body.get("prediction_id") or ""),
        scenario=str(body.get("scenario") or "alternate_action"),
        alternate_action=str(body.get("alternate_action") or ""),
        projected_outcome=str(body.get("projected_outcome") or ""),
    )
    return {"ok": True, "counterfactual": row}


# ─── Phase 5: Trust ────────────────────────────────────────────────────────────


@router.get("/api/trust/evidence-pack")
async def trust_evidence_pack() -> dict[str, Any]:
    from trust_compounding import build_evidence_pack

    return await build_evidence_pack()


@router.get("/api/trust/report")
async def trust_report(format: str = Query("json", pattern="^(json|markdown)$")) -> Response:
    from trust_compounding import build_evidence_pack, generate_trust_report_markdown

    if format == "markdown":
        md = await generate_trust_report_markdown()
        return Response(content=md, media_type="text/markdown; charset=utf-8")
    pack = await build_evidence_pack()
    import json

    return Response(content=json.dumps(pack, indent=2, default=str), media_type="application/json; charset=utf-8")


@router.get("/api/proof-arena/certificate")
async def proof_arena_certificate() -> dict[str, Any]:
    from trust_compounding import proof_arena_with_certificate

    return await proof_arena_with_certificate()


@router.get("/api/proof-arena/certificate/{certificate_id}")
async def proof_certificate_verify(certificate_id: str) -> dict[str, Any]:
    from trust_compounding import get_certificate

    cert = await get_certificate(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {"ok": True, "certificate": cert}


# ─── Phase 6: Distribution ───────────────────────────────────────────────────


@router.post("/api/analytics/event")
async def analytics_track_event(request: Request, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from distribution_compounding import track_event

    row = await track_event(
        event_type=str(body.get("event_type") or "custom"),
        payload=body.get("payload"),
        user_id=body.get("user_id"),
        session_id=body.get("session_id"),
        source=body.get("source"),
        attribution=body.get("attribution"),
    )
    return {"ok": True, "event": row}


@router.post("/api/analytics/share")
async def analytics_share(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from distribution_compounding import track_share

    row = await track_share(
        object_type=str(body.get("object_type") or "page"),
        object_id=str(body.get("object_id") or ""),
        channel=str(body.get("channel") or "unknown"),
        source=body.get("source"),
    )
    return {"ok": True, "event": row}


@router.get("/api/analytics/seo")
async def analytics_seo() -> dict[str, Any]:
    from distribution_compounding import seo_performance

    return await seo_performance()


@router.get("/api/analytics/institutional-dashboard")
async def analytics_institutional_dashboard() -> dict[str, Any]:
    from distribution_compounding import institutional_dashboard_data

    return await institutional_dashboard_data()


# ─── Phase 7: Corporate ──────────────────────────────────────────────────────


@router.get("/api/compliance/status")
async def api_compliance_status() -> dict[str, Any]:
    from corporate_compounding import compliance_status

    return await compliance_status()


@router.get("/api/corporate/data-room")
async def corporate_data_room() -> dict[str, Any]:
    from corporate_compounding import build_data_room_snapshot

    return await build_data_room_snapshot()


@router.get("/api/corporate/ip-registry")
async def corporate_ip_registry() -> dict[str, Any]:
    from corporate_compounding import list_ip_registry

    items = await list_ip_registry()
    return {"count": len(items), "items": items}


@router.get("/api/corporate/revenue-quality")
async def corporate_revenue_quality() -> dict[str, Any]:
    from corporate_compounding import revenue_quality_metrics

    return await revenue_quality_metrics()


# ─── Phase 8: Runtime verification ───────────────────────────────────────────


@router.get("/api/compounding/_verify/phase/{phase}")
async def compounding_verify_phase(phase: int) -> dict[str, Any]:
    from runtime_verification import verify_phase

    if phase < 1 or phase > 8:
        raise HTTPException(status_code=400, detail="phase must be 1-8")
    return await verify_phase(phase)


@router.get("/api/compounding/_verify")
async def compounding_verify_all() -> dict[str, Any]:
    from runtime_verification import phase_verify_all

    return await phase_verify_all()


@router.get("/api/observability/alerts")
async def observability_alerts() -> dict[str, Any]:
    from runtime_verification import alert_status

    return await alert_status()


@router.get("/api/security/wave-00")
async def security_wave_00_status() -> dict[str, Any]:
    from wave_00_hardening import wave_00_status

    return await wave_00_status()
