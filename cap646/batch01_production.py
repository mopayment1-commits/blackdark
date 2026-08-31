"""Batch 01 — canonical production spine for 826-completion (IDs 1–59, 50 capabilities).

Single source of truth for institutional Option A wiring. Handlers delegate here;
``backend_registry`` explicit bindings point to ``cap_XXX`` entrypoints in this module.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH01_IDS: frozenset[int] = frozenset(
    {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        10,
        11,
        12,
        13,
        14,
        17,
        18,
        19,
        20,
        21,
        22,
        25,
        27,
        28,
        29,
        30,
        33,
        34,
        36,
        37,
        40,
        44,
        45,
        46,
        47,
        48,
        49,
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

_BATCH01_FREE_TIER = frozenset({1, 2, 3, 4, 10, 21, 45})
_BATCH01_ALERTS = frozenset({17, 60, 629, 245})
_BATCH01_MARKET = frozenset({47, 129, 214, 29, 46})
_BATCH01_DERIVATIVES = frozenset({48, 49})
_BATCH01_DATA = frozenset({630, 631})
_BATCH01_AI = frozenset({175, 25, 30, 34, 59, 642})
_BATCH01_ONCHAIN = frozenset({5, 6, 7, 11, 12, 13, 14, 18, 19, 20, 22, 27, 28, 36, 37, 44, 55})
_BATCH01_INSTITUTIONAL = frozenset({103, 644, 646})
_BATCH01_DEDICATED = frozenset({33, 40, 56, 584})


from cap646.evidence_class import ai_compliance_footer


def batch01_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch01(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.batch01_production"
    result["backend_entrypoint"] = batch01_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "batch01"
    return result


async def _execute_dedicated(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or "BTC").upper().replace("/USDT", "")

    if capability_id == 33:
        from whale_tracker import get_latest_whale_alerts

        alerts = await get_latest_whale_alerts(limit=10)
        score = min(100.0, max(0.0, len(alerts) * 12.5))
        return ai_compliance_footer(
            {
                "capability_id": 33,
                "surface": "smart_money_actionability_score",
                "alerts": alerts,
                "actionability_score": score,
                "success": True,
            }
        )

    if capability_id == 40:
        from bd_platform.onchain_hub import lookintobitcoin_macro

        macro = await lookintobitcoin_macro()
        return ai_compliance_footer(
            {
                "capability_id": 40,
                "surface": "mvrv_mvrv_z_score_suite",
                "macro": macro,
                "success": bool(macro),
            }
        )

    if capability_id == 56:
        from bd_platform.market_rankings import market_rankings

        rankings = await market_rankings()
        return ai_compliance_footer(
            {
                "capability_id": 56,
                "surface": "token_screener",
                "screener": rankings,
                "success": bool(rankings),
            }
        )

    if capability_id == 584:
        from risk_manager import risk_status

        status = risk_status()
        return ai_compliance_footer(
            {
                "capability_id": 584,
                "surface": "risk_management_shield",
                "risk": status,
                "success": bool(status),
            }
        )

    raise ValueError(f"batch01 dedicated: unmapped capability {capability_id}")


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH01_IDS:
        raise ValueError(f"capability {capability_id} is not in batch01 production spine")

    params = dict(params or {})

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
    elif capability_id in _BATCH01_DEDICATED:
        result = await _execute_dedicated(capability_id, params=params)
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
