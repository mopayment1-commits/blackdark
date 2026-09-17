"""
Launch-57 cross-cutting infrastructure temporal boundary (B14 / SPEC §23–§27).
"""

from __future__ import annotations

from typing import Any

from launch57.infrastructure_temporal_common import is_api_bearing_body


def attach_infrastructure_boundary(
    body: dict[str, Any],
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not is_api_bearing_body(body):
        return body
    from launch57.b14_infrastructure_temporal_bridge import finalize_b14_infrastructure_surface

    p = dict(params or {})
    return finalize_b14_infrastructure_surface(body, payload=p)
