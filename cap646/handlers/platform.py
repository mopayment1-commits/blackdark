"""Institutional registry-backed capability execution (replaces generic hash routing)."""

from __future__ import annotations

from typing import Any

from cap646.backend_executor import handle_registry_capability

__all__ = ["handle_platform_capability", "handle_registry_capability"]


async def handle_platform_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await handle_registry_capability(capability_id, params=params)
