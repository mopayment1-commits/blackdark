"""Official 25-cap batch production spine — routes every capability 1–826 via institutional production."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.batch_constants import (
    CAPABILITIES_PER_BATCH,
    TOTAL_CAPABILITIES,
    legacy_production_batch_for,
    official_batch_name,
)


def official_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    from cap646.institutional_official_production import _BATCH01_OVERLAP_IDS

    handler_module = str(result.get("handler_module") or "")
    if capability_id in _BATCH01_OVERLAP_IDS or "batch01" in handler_module:
        batch = "batch01"
    elif result.get("production_spine"):
        batch = str(result["production_spine"])
    elif legacy_production_batch_for(capability_id):
        batch = legacy_production_batch_for(capability_id)
    else:
        batch = official_batch_name(capability_id)
    result["production_spine"] = batch
    result["official_batch"] = batch
    result.setdefault("capabilities_per_batch", CAPABILITIES_PER_BATCH)
    if not result.get("backend_module"):
        result["backend_module"] = "cap646.institutional_official_production"
    result.setdefault("backend_entrypoint", official_entrypoint(capability_id))
    result.setdefault("binding_source", "explicit_option_a")
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id < 1 or capability_id > TOTAL_CAPABILITIES:
        raise ValueError(f"capability {capability_id} out of range 1–{TOTAL_CAPABILITIES}")

    from cap646.catalog import catalog_by_id
    from cap646.institutional_official_production import execute as institutional_execute

    row = catalog_by_id().get(capability_id, {})
    result = await institutional_execute(capability_id, params=dict(params or {}))
    result.setdefault("capability", row.get("capability"))
    result.setdefault("track", row.get("track"))
    return _stamp(result, capability_id)


def _make_entry(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _entry(
        symbol: str = "BTC",
        *,
        params: dict[str, Any] | None = None,
        capability_id: int = capability_id,
    ) -> dict[str, Any]:
        merged = dict(params or {})
        merged.setdefault("symbol", symbol)
        return await execute(capability_id, params=merged)

    _entry.__name__ = official_entrypoint(capability_id)
    return _entry


for _cid in range(1, TOTAL_CAPABILITIES + 1):
    globals()[official_entrypoint(_cid)] = _make_entry(_cid)
