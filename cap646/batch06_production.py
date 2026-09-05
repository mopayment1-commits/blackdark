"""Batch 06 — production spine for official IDs 251–300."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.batch06_dedicated import BATCH06_DEDICATED_IDS, BATCH06_REUSED_LINK_IDS
from cap646.batch06_ids import BATCH06_IDS
from cap646.catalog import canonical_id as resolve_canonical
from cap646.entitlements import entitlement_engine
from cap646.evidence_class import ai_compliance_footer


def batch06_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch06(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch06_production"
    result["backend_entrypoint"] = batch06_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch06"
    if capability_id in BATCH06_REUSED_LINK_IDS:
        result.setdefault("closure_status", "REUSED-LINK")
    else:
        result.setdefault("closure_status", "NOT_COMPLETE")
    return result


async def execute(
    capability_id: int,
    *,
    params: dict[str, Any] | None = None,
    user: dict[str, Any] | None = None,
    org_id: str | None = None,
    skip_entitlement: bool = False,
) -> dict[str, Any]:
    if capability_id not in BATCH06_IDS:
        raise ValueError(f"capability {capability_id} is not in batch06 production spine")

    params = dict(params or {})
    target_id = resolve_canonical(capability_id)

    if user is not None and not skip_entitlement:
        ent = await entitlement_engine.check(target_id, user=user, org_id=org_id)
        if not ent.get("allowed"):
            return ai_compliance_footer(
                {
                    "success": False,
                    "capability_id": target_id,
                    "requested_capability_id": capability_id,
                    "entitlement": ent,
                }
            )

    if capability_id in BATCH06_DEDICATED_IDS:
        from cap646.batch06_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch06(result, capability_id)

    raise ValueError(f"batch06: unmapped capability {capability_id}")


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
    return _entry


for _cid in sorted(BATCH06_IDS):
    globals()[batch06_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
