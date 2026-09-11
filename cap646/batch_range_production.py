"""Production spine for official batches 04–17 (IDs 151–826)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

OFFICIAL_BATCH04_IDS: frozenset[int] = frozenset(range(151, 201))
OFFICIAL_BATCH05_IDS: frozenset[int] = frozenset(range(201, 251))
OFFICIAL_BATCH06_IDS: frozenset[int] = frozenset(range(251, 301))
OFFICIAL_BATCH07_IDS: frozenset[int] = frozenset(range(301, 351))
OFFICIAL_BATCH08_IDS: frozenset[int] = frozenset(range(351, 401))
OFFICIAL_BATCH09_IDS: frozenset[int] = frozenset(range(401, 451))
OFFICIAL_BATCH10_IDS: frozenset[int] = frozenset(range(451, 501))
OFFICIAL_BATCH11_IDS: frozenset[int] = frozenset(range(501, 551))
OFFICIAL_BATCH12_IDS: frozenset[int] = frozenset(range(551, 601))
OFFICIAL_BATCH13_IDS: frozenset[int] = frozenset(range(601, 651))
OFFICIAL_BATCH14_IDS: frozenset[int] = frozenset(range(651, 701))
OFFICIAL_BATCH15_IDS: frozenset[int] = frozenset(range(701, 751))
OFFICIAL_BATCH16_IDS: frozenset[int] = frozenset(range(751, 801))
OFFICIAL_BATCH17_IDS: frozenset[int] = frozenset(range(801, 827))

BATCH_RANGE_IDS: frozenset[int] = (
    OFFICIAL_BATCH04_IDS
    | OFFICIAL_BATCH05_IDS
    | OFFICIAL_BATCH06_IDS
    | OFFICIAL_BATCH07_IDS
    | OFFICIAL_BATCH08_IDS
    | OFFICIAL_BATCH09_IDS
    | OFFICIAL_BATCH10_IDS
    | OFFICIAL_BATCH11_IDS
    | OFFICIAL_BATCH12_IDS
    | OFFICIAL_BATCH13_IDS
    | OFFICIAL_BATCH14_IDS
    | OFFICIAL_BATCH15_IDS
    | OFFICIAL_BATCH16_IDS
    | OFFICIAL_BATCH17_IDS
)


def official_batch_name(capability_id: int) -> str:
    return f"batch{(capability_id - 1) // 50 + 1:02d}"


def batch_range_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    batch = official_batch_name(capability_id)
    result["backend_module"] = "cap646.batch_range_production"
    result["backend_entrypoint"] = batch_range_entrypoint(capability_id)
    result["binding_source"] = "batch_range_production_spine"
    result["production_spine"] = batch
    result.setdefault("official_batch", batch)
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH_RANGE_IDS:
        raise ValueError(f"capability {capability_id} is not in batch04–17 production spine")

    from cap646.backend_executor import execute_binding
    from cap646.catalog import catalog_by_id

    params = dict(params or {})
    row = catalog_by_id()[capability_id]
    result = await execute_binding(capability_id, params=params)

    if not result.get("success"):
        from cap646.batch_failure_rescue import rescue_capability

        rescued = await rescue_capability(capability_id, params=params, prior=result)
        if rescued.get("success"):
            result = rescued

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
