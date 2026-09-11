"""Official batch 01 — handcrafted batch01 production spine (IDs 1–25)."""

from __future__ import annotations

from typing import Any

OFFICIAL_BATCH01_IDS = frozenset(range(1, 26))
BATCH01_DEDICATED_IDS = OFFICIAL_BATCH01_IDS
BATCH01_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    from cap646.batch01_production import execute as batch01_execute

    return await batch01_execute(capability_id, params=params)
