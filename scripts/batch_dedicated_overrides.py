#!/usr/bin/env python3
"""Custom dedicated handler overrides — survive batch_spine_factory regeneration (Run 021)."""
from __future__ import annotations

# cid -> (expected_surface, handler_source_without_leading_async)
_BATCH13_TAIL: dict[int, tuple[str, str]] = {
    647: (
        "real_time_feed",
        '''async def _cap647(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    """Path A — Pyth Hermes realtime feed (parity with free_tier #647)."""
    from bd_platform.free_tier_capabilities import pyth_realtime_feed

    symbol_clean = _sym(params)
    data = await pyth_realtime_feed(symbols=[symbol_clean])
    payload = {**data, "success": bool(data.get("feeds"))}
    return _wrap(647, symbol=symbol, payload_key="real_time_feed", payload=payload)''',
    ),
    648: (
        "datashare_connector",
        '''async def _cap648(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    # HEURISTIC — BigQuery datashare export not verifiable in local_dev_vm (Path B Run 021).
    from bd_platform.free_tier_capabilities import datashare_connector

    data = await datashare_connector()
    payload = {**data, "success": True, "probe_only": True}
    return _wrap(
        648,
        symbol=symbol,
        payload_key="datashare_connector",
        payload=payload,
        extra={
            "heuristic": True,
            "methodology_status": "NOT_COMPLETE",
            "methodology_reason": "datashare export readiness not verifiable in local_dev_vm",
        },
    )''',
    ),
    649: (
        "reserved_slot_649",
        '''async def _cap649(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    # HEURISTIC — reserved 826 inventory slot; no domain methodology bound (Path B Run 021).
    payload = {
        "heuristic": True,
        "methodology_status": "NOT_COMPLETE",
        "reserved_slot": True,
        "inventory_status": "PENDING",
        "success": True,
        "data_source": "826_inventory_reserved_slot",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return _wrap(
        649,
        symbol=symbol,
        payload_key="reserved_slot_649",
        payload=payload,
        extra={
            "heuristic": True,
            "methodology_status": "NOT_COMPLETE",
            "methodology_reason": "826 inventory reserved slot — Path B HEURISTIC",
        },
    )''',
    ),
    650: (
        "reserved_slot_650",
        '''async def _cap650(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    # HEURISTIC — reserved 826 inventory slot; no domain methodology bound (Path B Run 021).
    payload = {
        "heuristic": True,
        "methodology_status": "NOT_COMPLETE",
        "reserved_slot": True,
        "inventory_status": "PENDING",
        "success": True,
        "data_source": "826_inventory_reserved_slot",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return _wrap(
        650,
        symbol=symbol,
        payload_key="reserved_slot_650",
        payload=payload,
        extra={
            "heuristic": True,
            "methodology_status": "NOT_COMPLETE",
            "methodology_reason": "826 inventory reserved slot — Path B HEURISTIC",
        },
    )''',
    ),
}

BATCH_DEDICATED_OVERRIDES: dict[int, dict[int, tuple[str, str]]] = {
    13: _BATCH13_TAIL,
}


def overrides_for(batch_num: int) -> dict[int, tuple[str, str]]:
    return BATCH_DEDICATED_OVERRIDES.get(batch_num, {})
