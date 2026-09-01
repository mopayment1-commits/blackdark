"""Batch 01 — canonical production spine for official 826 batch 01 (IDs 1–50).

Owner-approved scope: official Batch 01 = IDs 1–50 only.
``LEGACY_BATCH01_EXTENSION_IDS`` retains earlier cherry-picked spine routes for IDs >50;
those IDs are recorded in RTM under their true ``official_batch``.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

OFFICIAL_BATCH01_IDS: frozenset[int] = frozenset(range(1, 51))

LEGACY_BATCH01_EXTENSION_IDS: frozenset[int] = frozenset(
    {
        55,
        56,
        59,
        60,
        103,
        129,
        175,
        214,
        245,
        584,
        629,
        630,
        631,
        642,
        644,
        646,
    }
)

BATCH01_IDS: frozenset[int] = OFFICIAL_BATCH01_IDS | LEGACY_BATCH01_EXTENSION_IDS

_BATCH01_FREE_TIER = frozenset({1, 2, 3, 4, 10, 21, 38, 39, 45})
_BATCH01_ALERTS = frozenset({60, 629, 245})
_BATCH01_MARKET = frozenset({47, 129, 214})
_BATCH01_DERIVATIVES = frozenset({48, 49})
_BATCH01_DATA = frozenset({630, 631})
_BATCH01_AI = frozenset({175, 34, 59, 642})
_BATCH01_ONCHAIN = frozenset({5})
_BATCH01_INSTITUTIONAL = frozenset({103, 644, 646})
_BATCH01_VERIFIED = frozenset({49})


from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch01_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch01(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch01_production"
    result["backend_entrypoint"] = batch01_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch01"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH01_IDS:
        raise ValueError(f"capability {capability_id} is not in batch01 production spine")

    params = dict(params or {})

    if capability_id in BATCH01_DEDICATED_IDS:
        from cap646.batch01_dedicated import execute as execute_dedicated

        result = await execute_dedicated(capability_id, params=params)
        return _stamp_batch01(result, capability_id)

    if capability_id in _BATCH01_FREE_TIER:
        from bd_platform.free_tier_capabilities import execute_free_tier_capability

        result = await execute_free_tier_capability(capability_id, params=params)
        return _stamp_batch01(result, capability_id)

    handler_fn: Callable[..., Awaitable[dict[str, Any]]]
    if capability_id in _BATCH01_ALERTS:
        from cap646.handlers.alerts import handle_alerts_capability

        handler_fn = handle_alerts_capability
    elif capability_id in _BATCH01_MARKET:
        from cap646.handlers.market import handle_market_capability

        handler_fn = handle_market_capability
    elif capability_id in _BATCH01_DERIVATIVES:
        from cap646.handlers.derivatives import handle_derivatives_capability

        handler_fn = handle_derivatives_capability
    elif capability_id in _BATCH01_DATA:
        from cap646.handlers.data import handle_data_capability

        handler_fn = handle_data_capability
    elif capability_id in _BATCH01_VERIFIED:
        from cap646.handlers.verified import handle_verified_capability

        handler_fn = handle_verified_capability
    elif capability_id in _BATCH01_AI:
        from cap646.handlers.ai import handle_ai_capability

        handler_fn = handle_ai_capability
    elif capability_id in _BATCH01_ONCHAIN:
        from cap646.handlers.onchain import handle_onchain_capability

        handler_fn = handle_onchain_capability
    elif capability_id in _BATCH01_INSTITUTIONAL:
        from cap646.handlers.institutional import handle_institutional_capability

        result = await handle_institutional_capability(capability_id, params=params)
        return _stamp_batch01(result, capability_id)
    else:
        raise ValueError(f"batch01: unmapped capability {capability_id}")

    result = await handler_fn(capability_id, params=params)
    return _stamp_batch01(result, capability_id)


def _make_cap_entrypoint(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _entry(*, params: dict[str, Any] | None = None, capability_id: int = capability_id) -> dict[str, Any]:
        return await execute(capability_id, params=params)

    _entry.__name__ = batch01_entrypoint(capability_id)
    _entry.__doc__ = f"Batch01 production entrypoint for capability #{capability_id}."
    return _entry


for _cid in BATCH01_IDS:
    globals()[batch01_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
