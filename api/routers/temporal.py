"""Production temporal spine API routes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from blackdark.data.api import _ensure_ready
from blackdark.data.db import get_session
from blackdark.data.response_metadata import dataset_response
from blackdark.temporal.contamination_registry import ContaminationPurpose
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.persistence.postgres import PostgresContaminationRegistry
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine
from blackdark.temporal.truth import parse_temporal_instant
from blackdark.temporal.walk_forward import (
    WalkForwardControl,
    WalkForwardFreezeContext,
    generate_walk_forward_windows,
    run_walk_forward_evaluation,
)
from security_auth import require_admin

logger = logging.getLogger("BLACKDARK.Temporal.API")

router = APIRouter(prefix="/api/temporal", tags=["temporal-spine"])


class TemporalIngestRequest(BaseModel):
    entity_key: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    observation: dict[str, Any]
    provenance: dict[str, Any]
    simulated_time: str
    prediction: Any
    confidence: float = 0.5
    abstention_state: str = "act"
    subject_identity: str
    input_identity: str
    model_version: str = "model-v1"
    rule_config_version: str = "rule-v1"
    dataset_version: str = "ds-1"
    code_version: str = "code-v1"
    input_snapshot_hash: str = "hash-0"
    uses_simulated_time: bool = True
    live_forward_passage_confirmed: bool = False


class WalkForwardRequest(BaseModel):
    dataset_id: str
    samples: list[dict[str, Any]]
    series_start: str
    series_end: str
    train_duration_seconds: int = 3600
    eval_duration_seconds: int = 1800
    step_seconds: int = 1800
    purge_gap_seconds: int = 0
    embargo_gap_seconds: int = 0
    model_version: str = "model-v1"
    config_version: str = "cfg-v1"
    dataset_version: str = "ds-1"


class ContaminationExposureRequest(BaseModel):
    dataset_id: str
    window_start: str
    window_end: str
    purpose: str
    model_version: str | None = None
    config_version: str | None = None
    dataset_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/spine/ingest", status_code=201)
async def ingest_temporal_spine(
    body: TemporalIngestRequest,
    _: None = Depends(require_admin),
    __: None = Depends(_ensure_ready),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload={
                    "entity_key": body.entity_key,
                    "event_type": body.event_type,
                    "payload": body.payload,
                    "observation": body.observation,
                    "provenance": body.provenance,
                },
                simulated_time=parse_temporal_instant(body.simulated_time),
                prediction=body.prediction,
                confidence=body.confidence,
                abstention_state=body.abstention_state,
                subject_identity=body.subject_identity,
                input_identity=body.input_identity,
                model_version=body.model_version,
                rule_config_version=body.rule_config_version,
                dataset_version=body.dataset_version,
                code_version=body.code_version,
                input_snapshot_hash=body.input_snapshot_hash,
                idempotency_key=idempotency_key,
                uses_simulated_time=body.uses_simulated_time,
                live_forward_passage_confirmed=body.live_forward_passage_confirmed,
            ),
        )
    if result.status != "completed":
        raise HTTPException(status_code=422, detail=result.to_metadata())
    return result.to_metadata()


@router.post("/walk-forward/evaluate")
async def evaluate_walk_forward(
    body: WalkForwardRequest,
    _: None = Depends(require_admin),
    __: None = Depends(_ensure_ready),
):
    windows = generate_walk_forward_windows(
        dataset_id=body.dataset_id,
        series_start=body.series_start,
        series_end=body.series_end,
        train_duration=timedelta(seconds=body.train_duration_seconds),
        eval_duration=timedelta(seconds=body.eval_duration_seconds),
        step=timedelta(seconds=body.step_seconds),
        purge_gap_seconds=body.purge_gap_seconds,
        embargo_gap_seconds=body.embargo_gap_seconds,
    )
    async with get_session() as session:
        registry = PostgresContaminationRegistry(session)
        await registry.hydrate()

        def _evaluate(train, eval_set, freeze):
            return {
                "train_count": len(train),
                "eval_count": len(eval_set),
                "model_version": freeze.model_version,
            }

        result = run_walk_forward_evaluation(
            dataset_id=body.dataset_id,
            samples=body.samples,
            windows=windows,
            freeze=WalkForwardFreezeContext(
                model_version=body.model_version,
                dataset_version=body.dataset_version,
                config_version=body.config_version,
                controls=(
                    WalkForwardControl.PURGE,
                    WalkForwardControl.EMBARGO,
                    WalkForwardControl.NO_FUTURE_FEATURE_LEAKAGE,
                    WalkForwardControl.IMMUTABLE_EVALUATION_WINDOWS,
                    WalkForwardControl.MODEL_VERSION_FREEZE,
                    WalkForwardControl.DATASET_VERSION_FREEZE,
                    WalkForwardControl.CONFIGURATION_FREEZE,
                ),
            ),
            contamination_registry=registry,
            evaluate_fold=_evaluate,
        )
        for fold in result.folds:
            entry = registry.record_exposure(
                dataset_id=body.dataset_id,
                window_start=fold.window.eval_start,
                window_end=fold.window.eval_end,
                purpose=ContaminationPurpose.EVALUATION,
                model_version=body.model_version,
                config_version=body.config_version,
                dataset_version=body.dataset_version,
                metadata=fold.to_metadata(),
            )
            await registry.persist_entry(entry)
    return result.to_metadata()


@router.post("/contamination/exposure", status_code=201)
async def record_contamination_exposure(
    body: ContaminationExposureRequest,
    _: None = Depends(require_admin),
    __: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        registry = PostgresContaminationRegistry(session)
        await registry.hydrate()
        entry = registry.record_exposure(
            dataset_id=body.dataset_id,
            window_start=body.window_start,
            window_end=body.window_end,
            purpose=ContaminationPurpose(body.purpose),
            model_version=body.model_version,
            config_version=body.config_version,
            dataset_version=body.dataset_version,
            metadata=body.metadata,
        )
        entry_id = await registry.persist_entry(entry)
    return {"ok": True, "entry_id": entry_id, "entry": entry.to_metadata()}


@router.get("/contamination/{dataset_id}")
async def list_contamination(
    dataset_id: str,
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        registry = PostgresContaminationRegistry(session)
        await registry.hydrate()
        entries = registry.query_exposures(dataset_id=dataset_id)
    return dataset_response(
        count=len(entries),
        data=[e.to_metadata() for e in entries],
        dataset="te_contamination_registry",
    )


@router.get("/health")
async def temporal_health(_: None = Depends(_ensure_ready)):
    return {"ok": True, "component": "temporal_spine", "timestamp": datetime.now(UTC).isoformat()}
