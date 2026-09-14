"""Forward Shadow Reality Anchor (P3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

SIMULATED_TIME_PASSAGE_CLAIMED_AS_FORWARD_REALITY = 0

# TEMP-AR-0164 requires live reality anchor — external/live gate preserved
REALITY_ANCHOR_EXTERNAL_GATE_ID = "TEMP-AR-0164"


@dataclass(frozen=True, slots=True)
class RealityAnchorStatus:
    """Distinguishes genuine forward accumulation from historical reconstruction."""

    anchor_id: str
    forward_time_passage_verified: bool
    simulated_time_used: bool
    live_data_required: bool
    external_evidence_pending: bool
    external_gate_requirement_id: str | None
    anchor_metadata: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "forward_time_passage_verified": self.forward_time_passage_verified,
            "simulated_time_used": self.simulated_time_used,
            "live_data_required": self.live_data_required,
            "external_evidence_pending": self.external_evidence_pending,
            "external_gate_requirement_id": self.external_gate_requirement_id,
            "anchor_metadata": dict(self.anchor_metadata),
        }


def evaluate_reality_anchor(
    *,
    anchor_id: str,
    receipt_issued_at: datetime,
    evaluation_time: datetime,
    uses_simulated_time: bool,
    live_forward_passage_confirmed: bool = False,
) -> RealityAnchorStatus:
    """
    TEMP-AR-0163, 0164: forward shadow as reality anchor.

    Live forward passage (0164) is external-gated; local engineering surfaces status only.
    """
    if uses_simulated_time:
        return RealityAnchorStatus(
            anchor_id=anchor_id,
            forward_time_passage_verified=False,
            simulated_time_used=True,
            live_data_required=True,
            external_evidence_pending=True,
            external_gate_requirement_id=REALITY_ANCHOR_EXTERNAL_GATE_ID,
            anchor_metadata={
                "reason": "simulated_time_cannot_claim_forward_reality",
                "receipt_issued_at": receipt_issued_at.isoformat(),
            },
        )

    return RealityAnchorStatus(
        anchor_id=anchor_id,
        forward_time_passage_verified=live_forward_passage_confirmed,
        simulated_time_used=False,
        live_data_required=not live_forward_passage_confirmed,
        external_evidence_pending=not live_forward_passage_confirmed,
        external_gate_requirement_id=(
            REALITY_ANCHOR_EXTERNAL_GATE_ID if not live_forward_passage_confirmed else None
        ),
        anchor_metadata={
            "receipt_issued_at": receipt_issued_at.isoformat(),
            "evaluation_time": evaluation_time.isoformat(),
        },
    )
