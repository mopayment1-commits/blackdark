"""
B9 → #34/#35/#36/#51 targeted reconciliation bridge.

Binds research/explanation surfaces to launch57.research_explanation_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch9_isolation import finalize_b9_response
from launch57.b8_alerts_bridge import apply_b8_trust_envelope
from launch57.research_explanation_timing_common import (
    B9_LAUNCH_NUMBERS,
    attach_explanation_temporal_envelope,
    build_explanation_timing_context,
)

B9_RESEARCH_EXPLANATION_TIMING_ACTIVATED: bool = True


def b9_research_explanation_timing_state() -> dict[str, Any]:
    return {
        "contract": "B9_RESEARCH_EXPLANATION_TIMING_RECONCILIATION",
        "activated": B9_RESEARCH_EXPLANATION_TIMING_ACTIVATED,
        "affected_launch_items": sorted(B9_LAUNCH_NUMBERS),
        "status": "PENDING_VERIFICATION" if B9_RESEARCH_EXPLANATION_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/research_explanation_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b9_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b8_trust_envelope(body, display_timezone=display_timezone)
    out["b9_research_explanation_timing"] = b9_research_explanation_timing_state()
    return finalize_b9_response(out)


def finalize_b9_explanation_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §18 explanation timing; fail closed on expired/stale explanations."""
    launch_id = int(body.get("launch_item_id") or 0)
    if launch_id not in B9_LAUNCH_NUMBERS:
        return body

    if not B9_RESEARCH_EXPLANATION_TIMING_ACTIVATED:
        return apply_b9_trust_envelope(body, display_timezone=display_timezone)

    p = dict(payload or {})
    zone = display_timezone or p.get("display_timezone")
    explanation_row = _extract_explanation_row(body)
    timing = build_explanation_timing_context(
        p,
        explanation=explanation_row,
        spine=spine,
        display_timezone=zone,
    )
    out = apply_b9_trust_envelope(body, display_timezone=zone)
    out = attach_explanation_temporal_envelope(out, timing)

    if not timing.presented_as_current and out.get("success") is not False:
        out["success"] = False
        out["error"] = timing.expired_reason or "explanation_expired"
        out["presented_as_current"] = False

    out["b9_research_explanation_timing"] = b9_research_explanation_timing_state()
    return finalize_b9_response(out)


def _extract_explanation_row(body: dict[str, Any]) -> dict[str, Any]:
    for key in ("explanation", "price_move_explanation", "research_agent", "research_portal", "research_reports", "shareable_brief"):
        block = body.get(key)
        if isinstance(block, dict):
            return block
    return {}
