"""Batch 05 — production spine for official IDs 201–250."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH05_IDS: frozenset[int] = frozenset(range(201, 201 + 50))
OFFICIAL_BATCH05_IDS = BATCH05_IDS

from cap646.batch05_dedicated import BATCH05_DEDICATED_IDS, BATCH05_REUSED_LINK_BATCH01_IDS
from cap646.evidence_class import ai_compliance_footer


def batch05_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch05(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch05_production"
    result["backend_entrypoint"] = batch05_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch05"
    if capability_id in BATCH05_REUSED_LINK_BATCH01_IDS:
        result.setdefault("closure_status", "REUSED-LINK")
    else:
        result.setdefault("closure_status", "NOT_COMPLETE")
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH05_IDS:
        raise ValueError(f"capability {capability_id} is not in batch05 production spine")

    params = dict(params or {})

    if capability_id in BATCH05_DEDICATED_IDS:
        from cap646.batch05_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch05(result, capability_id)

    raise ValueError(f"batch05: unmapped capability {capability_id}")


def _make_cap_entrypoint(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _entry(
        symbol: str = "BTC",
        *,
        params: dict[str, Any] | None = None,
        capability_id: int = capability_id,
    ) -> dict[str, Any]:
        merged = dict(params or {})
        merged.setdefault("symbol", symbol)
        return await execute(capability_id, params=merged)

    _entry.__name__ = batch05_entrypoint(capability_id)
    _entry.__doc__ = f"Batch05 production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH05_IDS:
    globals()[batch05_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
