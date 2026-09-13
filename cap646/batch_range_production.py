"""Production spine for capabilities 151–826 — 25-cap institutional batches (batch07+)."""

from __future__ import annotations

import importlib
from typing import Any, Awaitable, Callable

from cap646.batch_constants import (
    BATCH_RANGE_IDS,
    CAPABILITIES_PER_BATCH,
    DEDICATED_RANGE_START,
    batch_number,
    official_batch_name,
    total_batch_count,
)


def batch_range_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp(result: dict[str, Any], capability_id: int, *, dedicated: bool = False) -> dict[str, Any]:
    batch = official_batch_name(capability_id)
    result.setdefault("production_spine", batch)
    result.setdefault("official_batch", batch)
    result.setdefault("capabilities_per_batch", CAPABILITIES_PER_BATCH)
    if dedicated:
        result["backend_module"] = "cap646.batch_range_production"
        result["backend_entrypoint"] = batch_range_entrypoint(capability_id)
        result["binding_source"] = "explicit_option_a"
    return result


def _dedicated_module(batch_num: int):
    if batch_num < batch_number(DEDICATED_RANGE_START):
        return None
    mod_name = f"cap646.batch{batch_num:02d}_dedicated"
    try:
        return importlib.import_module(mod_name)
    except ImportError:
        return None


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH_RANGE_IDS:
        raise ValueError(f"capability {capability_id} is not in batch07+ production spine (151–826)")

    from cap646.catalog import catalog_by_id

    params = dict(params or {})
    row = catalog_by_id()[capability_id]

    batch_num = batch_number(capability_id)
    dedicated_mod = _dedicated_module(batch_num)
    if dedicated_mod is not None:
        dedicated_ids = getattr(dedicated_mod, f"BATCH{batch_num:02d}_DEDICATED_IDS", frozenset())
        if capability_id in dedicated_ids:
            result = await dedicated_mod.execute(capability_id, params=params)
            result.setdefault("capability", row["capability"])
            result.setdefault("track", row["track"])
            return _stamp(result, capability_id, dedicated=True)

    from cap646.batch01_production import LEGACY_BATCH01_EXTENSION_IDS

    if capability_id in LEGACY_BATCH01_EXTENSION_IDS:
        from cap646.batch01_production import execute as batch01_execute

        result = await batch01_execute(capability_id, params=params)
        result.setdefault("capability", row["capability"])
        result.setdefault("track", row["track"])
        return _stamp(result, capability_id)

    from cap646.backend_executor import execute_binding

    result = await execute_binding(capability_id, params=params)
    if not result.get("success"):
        result.setdefault("error", "binding_execution_failed")
    result.setdefault("capability", row["capability"])
    result.setdefault("track", row["track"])
    return _stamp(result, capability_id)


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

    _entry.__name__ = batch_range_entrypoint(capability_id)
    return _entry


for _cid in BATCH_RANGE_IDS:
    globals()[batch_range_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
