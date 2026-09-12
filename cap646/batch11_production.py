"""Batch 11 prep — production spine for official Batch 11 (IDs 501–550)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

BATCH11_IDS: frozenset[int] = frozenset(range(501, 551))
BATCH11_PREP_IDS = BATCH11_IDS

from cap646.batch11_dedicated import BATCH11_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch11_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch11(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch11_production"
    result["backend_entrypoint"] = batch11_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch11_prep"
    nested = result.get("data") if isinstance(result.get("data"), dict) else {}
    if not result.get("data_source") and not result.get("source"):
        result["data_source"] = nested.get("data_source") or nested.get("source") or f"cap646.batch11_production#cap{capability_id:03d}"
    if not result.get("timestamp"):
        result["timestamp"] = result.get("timestamp") or nested.get("timestamp") or datetime.now(UTC).isoformat()
    if not result.get("quality"):
        result["quality"] = {"freshness": "runtime_stamped", "provenance": result.get("data_source")}
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH11_IDS:
        raise ValueError(f"capability {capability_id} is not in batch11 prep production spine")
    params = dict(params or {})
    if capability_id in BATCH11_DEDICATED_IDS:
        from cap646.batch11_dedicated import execute as execute_dedicated
        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch11(result, capability_id)
    raise ValueError(f"batch11_prep: unmapped capability {capability_id}")


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

    _entry.__name__ = batch11_entrypoint(capability_id)
    _entry.__doc__ = f"Batch11 prep production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH11_IDS:
    globals()[batch11_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
