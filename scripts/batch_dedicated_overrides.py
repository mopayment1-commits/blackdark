#!/usr/bin/env python3
"""Custom dedicated handler overrides — survive batch_spine_factory regeneration (Run 021)."""
from __future__ import annotations

# cid -> (expected_surface, handler_source)
_BATCH04_FREE_TIER: dict[int, tuple[str, str]] = {
    196: (
        "realized_cap_realized_value_intelligence",
        '''async def _cap196(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    """Path A — free_tier realized_cap_metrics parity (SPLIT-BRAIN fix Run 826)."""
    from bd_platform.free_tier_capabilities import realized_cap_metrics

    _sym = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    _raw = await realized_cap_metrics(symbol=_sym)
    payload = dict(_raw)
    return _wrap(
        196,
        symbol=symbol,
        payload_key="realized_cap_realized_value_intelligence",
        payload=payload,
        extra={
            "methodology": {
                "framework": "Path A — explicit free_tier parity (v6 §2.1)",
                "implementation": "bd_platform.free_tier_capabilities.realized_cap_metrics",
                "methodology_status": "DOCUMENTED",
                "binding_source_resolved": "free_tier_explicit",
            },
        },
    )''',
    ),
}

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


def _free_tier_execute_handler(cid: int, surface: str) -> str:
    return f'''async def _cap{cid:03d}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    """Path A — free_tier execute parity (SPLIT-BRAIN fix Run 826)."""
    from bd_platform.free_tier_capabilities import execute_free_tier_capability

    ft = await execute_free_tier_capability({cid}, params={{**params, "symbol": symbol, "address": address}})
    payload = dict(ft.get("data") or {{}})
    return _wrap(
        {cid},
        symbol=symbol,
        payload_key="{surface}",
        payload=payload,
        extra={{
            "methodology": {{
                "framework": "Path A — explicit free_tier parity (v6 §2.1)",
                "implementation": "bd_platform.free_tier_capabilities.execute_free_tier_capability",
                "methodology_status": "DOCUMENTED",
                "binding_source_resolved": "free_tier_explicit",
            }},
        }},
    )'''


_FREE_TIER_EXTENSION_SURFACES: dict[int, str] = {
    652: "prompt_to_sql_agent",
    672: "liquid_staking_intelligence",
    673: "rwa_intelligence",
    674: "raises_funding_rounds",
    675: "investor_profiles",
    676: "unlocks",
    690: "bloomberg_terminal_bridge_proxy",
    691: "refinitiv_eikon_bridge_proxy",
    702: "kaiko_institutional_proxy",
    703: "amberdata_institutional_proxy",
    704: "defi_risk_radar",
    705: "lending_market_risk",
}

_BATCH14_FREE_TIER: dict[int, tuple[str, str]] = {
    cid: (_FREE_TIER_EXTENSION_SURFACES[cid], _free_tier_execute_handler(cid, _FREE_TIER_EXTENSION_SURFACES[cid]))
    for cid in (652, 672, 673, 674, 675, 676, 690, 691)
}

_BATCH15_FREE_TIER: dict[int, tuple[str, str]] = {
    cid: (_FREE_TIER_EXTENSION_SURFACES[cid], _free_tier_execute_handler(cid, _FREE_TIER_EXTENSION_SURFACES[cid]))
    for cid in (702, 703, 704, 705)
}

BATCH_DEDICATED_OVERRIDES: dict[int, dict[int, tuple[str, str]]] = {
    4: _BATCH04_FREE_TIER,
    13: _BATCH13_TAIL,
    14: _BATCH14_FREE_TIER,
    15: _BATCH15_FREE_TIER,
}


def overrides_for(batch_num: int) -> dict[int, tuple[str, str]]:
    return BATCH_DEDICATED_OVERRIDES.get(batch_num, {})
