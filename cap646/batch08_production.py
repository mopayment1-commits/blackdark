"""Batch 08 prep — production spine for official Batch 08 (IDs 351–400)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH08_IDS: frozenset[int] = frozenset(range(351, 401))
BATCH08_PREP_IDS = BATCH08_IDS

from cap646.batch08_dedicated import BATCH08_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch08_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch08(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch08_production"
    result["backend_entrypoint"] = batch08_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch08_prep"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH08_IDS:
        raise ValueError(f"capability {capability_id} is not in batch08 prep production spine")
    params = dict(params or {})
    if capability_id in BATCH08_DEDICATED_IDS:
        from cap646.batch08_dedicated import execute as execute_dedicated
        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch08(result, capability_id)
    raise ValueError(f"batch08_prep: unmapped capability {capability_id}")


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

    _entry.__name__ = batch08_entrypoint(capability_id)
    _entry.__doc__ = f"Batch08 prep production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH08_IDS:
    globals()[batch08_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
