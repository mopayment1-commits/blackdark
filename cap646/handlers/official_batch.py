"""Official 25-cap batch handler — routes capabilities 1–826 through production spine."""

from __future__ import annotations

from typing import Any


async def handle_official_batch_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.official_batch_production import execute

    return await execute(capability_id, params=params)
