"""
B14 → cross-cutting infrastructure temporal bridge (SPEC §23–§27).

Binds API/DB/clock/DST/scheduling surfaces to launch57.infrastructure_temporal_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch14_isolation import finalize_b14_response
from launch57.infrastructure_temporal_common import (
    ClockContext,
    DstGapFoldPolicy,
    attach_infrastructure_temporal_envelope,
    build_clock_health_snapshot,
    build_infrastructure_temporal_context,
    is_api_bearing_body,
    normalize_response_api_timestamps,
)

B14_INFRASTRUCTURE_TEMPORAL_ACTIVATED: bool = True


def b14_infrastructure_temporal_state() -> dict[str, Any]:
    return {
        "contract": "B14_INFRASTRUCTURE_TEMPORAL_RECONCILIATION",
        "activated": B14_INFRASTRUCTURE_TEMPORAL_ACTIVATED,
        "domain": "api_db_clock_dst_scheduling_cross_cutting",
        "status": "PENDING_VERIFICATION" if B14_INFRASTRUCTURE_TEMPORAL_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/infrastructure_temporal_common.py",
        "reopen_reason": "NONE",
    }


def finalize_b14_infrastructure_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach SPEC §23–§27 infrastructure temporal envelope; fail closed on violations."""
    if not is_api_bearing_body(body):
        return body

    if not B14_INFRASTRUCTURE_TEMPORAL_ACTIVATED:
        out = dict(body)
        out["b14_infrastructure_temporal"] = b14_infrastructure_temporal_state()
        return finalize_b14_response(out)

    p = dict(payload or {})
    governed = dict(p.get("governed_payload") or {})
    offset = float(governed.get("estimated_clock_offset_sec") or p.get("estimated_clock_offset_sec") or 0.0)
    context_name = str(
        governed.get("clock_context") or p.get("clock_context") or ClockContext.DEFAULT.value
    )
    try:
        clock_context = ClockContext(context_name)
    except ValueError:
        clock_context = ClockContext.DEFAULT

    dst_policy_name = str(governed.get("dst_policy") or p.get("dst_policy") or DstGapFoldPolicy.REJECT.value)
    try:
        dst_policy = DstGapFoldPolicy(dst_policy_name)
    except ValueError:
        dst_policy = DstGapFoldPolicy.REJECT

    timing_probe = build_infrastructure_temporal_context(
        body,
        estimated_clock_offset_sec=offset,
        clock_context=clock_context,
        dst_policy=dst_policy,
    )

    out, _ = normalize_response_api_timestamps(body)
    clock_health = build_clock_health_snapshot(estimated_offset_sec=offset, context=clock_context)

    if not timing_probe.infrastructure_temporally_consistent:
        out = attach_infrastructure_temporal_envelope(out, timing_probe, clock_health=clock_health)
        out["success"] = False
        out["error"] = out.get("error") or timing_probe.expired_reason or "infrastructure_temporal_violation"
        out["b14_infrastructure_temporal"] = b14_infrastructure_temporal_state()
        return finalize_b14_response(out)

    timing = build_infrastructure_temporal_context(
        out,
        estimated_clock_offset_sec=offset,
        clock_context=clock_context,
        dst_policy=dst_policy,
    )
    out = attach_infrastructure_temporal_envelope(out, timing, clock_health=clock_health)
    out["b14_infrastructure_temporal"] = b14_infrastructure_temporal_state()
    return finalize_b14_response(out)
