"""Production temporal spine orchestration (P0-1)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.data import temporal_repository as repo

logger = logging.getLogger("BLACKDARK.Temporal.Spine")
from blackdark.temporal.firewall import TemporalProcessingContext, evaluate_temporal_leakage_firewall
from blackdark.temporal.replay_coverage import run_full_decision_path_replay
from blackdark.temporal.normalization import normalize_ingestion_to_canonical_event
from blackdark.temporal.observability import SpineObservability
from blackdark.temporal.p2_pipeline import run_p2_outcome_evidence_pipeline
from blackdark.temporal.p3_pipeline import run_forward_shadow_pipeline
from blackdark.temporal.persistence.postgres import (
    PostgresContaminationRegistry,
    PostgresEventStore,
    PostgresEvidenceLedger,
    PostgresForwardShadowLedger,
)
from blackdark.temporal.metrics import increment_temporal_metric, record_spine_outcome
from blackdark.temporal.pit_contract import PitContractViolation
from blackdark.temporal.reality_anchor_service import observe_reality_anchor
from blackdark.temporal.decision_path import execute_historical_decision_path
from blackdark.temporal.reconstruction import reconstruct_point_in_time
from blackdark.temporal.replay import ReplayRequest, run_deterministic_mass_replay
from blackdark.temporal.serialization import evidence_record_to_row


@dataclass(frozen=True, slots=True)
class ProductionSpineRequest:
    ingestion_payload: Mapping[str, Any]
    simulated_time: datetime
    prediction: Any
    confidence: float
    abstention_state: str
    subject_identity: str
    input_identity: str
    model_version: str = "model-v1"
    rule_config_version: str = "rule-v1"
    dataset_version: str = "ds-1"
    code_version: str = "code-v1"
    input_snapshot_hash: str = "hash-0"
    idempotency_key: str | None = None
    uses_simulated_time: bool = True
    live_forward_passage_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class ProductionSpineResult:
    run_id: str
    event_id: str | None
    evidence_ids: tuple[str, ...]
    receipt_id: str | None
    reality_anchor_needs_runtime_verification: bool
    observability: Mapping[str, Any]
    p2_metadata: Mapping[str, Any] | None
    p3_metadata: Mapping[str, Any] | None
    status: str
    error_code: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "event_id": self.event_id,
            "evidence_ids": list(self.evidence_ids),
            "receipt_id": self.receipt_id,
            "reality_anchor_needs_runtime_verification": self.reality_anchor_needs_runtime_verification,
            "observability": dict(self.observability),
            "p2_metadata": dict(self.p2_metadata) if self.p2_metadata else None,
            "p3_metadata": dict(self.p3_metadata) if self.p3_metadata else None,
            "status": self.status,
            "error_code": self.error_code,
        }


async def run_production_temporal_spine(
    session: AsyncSession,
    request: ProductionSpineRequest,
) -> ProductionSpineResult:
    started = time.perf_counter()
    run_id = repo.new_spine_run_id()
    obs = SpineObservability()
    event_store = PostgresEventStore(session)
    evidence_ledger = PostgresEvidenceLedger(session)
    shadow_ledger = PostgresForwardShadowLedger(session)
    contamination_registry = PostgresContaminationRegistry(session)
    await contamination_registry.hydrate()

    try:
        if request.idempotency_key:
            existing = await repo.get_canonical_event_by_idempotency_key(
                session, request.idempotency_key
            )
            if existing:
                obs.record("idempotency", "hit", event_id=existing["event_id"])
                return ProductionSpineResult(
                    run_id=run_id,
                    event_id=existing["event_id"],
                    evidence_ids=(),
                    receipt_id=None,
                    reality_anchor_needs_runtime_verification=True,
                    observability=obs.to_metadata(),
                    p2_metadata=None,
                    p3_metadata=None,
                    status="completed",
                )

        obs.record("normalization", "started")
        event = normalize_ingestion_to_canonical_event(request.ingestion_payload, strict=True)
        obs.record("normalization", "completed", event_id=event.event_id)

        obs.record("pit_reconstruction", "started")
        record = event.to_temporal_record()
        pit = reconstruct_point_in_time([record], request.simulated_time, strict=True)
        if not pit.included:
            raise PitContractViolation(
                "PIT_RECONSTRUCTION_EMPTY",
                "No records accessible at simulated_time",
            )
        obs.record("pit_reconstruction", "completed", included=len(pit.included))

        obs.record("leakage_firewall", "started")
        ctx = TemporalProcessingContext(
            simulated_time=request.simulated_time,
            strict_mode=True,
        )
        firewall = evaluate_temporal_leakage_firewall([record], ctx)
        if not firewall.allowed:
            raise PitContractViolation(
                "TEMPORAL_LEAKAGE_REJECTED",
                ",".join(firewall.reason_codes) or "leakage_detected",
            )
        obs.record("leakage_firewall", "completed")

        obs.record("persistence_event", "started")
        await event_store.persist_append(event, idempotency_key=request.idempotency_key)
        obs.record("persistence_event", "completed", event_id=event.event_id)

        obs.record("replay", "started")
        replay_request = ReplayRequest(
            event_source=event_store,
            start_time=request.simulated_time,
            end_time=request.simulated_time,
            replay_clock_or_schedule=(request.simulated_time,),
            strict_mode=True,
            replay_parameters={"model_version": request.model_version},
            dataset_or_source_version_context={"dataset_version": request.dataset_version},
        )
        replay = run_deterministic_mass_replay(replay_request)
        decision_path = execute_historical_decision_path(
            event_source=event_store,
            mass_replay=replay,
            parameters={"dataset_version": request.dataset_version},
            model_identity=request.model_version,
        )
        obs.record("replay", "completed", replay_id=replay.replay_id)

        obs.record("p2_pipeline", "started")
        p2 = run_p2_outcome_evidence_pipeline(
            event_source=event_store,
            mass_replay=replay,
            decision_path=decision_path,
            ledger=evidence_ledger,
        )
        evidence_ids = [record.evidence_id for record in p2.evidence_records]
        await evidence_ledger.flush_records(
            source_table="te_canonical_events",
            source_record_id=event.event_id,
        )
        obs.record("p2_pipeline", "completed", evidence_count=len(evidence_ids))

        obs.record("p3_pipeline", "started")
        p3 = run_forward_shadow_pipeline(
            subject_identity=request.subject_identity,
            input_identity=request.input_identity,
            prediction=request.prediction,
            confidence=request.confidence,
            abstention_state=request.abstention_state,
            issued_at=request.simulated_time,
            evaluation_time=datetime.now(UTC),
            temporal_context={"simulated_time": request.simulated_time.isoformat()},
            source_context=dict(event.provenance.to_metadata()),
            model_version=request.model_version,
            rule_config_version=request.rule_config_version,
            dataset_version=request.dataset_version,
            code_version=request.code_version,
            input_snapshot_hash=request.input_snapshot_hash,
            shadow_ledger=shadow_ledger,
            evidence_ledger=evidence_ledger,
            uses_simulated_time=request.uses_simulated_time,
        )
        receipt = await shadow_ledger.persist_receipt(
            p3.shadow_receipt,
            idempotency_key=request.idempotency_key,
        )
        flushed = await evidence_ledger.flush_records(
            source_table="te_canonical_events",
            source_record_id=event.event_id,
        )
        for record in flushed:
            if record.evidence_id not in evidence_ids:
                evidence_ids.append(record.evidence_id)
        obs.record("p3_pipeline", "completed", receipt_id=receipt.shadow_receipt_id)

        obs.record("reality_anchor", "started")
        anchor_obs = await observe_reality_anchor(
            session,
            receipt=receipt,
            evaluation_time=datetime.now(UTC),
            uses_simulated_time=request.uses_simulated_time,
            live_forward_passage_confirmed=request.live_forward_passage_confirmed,
            runtime_context={"run_id": run_id},
        )
        obs.record(
            "reality_anchor",
            "completed",
            needs_runtime_verification=anchor_obs.needs_runtime_verification,
        )

        await repo.insert_spine_run(
            session,
            {
                "run_id": run_id,
                "pipeline_stage": "production_spine",
                "status": "completed",
                "input_idempotency_key": request.idempotency_key,
                "event_id": event.event_id,
                "evidence_id": evidence_ids[0] if evidence_ids else None,
                "receipt_id": receipt.shadow_receipt_id,
                "error_code": None,
                "observability": json.dumps(obs.to_metadata()),
            },
        )

        result = ProductionSpineResult(
            run_id=run_id,
            event_id=event.event_id,
            evidence_ids=tuple(evidence_ids),
            receipt_id=receipt.shadow_receipt_id,
            reality_anchor_needs_runtime_verification=anchor_obs.needs_runtime_verification,
            observability=obs.to_metadata(),
            p2_metadata=p2.to_metadata(),
            p3_metadata=p3.to_metadata(),
            status="completed",
        )
        record_spine_outcome(
            status="completed",
            reality_anchor_pending=anchor_obs.needs_runtime_verification,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        return result
    except PitContractViolation as exc:
        obs.record("failed", "pit_contract", code=exc.code)
        await repo.insert_spine_run(
            session,
            {
                "run_id": run_id,
                "pipeline_stage": "production_spine",
                "status": "failed",
                "input_idempotency_key": request.idempotency_key,
                "event_id": None,
                "evidence_id": None,
                "receipt_id": None,
                "error_code": exc.code,
                "observability": json.dumps(obs.to_metadata()),
            },
        )
        failed = ProductionSpineResult(
            run_id=run_id,
            event_id=None,
            evidence_ids=(),
            receipt_id=None,
            reality_anchor_needs_runtime_verification=True,
            observability=obs.to_metadata(),
            p2_metadata=None,
            p3_metadata=None,
            status="failed",
            error_code=exc.code,
        )
        record_spine_outcome(
            status="failed",
            error_code=exc.code,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        return failed
    except Exception as exc:
        obs.record("failed", "unexpected", error=str(exc))
        increment_temporal_metric("temporal_db_failures_total")
        try:
            await repo.insert_spine_run(
                session,
                {
                    "run_id": run_id,
                    "pipeline_stage": "production_spine",
                    "status": "failed",
                    "input_idempotency_key": request.idempotency_key,
                    "event_id": None,
                    "evidence_id": None,
                    "receipt_id": None,
                    "error_code": type(exc).__name__,
                    "observability": json.dumps(obs.to_metadata()),
                },
            )
        except Exception:
            logger.exception("Failed to persist spine run after unexpected error; transaction will roll back")
        raise
