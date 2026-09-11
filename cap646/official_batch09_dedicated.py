"""Official batch 09 — from-scratch dedicated backends (IDs 201–225)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH09_IDS: frozenset[int] = frozenset(range(201, 226))
BATCH09_DEDICATED_IDS: frozenset[int] = frozenset({201, 202, 203, 204, 205, 207, 208, 209, 210, 211, 213, 214, 215, 216, 217, 218, 219, 220, 223, 224, 225})
BATCH09_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    201: "network_growth_intelligence",
    202: "supply_distribution_intelligence",
    203: "dex_trading_intelligence",
    204: "defi_protocol_activity_intelligence",
    205: "open_interest_intelligence",
    207: "price_volume_market_metrics",
    208: "metric_correlation_workbench",
    209: "custom_chart_builder",
    210: "custom_dashboards_layouts",
    211: "screener",
    213: "anomaly_detection_alerts",
    214: "watchlists",
    215: "community_explorer",
    216: "research_market_insights",
    217: "sanapi_style_data_access",
    218: "google_sheets_integration",
    219: "metric_availability_registry",
    220: "data_stabilization_mutability_metadata",
    223: "social_to_on_chain_confirmation_engine",
    224: "narrative_actionability_score",
    225: "development_to_market_divergence_detector",
}

async def _cap201(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap201 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap202(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap202 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap203(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap203 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap204(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap204 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap205(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap205 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap207(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap207 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap208(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap208 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap209(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap209 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap210(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap210 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap211(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap211 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap213(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap213 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap214(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap214 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap215(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap215 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap216(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap216 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap217(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap217 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap218(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap218 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap219(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap219 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap220(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap220 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap223(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap223 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap224(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap224 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap225(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch09_dedicated import _cap225 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    201: _cap201,
    202: _cap202,
    203: _cap203,
    204: _cap204,
    205: _cap205,
    207: _cap207,
    208: _cap208,
    209: _cap209,
    210: _cap210,
    211: _cap211,
    213: _cap213,
    214: _cap214,
    215: _cap215,
    216: _cap216,
    217: _cap217,
    218: _cap218,
    219: _cap219,
    220: _cap220,
    223: _cap223,
    224: _cap224,
    225: _cap225,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH09_DEDICATED_IDS,
        overlap_batch01_ids=BATCH09_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch09",
        not_dedicated_error=f"official batch09: not dedicated",
    )
