"""Shared batch handler routing — Extract Function (Fowler Rule of Three)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


async def route_batch_capability(
    execute: Callable[..., Awaitable[dict[str, Any]]],
    capability_id: int,
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    return await execute(capability_id, params=params)
