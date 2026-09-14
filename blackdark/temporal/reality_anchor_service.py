"""Production reality anchor service (TEAS-REQ-054/055 / TEMP-AR-0164)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.data import temporal_repository as repo
from blackdark.temporal.forward_shadow import ForwardShadowReceipt
from blackdark.temporal.reality_anchor import (
    REALITY_ANCHOR_EXTERNAL_GATE_ID,
    RealityAnchorStatus,
    evaluate_reality_anchor,
)


@dataclass(frozen=True, slots=True)
class RealityAnchorObservation:
    observation_id: str
    anchor_status: RealityAnchorStatus
    receipt_id: str | None
    runtime_evidence_captured: bool
    needs_runtime_verification: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "anchor_status": self.anchor_status.to_metadata(),
            "receipt_id": self.receipt_id,
            "runtime_evidence_captured": self.runtime_evidence_captured,
            "needs_runtime_verification": self.needs_runtime_verification,
        }


async def observe_reality_anchor(
    session: AsyncSession,
    *,
    receipt: ForwardShadowReceipt,
    evaluation_time: datetime,
    uses_simulated_time: bool,
    live_forward_passage_confirmed: bool = False,
    runtime_context: Mapping[str, Any] | None = None,
) -> RealityAnchorObservation:
    status = evaluate_reality_anchor(
        anchor_id=receipt.shadow_receipt_id,
        receipt_issued_at=receipt.issued_at,
        evaluation_time=evaluation_time,
        uses_simulated_time=uses_simulated_time,
        live_forward_passage_confirmed=live_forward_passage_confirmed,
    )
    observation_id = f"rao_{uuid4().hex[:16]}"
    needs_runtime = status.external_evidence_pending or not status.forward_time_passage_verified
    payload = {
        "anchor_status": status.to_metadata(),
        "runtime_context": dict(runtime_context or {}),
        "receipt": receipt.to_metadata(),
    }
    await repo.insert_reality_anchor_observation(
        session,
        {
            "observation_id": observation_id,
            "anchor_id": receipt.shadow_receipt_id,
            "receipt_id": receipt.shadow_receipt_id,
            "forward_time_passage_verified": status.forward_time_passage_verified,
            "simulated_time_used": status.simulated_time_used,
            "live_data_required": status.live_data_required,
            "external_evidence_pending": status.external_evidence_pending,
            "external_gate_requirement_id": status.external_gate_requirement_id or REALITY_ANCHOR_EXTERNAL_GATE_ID,
            "observation_payload": json.dumps(payload),
        },
    )
    return RealityAnchorObservation(
        observation_id=observation_id,
        anchor_status=status,
        receipt_id=receipt.shadow_receipt_id,
        runtime_evidence_captured=True,
        needs_runtime_verification=needs_runtime,
    )
