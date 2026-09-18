"""
B4 → #2/#3 targeted reconciliation bridge.

Binds trust_batch1 oracle/certificate paths to launch57.decision_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch4_isolation import finalize_b4_response
from launch57.decision_timing_common import (
    attach_decision_temporal_envelope,
    build_decision_timing_context,
    snapshot_decision_time_evidence_state,
)
from launch57.evidence_class_common import attach_evidence_class_metadata
from launch57.failure_recovery_common import attach_failure_recovery_envelope
from launch57.teis_support_common import attach_teis_support_envelope

B4_DECISION_TIMING_ACTIVATED: bool = True


def b4_decision_timing_state() -> dict[str, Any]:
    return {
        "contract": "B4_DECISION_TIMING_RECONCILIATION",
        "activated": B4_DECISION_TIMING_ACTIVATED,
        "affected_launch_items": [2, 3],
        "status": "PENDING_VERIFICATION" if B4_DECISION_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/decision_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b4_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    """Evidence display via canonical #6 owner; no cap646.evidence_class."""
    out = attach_evidence_class_metadata(dict(body), display_timezone=display_timezone)
    cls = out.get("evidence_class", "SHADOW_LIVE_FORWARD")
    out["compliance_footer"] = {
        "evidence_class": cls,
        "unknown_is_not_zero": True,
        "legal": (
            "Decision evidence only. Not financial advice. "
            f"Evidence class={cls}. Stale/untrusted inputs must not pass as success."
        ),
    }
    out["b4_decision_timing"] = b4_decision_timing_state()
    return finalize_b4_response(
        attach_failure_recovery_envelope(
            attach_teis_support_envelope(out),
            launch_item_id=int(out.get("launch_item_id") or 0) or None,
        )
    )


def finalize_b4_decision_surface(
    body: dict[str, Any],
    *,
    display_timezone: str | None = None,
    require_authoritative_decision_time: bool = False,
) -> dict[str, Any] | None:
    """Attach decision timing + evidence snapshot; return None when timing fails closed."""
    if not B4_DECISION_TIMING_ACTIVATED:
        return apply_b4_trust_envelope(body, display_timezone=display_timezone)

    timing = build_decision_timing_context(
        body,
        display_timezone=display_timezone,
        require_authoritative_decision_time=require_authoritative_decision_time,
    )
    if timing is None:
        return None

    evidence = snapshot_decision_time_evidence_state(body, display_timezone=display_timezone)
    out = apply_b4_trust_envelope(body, display_timezone=display_timezone)
    out["decision_time_evidence_state"] = evidence.to_payload()
    out = attach_decision_temporal_envelope(out, timing)
    out["b4_decision_timing"] = b4_decision_timing_state()
    return finalize_b4_response(
        attach_failure_recovery_envelope(
            attach_teis_support_envelope(out),
            launch_item_id=int(out.get("launch_item_id") or 0) or None,
        )
    )
