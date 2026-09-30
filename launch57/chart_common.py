"""
Launch-57 cross-cutting chart envelope (B13 / SPEC §22).
"""

from __future__ import annotations

from typing import Any

from launch57.chart_display_timing_common import is_chart_bearing_body


def attach_chart_envelope(
    body: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not is_chart_bearing_body(body):
        return body
    from launch57.b13_chart_display_bridge import finalize_b13_chart_surface

    p = dict(params or {})
    out = finalize_b13_chart_surface(
        body,
        payload=p,
        display_timezone=p.get("display_timezone"),
    )
    from launch57.infrastructure_boundary_common import attach_infrastructure_boundary

    return attach_infrastructure_boundary(out, params=p)
