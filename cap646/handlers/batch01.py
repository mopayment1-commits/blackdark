"""Batch 01 handler — routes capabilities 1–50 through the production spine."""

from __future__ import annotations

from typing import Any

from cap646.batch01_production import execute
from cap646.handlers._batch_route import route_batch_capability


async def handle_batch01_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await route_batch_capability(execute, capability_id, params=params)
