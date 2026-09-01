"""Batch 03 prep handler — routes IDs 101–150 to batch03 production spine."""

from __future__ import annotations

from typing import Any

from cap646.batch03_production import execute


async def handle_batch03_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await execute(capability_id, params=params)
