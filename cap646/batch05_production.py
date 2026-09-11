"""Batch 05 prep — production spine for official Batch 05 (IDs 201–250).

IDs 214/245 cross-spine overlap resolved Run 013 (removed from LEGACY_BATCH01_EXTENSION_IDS).
Catalog duplicates (206→86, 212→17, etc.) — batch05 dedicated handler retained for official RTM scope.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH05_IDS: frozenset[int] = frozenset(range(201, 251))
BATCH05_PREP_IDS = BATCH05_IDS  # alias

from cap646.batch05_dedicated import BATCH05_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch05_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch05(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch05_production"
    result["backend_entrypoint"] = batch05_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch05_prep"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH05_IDS:
        raise ValueError(f"capability {capability_id} is not in batch05 prep production spine")

    params = dict(params or {})

    if capability_id in BATCH05_DEDICATED_IDS:
        from cap646.batch05_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch05(result, capability_id)

    raise ValueError(f"batch05_prep: unmapped capability {capability_id}")


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
    _entry.__doc__ = f"Batch05 prep production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH05_IDS:
    globals()[batch05_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
