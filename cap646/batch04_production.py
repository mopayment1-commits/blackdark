"""Batch 04 — production spine for official IDs 151–200."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH04_IDS: frozenset[int] = frozenset(range(151, 151 + 50))
OFFICIAL_BATCH04_IDS = BATCH04_IDS

from cap646.batch04_dedicated import BATCH04_DEDICATED_IDS, BATCH04_OVERLAP_BATCH01_IDS
from cap646.evidence_class import ai_compliance_footer


def batch04_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch04(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch04_production"
    result["backend_entrypoint"] = batch04_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch04"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH04_IDS:
        raise ValueError(f"capability {capability_id} is not in batch04 production spine")

    params = dict(params or {})

    if capability_id in BATCH04_OVERLAP_BATCH01_IDS:
        raise ValueError(
            f"capability {capability_id} is batch01 overlap — use cap646.batch01_production / runtime batch01 spine"
        )

    if capability_id in BATCH04_DEDICATED_IDS:
        from cap646.batch04_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch04(result, capability_id)

    raise ValueError(f"batch04: unmapped capability {capability_id}")


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

    _entry.__name__ = batch04_entrypoint(capability_id)
    _entry.__doc__ = f"Batch04 production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH04_IDS:
    globals()[batch04_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
