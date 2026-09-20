"""
B3 → #6 targeted reconciliation bridge.

Binds B1/B2 temporal consumer paths to canonical launch57.evidence_class_common (#6).
"""

from __future__ import annotations

from typing import Any

from launch57.batch3_isolation import TEMPORAL_DEPENDENCY_PENDING_6, finalize_b3_response
from launch57.evidence_class_common import attach_evidence_class_metadata

# Builder activation for B3 local implementation session.
B3_EVIDENCE_RECONCILIATION_ACTIVATED: bool = True


def b3_evidence_reconciliation_state() -> dict[str, Any]:
    base = {
        "contract": "B6_TARGETED_RECONCILIATION",
        "auto_activate": False,
        "activated": B3_EVIDENCE_RECONCILIATION_ACTIVATED,
        "affected_launch_items": [6],
        "reopen_reason": "NONE",
    }
    if B3_EVIDENCE_RECONCILIATION_ACTIVATED:
        return {
            **base,
            "status": "PENDING_VERIFICATION",
            "binding_status": "ACTIVATED_BOUND_TO_LAUNCH57_6",
        }
    return {
        **base,
        "status": "PREPARED_NOT_ACTIVATED",
        "required_verdict": "B3:#6=PENDING_VERIFICATION",
    }


def prepare_b3_evidence_path(body: dict[str, Any]) -> dict[str, Any]:
    out = dict(body)
    pending = list(out.get("temporal_dependency_pending") or [])
    if not any(p.get("launch_number") == 6 for p in pending):
        pending.append(TEMPORAL_DEPENDENCY_PENDING_6)
    out["temporal_dependency_pending"] = pending
    out["b3_evidence_reconciliation"] = {
        **b3_evidence_reconciliation_state(),
        "status": "PREPARED_NOT_ACTIVATED",
        "activated": False,
    }
    return finalize_b3_response(out)


def apply_b3_evidence_reconciliation(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    """Attach canonical #6 evidence class when B3 reconciliation is activated."""
    if not B3_EVIDENCE_RECONCILIATION_ACTIVATED:
        return prepare_b3_evidence_path(body)

    out = attach_evidence_class_metadata(dict(body), display_timezone=display_timezone)
    pending = [p for p in (out.get("temporal_dependency_pending") or []) if p.get("launch_number") != 6]
    out["temporal_dependency_pending"] = pending
    out["b3_evidence_reconciliation"] = b3_evidence_reconciliation_state()
    return finalize_b3_response(out)
