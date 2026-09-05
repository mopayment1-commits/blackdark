"""Batch 05 handler — routes IDs 201–250 to batch05 production spine."""

from __future__ import annotations

from typing import Any

from cap646.batch05_production import execute
from cap646.handlers._batch_route import route_batch_capability


async def handle_batch05_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await route_batch_capability(execute, capability_id, params=params)
