"""Batch 02 handler — routes capabilities 101–150 through the production spine."""

from __future__ import annotations

from typing import Any

from cap646.batch02_production import execute


async def handle_batch02_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await execute(capability_id, params=params)
