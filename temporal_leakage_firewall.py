"""Temporal Leakage Firewall — registry-facing entrypoint (P0.1 truth primitive)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from blackdark.temporal.accessibility import filter_point_in_time as _filter_point_in_time

__all__ = ["filter_point_in_time"]


def filter_point_in_time(
    rows: list[dict[str, Any]],
    *,
    cutoff: datetime | str,
    time_field: str = "available_at",
    strict: bool = True,
) -> list[dict[str, Any]]:
    """Reject rows whose available_at was not accessible at simulated decision time."""
    return _filter_point_in_time(rows, cutoff=cutoff, time_field=time_field, strict=strict)
