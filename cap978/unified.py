"""Unified CAP978 execution and verification (IDs 1–978)."""

from __future__ import annotations

from typing import Any

from cap646.runtime import execute_capability
from cap978.catalog import is_extension
from cap978.verify import execute_extension, verify_functional_978


async def execute_unified(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 978:
        return {"success": False, "error": "capability_id_out_of_range", "capability_id": capability_id}
    if is_extension(capability_id):
        return await execute_extension(capability_id, user=user, params=params)
    return await execute_capability(capability_id, user=user, params=params)


async def verify_unified(capability_id: int, *, user: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 978:
        return {"id": capability_id, "verdict": "NOT_READY", "error": "out_of_range"}
    return await verify_functional_978(capability_id, user=user)
