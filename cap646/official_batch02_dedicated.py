"""Official batch 02 — institutional production spine (IDs 26–50)."""

from __future__ import annotations

from typing import Any

from cap646.batch02_official_production import (
    BATCH02_DEDICATED_IDS,
    BATCH02_OVERLAP_BATCH01_IDS,
    EXPECTED_SURFACE,
    OFFICIAL_BATCH02_IDS,
)


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    from cap646.batch02_official_production import execute as batch02_execute

    return await batch02_execute(capability_id, params=params)
