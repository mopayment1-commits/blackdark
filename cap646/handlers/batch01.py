"""Batch 01 handler — routes capabilities 1–59 through the production spine."""

from __future__ import annotations

from typing import Any

from cap646.batch01_production import execute


async def handle_batch01_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await execute(capability_id, params=params)
