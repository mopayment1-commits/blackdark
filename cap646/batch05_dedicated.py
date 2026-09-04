"""Batch 05 dedicated backends — catalog-aligned payloads for IDs 201–250.

Overlap facades (REUSED-LINK, no parallel implementation):
- #214/#245 → batch01 (``BATCH05_MECE_OVERLAP_214_245_DECISION.json``)
- #206/#228 → batch02 #86 (``BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json``)
- #232 → batch05 canonical #205 (same decision doc)
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import seed as _seed

BATCH05_REUSED_LINK_BATCH01_IDS: frozenset[int] = frozenset({214, 245})
BATCH05_REUSED_LINK_BATCH02_IDS: frozenset[int] = frozenset({206, 228})
BATCH05_REUSED_LINK_INTERNAL_IDS: frozenset[int] = frozenset({232})
BATCH05_REUSED_LINK_IDS: frozenset[int] = (
    BATCH05_REUSED_LINK_BATCH01_IDS | BATCH05_REUSED_LINK_BATCH02_IDS | BATCH05_REUSED_LINK_INTERNAL_IDS
)
BATCH05_DEDICATED_IDS: frozenset[int] = frozenset(range(201, 251))

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)

EXPECTED_SURFACE: dict[int, str] = {
    201: "network_growth_intelligence",
    202: "supply_distribution_intelligence",
    203: "dex_trading_intelligence",
    204: "defi_protocol_activity_intelligence",
    205: "open_interest_intelligence",
    206: "funding_rate_intelligence",
    207: "price_volume_market_metrics",
    208: "metric_correlation_workbench",
    209: "custom_chart_builder",
    210: "custom_dashboards_layouts",
    211: "screener",
    212: "smart_alerts",
    213: "anomaly_detection_alerts",
    214: "watchlists",
    215: "community_explorer",
    216: "research_market_insights",
    217: "sanapi_style_data_access",
    218: "google_sheets_integration",
    219: "metric_availability_registry",
    220: "data_stabilization_mutability_metadata",
    221: "data_quality_provenance_layer",
    222: "metric_methodology_registry",
    223: "social_to_on_chain_confirmation_engine",
    224: "narrative_actionability_score",
    225: "development_to_market_divergence_detector",
    226: "cross_domain_decision_intelligence_layer",
    227: "unified_trading_intelligence_workspace",
    228: "funding_rate_intelligence",
    229: "cross_exchange_funding_arbitrage_scanner",
    230: "spot_perp_arbitrage_scanner",
    231: "futures_basis_term_structure",
    232: "open_interest_intelligence",
    233: "liquidation_intelligence",
    234: "cvd_intelligence",
    235: "long_short_ratio_intelligence",
    236: "dex_screener",
    237: "token_risk_scoring",
    238: "pump_dump_detection",
    239: "narrative_tracking",
    240: "sector_rotation_intelligence",
    241: "sentiment_intelligence",
    242: "price_prediction_multi_signal_forecast",
    243: "correlation_matrix",
    244: "new_listings_intelligence",
    245: "real_time_data_freshness_update_assurance",
    246: "coverage_metadata_registry",
    247: "public_rest_api",
    248: "mcp_server_for_ai_agents",
    249: "cli_access",
    250: "openapi_sdk_generation",
}

_REUSED_LINK_CATALOG: dict[int, dict[str, Any]] = {
    214: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 214,
        "canonical_spine": "batch01",
        "binding": "cap646/batch01_dedicated.py::_cap214_watchlists",
    },
    245: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 245,
        "canonical_spine": "batch01",
        "binding": "cap646/batch01_production.py::cap_245",
    },
    206: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 86,
        "canonical_spine": "batch02",
        "binding": "cap646/batch02_production.py::cap_086",
    },
    228: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 86,
        "canonical_spine": "batch02",
        "binding": "cap646/batch02_production.py::cap_086",
    },
    232: {
        "classification": "REUSED-LINK",
        "canonical_capability_id": 205,
        "canonical_spine": "batch05",
        "binding": "cap646/batch05_dedicated.py::_cap205",
    },
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _stamp_reused_link(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    link = dict(_REUSED_LINK_CATALOG[capability_id])
    result["catalog_link"] = link
    result["classification"] = "REUSED-LINK"
    result["capability_id"] = capability_id
    result["closure_status"] = "REUSED-LINK"
    return result


async def _cap214(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap214_watchlists

    result = await _cap214_watchlists(symbol=symbol, address=address, params=params)
    return _stamp_reused_link(result, 214)


async def _cap245(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_production import execute as execute_batch01

    result = await execute_batch01(245, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 245)


async def _cap205(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await _cap_hero_bridge(205, symbol=symbol, address=address, params=params)


async def _cap206(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_production import execute as execute_batch02

    result = await execute_batch02(86, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 206)


async def _cap228(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_production import execute as execute_batch02

    result = await execute_batch02(86, params={**params, "symbol": symbol, "address": address})
    return _stamp_reused_link(result, 228)


async def _cap232(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    result = await _cap205(symbol=symbol, address=address, params=params)
    return _stamp_reused_link(result, 232)


async def _cap_hero_bridge(capability_id: int, *, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch05_hero_bridge import build_hero_payload

    payload = build_hero_payload(capability_id, symbol=symbol, params=params, seed=_seed())
    root = EXPECTED_SURFACE[capability_id]
    return _wrap(
        capability_id,
        symbol=symbol,
        payload_key=root,
        payload=payload,
        extra={"closure_status": "NOT_COMPLETE", "pre_probe": True},
    )


def _make_hero_handler(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _handler(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
        return await _cap_hero_bridge(capability_id, symbol=symbol, address=address, params=params)

    _handler.__name__ = f"_cap{capability_id}"
    return _handler


from cap646.batch05_hero_bridge import hero_binding_ids

_HERO_IDS = hero_binding_ids()

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    205: _cap205,
    206: _cap206,
    214: _cap214,
    228: _cap228,
    232: _cap232,
    245: _cap245,
    **{cid: _make_hero_handler(cid) for cid in sorted(_HERO_IDS - BATCH05_REUSED_LINK_IDS - {205})},
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH05_DEDICATED_IDS,
        overlap_batch01_ids=frozenset(),
        dispatch=_DISPATCH,
        overlap_error=f"capability {capability_id} has no batch05 overlap error path",
        not_dedicated_error=f"capability {capability_id} is not in batch05 dedicated spine",
    )
