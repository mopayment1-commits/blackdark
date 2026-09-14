"""Temporal Leakage Firewall — registry-facing entrypoints (P0.1–P0.3)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from blackdark.temporal.accessibility import filter_point_in_time as _filter_point_in_time
from blackdark.temporal.firewall import (
    TemporalLeakageFirewallDecision,
    TemporalProcessingContext,
    evaluate_temporal_leakage_firewall as _evaluate_temporal_leakage_firewall,
)
from blackdark.temporal.reconstruction import TemporalRecord

__all__ = [
    "evaluate_temporal_leakage_firewall",
    "filter_point_in_time",
]


def filter_point_in_time(
    rows: list[dict[str, Any]],
    *,
    cutoff: datetime | str,
    time_field: str = "available_at",
    strict: bool = True,
) -> list[dict[str, Any]]:
    """Reject rows whose available_at was not accessible at simulated decision time."""
    return _filter_point_in_time(rows, cutoff=cutoff, time_field=time_field, strict=strict)


def evaluate_temporal_leakage_firewall(
    records: Sequence[TemporalRecord],
    *,
    simulated_time: datetime | str,
    strict_mode: bool = True,
    operation: str = "temporal_admission",
) -> TemporalLeakageFirewallDecision:
    """Canonical Temporal Leakage Firewall entrypoint for registry callers."""
    context = TemporalProcessingContext(
        simulated_time=simulated_time,
        strict_mode=strict_mode,
        operation=operation,
    )
    return _evaluate_temporal_leakage_firewall(records, context)
