"""Batch 02 — canonical production spine for 826-completion (IDs 101–150, 50 capabilities)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH02_IDS: frozenset[int] = frozenset(range(101, 151))

from cap646.batch02_dedicated import BATCH02_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch02_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch02(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch02_production"
    result["backend_entrypoint"] = batch02_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch02"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH02_IDS:
        raise ValueError(f"capability {capability_id} is not in batch02 production spine")

    params = dict(params or {})

    if capability_id in BATCH02_DEDICATED_IDS:
        from cap646.batch02_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch02(result, capability_id)

    raise ValueError(f"batch02: unmapped capability {capability_id}")


def _make_cap_entrypoint(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _entry(*, params: dict[str, Any] | None = None, capability_id: int = capability_id) -> dict[str, Any]:
        return await execute(capability_id, params=params)

    _entry.__name__ = batch02_entrypoint(capability_id)
    _entry.__doc__ = f"Batch02 production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH02_IDS:
    globals()[batch02_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
