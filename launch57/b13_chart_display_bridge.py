"""
B13 → cross-cutting chart display timing bridge (SPEC §22).

Binds chart-bearing surfaces to launch57.chart_display_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch13_isolation import finalize_b13_response
from launch57.chart_display_timing_common import (
    attach_chart_display_temporal_envelope,
    bind_chart_components,
    build_chart_display_timing_context,
    is_chart_bearing_body,
)

B13_CHART_DISPLAY_TIMING_ACTIVATED: bool = True


def b13_chart_display_timing_state() -> dict[str, Any]:
    return {
        "contract": "B13_CHART_DISPLAY_TIMING_RECONCILIATION",
        "activated": B13_CHART_DISPLAY_TIMING_ACTIVATED,
        "domain": "charts_cross_cutting",
        "status": "PENDING_VERIFICATION" if B13_CHART_DISPLAY_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/chart_display_timing_common.py",
        "reopen_reason": "NONE",
    }


def finalize_b13_chart_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §22 chart display timezone consistency; fail closed on mixing."""
    if not is_chart_bearing_body(body):
        return body

    if not B13_CHART_DISPLAY_TIMING_ACTIVATED:
        out = dict(body)
        out["b13_chart_display_timing"] = b13_chart_display_timing_state()
        return finalize_b13_response(out)

    p = dict(payload or {})
    zone = display_timezone or p.get("display_timezone")
    existing_view = dict(body.get("chart_view") or {})
    timing_probe = build_chart_display_timing_context(p, chart_view=existing_view, display_timezone=zone)

    out = dict(body)
    if timing_probe.timezone_mixing_detected:
        out = attach_chart_display_temporal_envelope(out, timing_probe)
        out["success"] = False
        out["error"] = out.get("error") or timing_probe.expired_reason or "chart_timezone_mixing"
        out["chart_temporally_consistent"] = False
        out["b13_chart_display_timing"] = b13_chart_display_timing_state()
        return finalize_b13_response(out)

    out = bind_chart_components(
        out,
        display_timezone=timing_probe.display_timezone,
        canonical_storage_timezone=timing_probe.canonical_storage_timezone,
    )
    timing = build_chart_display_timing_context(p, chart_view=out.get("chart_view"), display_timezone=zone)
    out = attach_chart_display_temporal_envelope(out, timing)
    out["b13_chart_display_timing"] = b13_chart_display_timing_state()
    return finalize_b13_response(out)
