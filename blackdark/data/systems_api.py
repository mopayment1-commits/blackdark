"""API routes for Wave 01 twelve-system sprint (systems 1–12)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from blackdark.data.api import WAVE_01_VERSION, _ensure_ready, _parse_dt
from blackdark.data.db import get_session
from blackdark.data.provenance import hash_payload
from blackdark.data.repository import (
    get_evidence,
    get_prediction,
    insert_decision,
    insert_evidence,
    insert_failure_miss,
    insert_market_event,
    insert_outcome_evaluation,
    insert_prediction,
    insert_signal,
    query_decisions,
    query_failure_misses,
    query_ingestion_errors,
    query_ingestion_runs,
    query_outcomes,
    query_signals,
)
from blackdark.data.response_metadata import dataset_response
from security_auth import require_admin

logger = logging.getLogger("BLACKDARK.DataEngine.SystemsAPI")

systems_router = APIRouter(tags=["data-engine-systems"])


class MarketEventCreate(BaseModel):
    event_type: str
    severity: str
    symbol: str | None = None
    start_time: str
    end_time: str | None = None
    description: str | None = None
    price_change_pct: float | None = None
    volume_spike_multiplier: float | None = None
    source_links: list[str] = Field(default_factory=list)
    detected_by: str = "api"
    confirmed: bool = False


class SignalCreate(BaseModel):
    symbol: str
    signal_type: str
    direction: str = Field(pattern="^(buy|sell|neutral)$")
    confidence: float | None = None
    features_hash: str | None = None
    model_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PredictionCreate(BaseModel):
    symbol: str
    direction: str
    target_price: float | None = None
    model_version: str | None = None
    signal_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    unlock_at: str | None = None


class DecisionCreate(BaseModel):
    prediction_id: str
    decision_action: str = Field(pattern="^(act|wait)$")
    symbol: str
    rationale: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutcomeEvaluate(BaseModel):
    prediction_id: str
    outcome: str = Field(pattern="^(hit|miss|pending)$")
    actual_price: float | None = None
    predicted_direction: str | None = None
    pnl_pct: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceCreate(BaseModel):
    record_type: str
    payload: dict[str, Any]
    source_table: str | None = None
    source_record_id: str | None = None


class FailureMissCreate(BaseModel):
    failure_type: str = Field(pattern="^(miss|false_positive|ingestion_error)$")
    prediction_id: str | None = None
    signal_id: str | None = None
    symbol: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@systems_router.get("/api/v1/data/ingestion-runs")
async def list_ingestion_runs(
    source: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_ingestion_runs(session, source_slug=source, limit=limit)
    return dataset_response(count=len(rows), data=rows, dataset="ingestion_runs")


@systems_router.get("/api/v1/data/ingestion-errors")
async def list_ingestion_errors(
    source: str | None = None,
    resolved: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_ingestion_errors(session, source_slug=source, resolved=resolved, limit=limit)
    return dataset_response(count=len(rows), data=rows, dataset="ingestion_errors")


@systems_router.post("/api/v1/data/events", status_code=201)
async def create_market_event(
    body: MarketEventCreate,
    _: None = Depends(require_admin),
    __: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        event_id = await insert_market_event(
            session,
            row={
                **body.model_dump(),
                "start_time": _parse_dt(body.start_time),
                "end_time": _parse_dt(body.end_time) if body.end_time else None,
            },
        )
    return {"ok": True, "id": event_id, "event_type": body.event_type}


@systems_router.post("/api/v1/data/signals", status_code=201)
async def register_signal(body: SignalCreate, _: None = Depends(_ensure_ready)):
    signal_id = f"sig_{uuid4().hex[:16]}"
    features_hash = body.features_hash or hash_payload(json.dumps(body.metadata, sort_keys=True))
    async with get_session() as session:
        row_id = await insert_signal(
            session,
            signal_id=signal_id,
            symbol=body.symbol,
            signal_type=body.signal_type,
            direction=body.direction,
            confidence=body.confidence,
            features_hash=features_hash,
            model_version=body.model_version,
            provenance_hash=features_hash,
            metadata=body.metadata,
        )
    return {"ok": True, "signal_id": signal_id, "id": row_id, "direction": body.direction}


@systems_router.get("/api/v1/data/signals")
async def list_signals(
    symbol: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_signals(session, symbol=symbol, limit=limit)
    return dataset_response(count=len(rows), data=rows, dataset="signals")


@systems_router.post("/api/v1/data/predictions", status_code=201)
async def seal_prediction(body: PredictionCreate, _: None = Depends(_ensure_ready)):
    prediction_id = f"pred_{uuid4().hex[:16]}"
    payload = {
        "symbol": body.symbol.upper(),
        "direction": body.direction,
        "target_price": body.target_price,
        "model_version": body.model_version,
        **body.payload,
    }
    sealed_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    async with get_session() as session:
        row_id = await insert_prediction(
            session,
            prediction_id=prediction_id,
            symbol=body.symbol,
            sealed_payload_hash=sealed_hash,
            signal_id=body.signal_id,
            direction=body.direction,
            target_price=body.target_price,
            model_version=body.model_version,
            unlock_at=_parse_dt(body.unlock_at) if body.unlock_at else None,
            metadata=payload,
        )
    return {
        "ok": True,
        "prediction_id": prediction_id,
        "id": row_id,
        "sealed_payload_hash": sealed_hash,
    }


@systems_router.get("/api/v1/data/predictions/{prediction_id}")
async def get_prediction_record(prediction_id: str, _: None = Depends(_ensure_ready)):
    async with get_session() as session:
        row = await get_prediction(session, prediction_id)
    if not row:
        raise HTTPException(status_code=404, detail="prediction not found")
    return row


@systems_router.post("/api/v1/data/decisions", status_code=201)
async def record_decision(body: DecisionCreate, _: None = Depends(_ensure_ready)):
    decision_id = f"dec_{uuid4().hex[:16]}"
    evidence_hash = hash_payload(
        json.dumps(
            {
                "prediction_id": body.prediction_id,
                "action": body.decision_action,
                "symbol": body.symbol,
            },
            sort_keys=True,
        )
    )
    async with get_session() as session:
        row_id = await insert_decision(
            session,
            decision_id=decision_id,
            prediction_id=body.prediction_id,
            decision_action=body.decision_action,
            symbol=body.symbol,
            rationale=body.rationale,
            evidence_hash=evidence_hash,
            metadata=body.metadata,
        )
    return {"ok": True, "decision_id": decision_id, "id": row_id, "decision_action": body.decision_action}


@systems_router.get("/api/v1/data/decisions")
async def list_decisions(
    prediction_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_decisions(session, prediction_id=prediction_id, limit=limit)
    return dataset_response(count=len(rows), data=rows, dataset="decisions")


@systems_router.post("/api/v1/data/outcomes/evaluate", status_code=201)
async def evaluate_outcome(body: OutcomeEvaluate, _: None = Depends(_ensure_ready)):
    async with get_session() as session:
        row_id = await insert_outcome_evaluation(
            session,
            prediction_id=body.prediction_id,
            outcome=body.outcome,
            actual_price=body.actual_price,
            predicted_direction=body.predicted_direction,
            pnl_pct=body.pnl_pct,
            metadata=body.metadata,
        )
    return {"ok": True, "id": row_id, "outcome": body.outcome}


@systems_router.get("/api/v1/data/outcomes")
async def list_outcomes(
    prediction_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_outcomes(session, prediction_id=prediction_id, limit=limit)
    return dataset_response(count=len(rows), data=rows, dataset="outcomes")


@systems_router.post("/api/v1/data/evidence", status_code=201)
async def store_evidence(body: EvidenceCreate, _: None = Depends(_ensure_ready)):
    evidence_id = f"ev_{uuid4().hex[:16]}"
    payload_hash = hash_payload(json.dumps(body.payload, sort_keys=True))
    async with get_session() as session:
        row_id = await insert_evidence(
            session,
            evidence_id=evidence_id,
            record_type=body.record_type,
            payload=body.payload,
            payload_hash=payload_hash,
            source_table=body.source_table,
            source_record_id=body.source_record_id,
        )
    return {"ok": True, "evidence_id": evidence_id, "id": row_id, "payload_hash": payload_hash}


@systems_router.get("/api/v1/data/evidence/{evidence_id}")
async def get_evidence_record(evidence_id: str, _: None = Depends(_ensure_ready)):
    async with get_session() as session:
        row = await get_evidence(session, evidence_id)
    if not row:
        raise HTTPException(status_code=404, detail="evidence not found")
    return row


@systems_router.post("/api/v1/data/failures/misses", status_code=201)
async def record_failure_miss(body: FailureMissCreate, _: None = Depends(_ensure_ready)):
    async with get_session() as session:
        row_id = await insert_failure_miss(
            session,
            failure_type=body.failure_type,
            prediction_id=body.prediction_id,
            signal_id=body.signal_id,
            symbol=body.symbol,
            error_message=body.error_message,
            metadata=body.metadata,
        )
    return {"ok": True, "id": row_id, "failure_type": body.failure_type}


@systems_router.get("/api/v1/data/failures/misses")
async def list_failure_misses(
    failure_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_failure_misses(session, failure_type=failure_type, limit=limit)
    return dataset_response(count=len(rows), data=rows, dataset="failure_misses")


@systems_router.get("/api/v1/data/systems")
async def systems_index(_: None = Depends(_ensure_ready)):
    return {
        "wave": 1,
        "version": WAVE_01_VERSION,
        "systems": [
            {"id": 1, "name": "live_shadow_collection", "status": "active"},
            {"id": 2, "name": "historical_backfill", "status": "active", "cli": "python -m blackdark.data backfill"},
            {"id": 3, "name": "data_provenance", "endpoint": "/api/v1/data/provenance/{id}"},
            {"id": 4, "name": "ingestion_run_versioning", "endpoint": "/api/v1/data/ingestion-runs"},
            {"id": 5, "name": "market_event_library", "endpoints": ["/api/v1/data/events"]},
            {"id": 6, "name": "failure_registry", "endpoint": "/api/v1/data/ingestion-errors"},
            {"id": 7, "name": "signal_registry", "endpoint": "/api/v1/data/signals"},
            {"id": 8, "name": "prediction_ledger", "endpoint": "/api/v1/data/predictions"},
            {"id": 9, "name": "decision_ledger", "endpoint": "/api/v1/data/decisions"},
            {"id": 10, "name": "outcome_evaluator", "endpoint": "/api/v1/data/outcomes"},
            {"id": 11, "name": "evidence_store", "endpoint": "/api/v1/data/evidence"},
            {"id": 12, "name": "failure_misses", "endpoint": "/api/v1/data/failures/misses"},
        ],
    }
