"""Batch 03 — production spine for official IDs 101–150."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH03_IDS: frozenset[int] = frozenset(range(101, 151))
OFFICIAL_BATCH03_IDS = BATCH03_IDS
BATCH03_PREP_IDS = BATCH03_IDS  # legacy alias

from cap646.batch03_dedicated import BATCH03_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch03_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch03(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch03_production"
    result["backend_entrypoint"] = batch03_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch03"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH03_IDS:
        raise ValueError(f"capability {capability_id} is not in batch03 production spine")

    params = dict(params or {})

    if capability_id in BATCH03_DEDICATED_IDS:
        from cap646.batch03_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch03(result, capability_id)

    raise ValueError(f"batch03: unmapped capability {capability_id}")


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

    _entry.__name__ = batch03_entrypoint(capability_id)
    _entry.__doc__ = f"Batch03 prep production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH03_IDS:
    globals()[batch03_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
