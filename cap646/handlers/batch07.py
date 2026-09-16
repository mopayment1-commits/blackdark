"""Batch 07 prep handler — routes IDs 301–350 to batch07 production spine."""

from __future__ import annotations

from typing import Any

from cap646.batch07_production import execute
from cap646.handlers._batch_route import route_batch_capability


async def handle_batch07_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await route_batch_capability(execute, capability_id, params=params)
