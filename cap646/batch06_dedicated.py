"""Batch 06 dedicated backends — catalog-aligned payloads for IDs 251–300."""

from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

from cap646.batch06_ids import BATCH06_IDS, BATCH06_MANIFEST_IDS
from cap646.dedicated_common import execute_dedicated_caps, make_wrap_binding, seed as _seed

BATCH06_REUSED_LINK_BATCH02_IDS: frozenset[int] = frozenset({251, 256, 275})
BATCH06_REUSED_LINK_BATCH03_IDS: frozenset[int] = frozenset({260})
BATCH06_REUSED_LINK_BATCH05_IDS: frozenset[int] = frozenset({255, 257, 259, 261, 272, 291, 292})
BATCH06_REUSED_LINK_IDS: frozenset[int] = (
    BATCH06_REUSED_LINK_BATCH02_IDS | BATCH06_REUSED_LINK_BATCH03_IDS | BATCH06_REUSED_LINK_BATCH05_IDS
)

EXPECTED_SURFACE: dict[int, str] = {
    251: "cross_domain_decision_intelligence",
    252: "liquidation_heatmap",
    253: "liquidation_map_levels",
    254: "real_time_liquidation_events",
    255: "open_interest_intelligence",
    256: "funding_rate_intelligence",
    257: "long_short_ratio_intelligence",
    258: "top_trader_positioning",
    259: "futures_basis_intelligence",
    260: "futures_volume_intelligence",
    261: "futures_cvd_taker_flow",
    262: "options_open_interest",
    263: "options_volume",
    264: "options_iv_skew",
    265: "max_pain_gamma_context",
    266: "spot_market_intelligence",
    267: "order_book_market_depth",
    268: "historical_derivatives_data",
    269: "exchange_comparison",
    270: "liquidation_cascade_proximity",
    271: "leverage_pressure_score",
    272: "api_data_platform",
    273: "multi_model_liquidation_comparison",
    274: "derivatives_alerts",
    275: "cross_domain_decision_intelligence",
    276: "entity_resolution_engine",
    277: "address_labeling_system",
    278: "entity_profiles",
    279: "transaction_search",
    280: "portfolio_holdings",
    281: "balance_history",
    282: "entity_pnl",
    283: "exchange_usage_intelligence",
    284: "top_counterparties",
    285: "network_graph_visualizer",
    286: "automated_trace_path_finding",
    287: "cross_chain_trace",
    288: "token_top_holders",
    289: "token_exchange_flows",
    290: "token_transaction_explorer",
    291: "custom_dashboards",
    292: "custom_alerts",
    293: "private_labels",
    294: "portfolio_archive_snapshot",
    295: "ai_market_insights",
    296: "whale_movement_intelligence",
    297: "fraud_suspicious_activity",
    298: "api_onchain_intelligence",
    299: "cross_entity_decision_intelligence",
    300: "advanced_multi_asset_charting",
}

_REUSED_LINK_CATALOG: dict[int, dict[str, Any]] = {
    251: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 69,
        "canonical_spine": "batch02",
        "binding": "cap646/batch02_production.py::cap_069",
    },
    255: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 205,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_open_interest_205",
    },
    256: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 86,
        "canonical_spine": "batch02",
        "binding": "cap646/batch02_production.py::cap_086",
    },
    257: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 235,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_long_short_ratio_intelligence_235",
    },
    259: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 231,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_futures_basis_term_structure_231",
    },
    260: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 126,
        "canonical_spine": "batch03",
        "binding": "cap646/batch03_dedicated.py::_cap126",
    },
    261: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 234,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_cvd_intelligence_234",
    },
    272: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 247,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_public_rest_api_247",
    },
    275: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 69,
        "canonical_spine": "batch02",
        "binding": "cap646/batch02_production.py::cap_069",
        "alias_of": 251,
    },
    291: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 210,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_custom_dashboards_layouts_210",
    },
    292: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 213,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_strangler_spine.py::build_anomaly_detection_alerts_213",
    },
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)


_REUSED_SOURCE_KEY: dict[int, str] = {
    259: "futures_basis_term_structure",
    260: "futures_volume",
    261: "cvd_intelligence",
    272: "public_rest_api",
    291: "custom_dashboards_layouts",
    292: "anomaly_detection_alerts",
}


def _stamp_reused_link(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    link = dict(_REUSED_LINK_CATALOG[capability_id])
    result["catalog_link"] = link
    result["classification"] = "REUSED-LINK"
    result["capability_id"] = capability_id
    result["closure_status"] = "REUSED-LINK"
    target = EXPECTED_SURFACE[capability_id]
    source = _REUSED_SOURCE_KEY.get(capability_id, target)
    if source in result and isinstance(result.get(source), dict):
        result[target] = result[source]
    elif target not in result:
        for key, val in result.items():
            if isinstance(val, dict) and ("ok" in val or "feature_ref" in val):
                result[target] = val
                break
    result["surface"] = target
    return result


async def _cap251(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_production import execute as execute_batch02

    result = await execute_batch02(69, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 251)


async def _cap275(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    result = await _cap251(symbol=symbol, address=address, params=params)
    return _stamp_reused_link(result, 275)


async def _cap255(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(205, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 255)


async def _cap256(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_production import execute as execute_batch02

    result = await execute_batch02(86, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 256)


async def _cap257(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(235, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 257)


async def _cap259(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(231, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 259)


async def _cap260(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_production import execute as execute_batch03

    result = await execute_batch03(126, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 260)


async def _cap261(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(234, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 261)


async def _cap272(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(247, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 272)


async def _cap291(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(210, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 291)


async def _cap292(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_production import execute as execute_batch05

    result = await execute_batch05(213, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 292)


def _make_strangler_handler(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _handler(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
        from cap646.batch06_strangler_spine import STRANGLER_BUILDERS

        builder = STRANGLER_BUILDERS[capability_id]
        sig = inspect.signature(builder)
        kwargs: dict[str, Any] = {"symbol": symbol, "params": params}
        if "seed" in sig.parameters:
            kwargs["seed"] = _seed()
        payload = await builder(**kwargs)
        root = EXPECTED_SURFACE[capability_id]
        return _wrap(
            capability_id,
            symbol=symbol,
            payload_key=root,
            payload=payload,
            extra={"closure_status": "NOT_COMPLETE", "miswire_remediation": "STRANGLER_IMPLEMENTED"},
        )

    _handler.__name__ = f"_cap{capability_id}"
    return _handler


from cap646.batch06_strangler_spine import STRANGLER_BUILDERS

_STRANGLER_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    cid: _make_strangler_handler(cid) for cid in sorted(STRANGLER_BUILDERS)
}

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    251: _cap251,
    255: _cap255,
    256: _cap256,
    257: _cap257,
    259: _cap259,
    260: _cap260,
    261: _cap261,
    272: _cap272,
    275: _cap275,
    291: _cap291,
    292: _cap292,
    **_STRANGLER_DISPATCH,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH06_DEDICATED_IDS,
        overlap_batch01_ids=frozenset(),
        dispatch=_DISPATCH,
        overlap_error=f"capability {capability_id} has no batch06 overlap error path",
        not_dedicated_error=f"capability {capability_id} is not in batch06 dedicated spine",
    )


# Re-export for generators/tests
BATCH06_DEDICATED_IDS = BATCH06_IDS
