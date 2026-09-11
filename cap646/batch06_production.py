"""Batch 06 prep — production spine for official Batch 06 (IDs 251–300).

WF-027 preflight Run 015: zero overlap with unresolved legacy IDs {584,629,630,631,642,644,646}.
Catalog duplicates retained with batch06 dedicated handlers for official RTM scope.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH06_IDS: frozenset[int] = frozenset(range(251, 301))
BATCH06_PREP_IDS = BATCH06_IDS  # alias

from cap646.batch06_dedicated import BATCH06_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch06_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch06(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch06_production"
    result["backend_entrypoint"] = batch06_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch06_prep"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH06_IDS:
        raise ValueError(f"capability {capability_id} is not in batch06 prep production spine")

    params = dict(params or {})

    if capability_id in BATCH06_DEDICATED_IDS:
        from cap646.batch06_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch06(result, capability_id)

    raise ValueError(f"batch06_prep: unmapped capability {capability_id}")


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

    _entry.__name__ = batch06_entrypoint(capability_id)
    _entry.__doc__ = f"Batch06 prep production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH06_IDS:
    globals()[batch06_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
