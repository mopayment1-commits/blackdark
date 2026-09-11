"""Batch 08 prep dedicated backends — IDs 351–400 (Run 021)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.batch08_underlying import invoke_underlying
from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH08_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
OFFICIAL_BATCH08_IDS: frozenset[int] = frozenset(range(351, 401))
BATCH08_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH08_IDS

EXPECTED_SURFACE: dict[int, str] = {
    351: 'active_users',
    352: 'core_developers',
    353: 'code_commits',
    354: 'tvl_intelligence',
    355: 'borrowed_loans_outstanding',
    356: 'dex_volume',
    357: 'stablecoin_supply',
    358: 'valuation_multiples',
    359: 'growth_metrics',
    360: 'margins_take_rate',
    361: 'project_comparables',
    362: 'sector_comparables',
    363: 'tokenized_asset_coverage',
    364: 'fundamental_screener',
    365: 'financial_statement_view',
    366: 'data_methodology_registry',
    367: 'source_data_provenance',
    368: 'api_data_export',
    369: 'cross_fundamental_decision_intelligence',
    370: 'sql_on_chain_query_workspace',
    371: 'curated_data_models',
    372: 'decoded_smart_contract_tables',
    373: 'cross_chain_data_warehouse',
    374: 'visualization_builder',
    375: 'dashboard_builder',
    376: 'public_dashboard_sharing',
    377: 'community_discovery',
    378: 'query_forking',
    379: 'data_api',
    380: 'real_time_feed',
    381: 'datashare',
    382: 'dbt_connector',
    383: 'bi_connectors',
    384: 'mcp_for_ai_agents',
    385: 'prompt_to_sql_agent',
    386: 'dashboard_from_prompt',
    387: 'scheduled_queries',
    388: 'alerts_from_query_results',
    389: 'data_lineage',
    390: 'query_performance_governance',
    391: 'white_label_embedded_analytics',
    392: 'cross_domain_decision_layer',
    393: 'tvl_intelligence',
    394: 'chain_tvl_comparison',
    395: 'protocol_directory',
    396: 'fees_revenue',
    397: 'dex_volume',
    398: 'perps_volume',
    399: 'options_volume',
    400: 'stablecoins_intelligence',
}

_base_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _wrap(
    capability_id: int,
    *,
    symbol: str,
    payload_key: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Batch wrap — BCBS 239 top-level provenance."""
    merged: dict[str, Any] = dict(extra or {})
    if isinstance(payload, dict):
        src = payload.get("data_source") or payload.get("source")
        if src and not merged.get("data_source"):
            merged["data_source"] = src
        ts = payload.get("timestamp") or payload.get("attached_at")
        if ts and not merged.get("timestamp"):
            merged["timestamp"] = ts
    if not merged.get("data_source"):
        merged["data_source"] = f"cap646.batch08_dedicated#cap{capability_id:03d}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )


async def _cap351(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(351, params={**params, "symbol": symbol})
    return _wrap(351, symbol=symbol, payload_key="active_users", payload=payload)

async def _cap352(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(352, params={**params, "symbol": symbol})
    return _wrap(352, symbol=symbol, payload_key="core_developers", payload=payload)

async def _cap353(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(353, params={**params, "symbol": symbol})
    return _wrap(353, symbol=symbol, payload_key="code_commits", payload=payload)

async def _cap354(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(354, params={**params, "symbol": symbol})
    return _wrap(354, symbol=symbol, payload_key="tvl_intelligence", payload=payload)

async def _cap355(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(355, params={**params, "symbol": symbol})
    return _wrap(355, symbol=symbol, payload_key="borrowed_loans_outstanding", payload=payload)

async def _cap356(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(356, params={**params, "symbol": symbol})
    return _wrap(356, symbol=symbol, payload_key="dex_volume", payload=payload)

async def _cap357(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(357, params={**params, "symbol": symbol})
    return _wrap(357, symbol=symbol, payload_key="stablecoin_supply", payload=payload)

async def _cap358(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(358, params={**params, "symbol": symbol})
    return _wrap(358, symbol=symbol, payload_key="valuation_multiples", payload=payload)

async def _cap359(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(359, params={**params, "symbol": symbol})
    return _wrap(359, symbol=symbol, payload_key="growth_metrics", payload=payload)

async def _cap360(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(360, params={**params, "symbol": symbol})
    return _wrap(360, symbol=symbol, payload_key="margins_take_rate", payload=payload)

async def _cap361(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(361, params={**params, "symbol": symbol})
    return _wrap(361, symbol=symbol, payload_key="project_comparables", payload=payload)

async def _cap362(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(362, params={**params, "symbol": symbol})
    return _wrap(362, symbol=symbol, payload_key="sector_comparables", payload=payload)

async def _cap363(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(363, params={**params, "symbol": symbol})
    return _wrap(363, symbol=symbol, payload_key="tokenized_asset_coverage", payload=payload)

async def _cap364(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(364, params={**params, "symbol": symbol})
    return _wrap(364, symbol=symbol, payload_key="fundamental_screener", payload=payload)

async def _cap365(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(365, params={**params, "symbol": symbol})
    return _wrap(365, symbol=symbol, payload_key="financial_statement_view", payload=payload)

async def _cap366(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(366, params={**params, "symbol": symbol})
    return _wrap(366, symbol=symbol, payload_key="data_methodology_registry", payload=payload)

async def _cap367(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(367, params={**params, "symbol": symbol})
    return _wrap(367, symbol=symbol, payload_key="source_data_provenance", payload=payload)

async def _cap368(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(368, params={**params, "symbol": symbol})
    return _wrap(368, symbol=symbol, payload_key="api_data_export", payload=payload)

async def _cap369(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(369, params={**params, "symbol": symbol})
    return _wrap(369, symbol=symbol, payload_key="cross_fundamental_decision_intelligence", payload=payload)

async def _cap370(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(370, params={**params, "symbol": symbol})
    return _wrap(370, symbol=symbol, payload_key="sql_on_chain_query_workspace", payload=payload)

async def _cap371(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(371, params={**params, "symbol": symbol})
    return _wrap(371, symbol=symbol, payload_key="curated_data_models", payload=payload)

async def _cap372(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(372, params={**params, "symbol": symbol})
    return _wrap(372, symbol=symbol, payload_key="decoded_smart_contract_tables", payload=payload)

async def _cap373(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(373, params={**params, "symbol": symbol})
    return _wrap(373, symbol=symbol, payload_key="cross_chain_data_warehouse", payload=payload)

async def _cap374(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(374, params={**params, "symbol": symbol})
    return _wrap(374, symbol=symbol, payload_key="visualization_builder", payload=payload)

async def _cap375(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(375, params={**params, "symbol": symbol})
    return _wrap(375, symbol=symbol, payload_key="dashboard_builder", payload=payload)

async def _cap376(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(376, params={**params, "symbol": symbol})
    return _wrap(376, symbol=symbol, payload_key="public_dashboard_sharing", payload=payload)

async def _cap377(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(377, params={**params, "symbol": symbol})
    return _wrap(377, symbol=symbol, payload_key="community_discovery", payload=payload)

async def _cap378(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(378, params={**params, "symbol": symbol})
    return _wrap(378, symbol=symbol, payload_key="query_forking", payload=payload)

async def _cap379(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(379, params={**params, "symbol": symbol})
    return _wrap(379, symbol=symbol, payload_key="data_api", payload=payload)

async def _cap380(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(380, params={**params, "symbol": symbol})
    return _wrap(380, symbol=symbol, payload_key="real_time_feed", payload=payload)

async def _cap381(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(381, params={**params, "symbol": symbol})
    return _wrap(381, symbol=symbol, payload_key="datashare", payload=payload)

async def _cap382(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(382, params={**params, "symbol": symbol})
    return _wrap(382, symbol=symbol, payload_key="dbt_connector", payload=payload)

async def _cap383(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(383, params={**params, "symbol": symbol})
    return _wrap(383, symbol=symbol, payload_key="bi_connectors", payload=payload)

async def _cap384(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(384, params={**params, "symbol": symbol})
    return _wrap(384, symbol=symbol, payload_key="mcp_for_ai_agents", payload=payload)

async def _cap385(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(385, params={**params, "symbol": symbol})
    return _wrap(385, symbol=symbol, payload_key="prompt_to_sql_agent", payload=payload)

async def _cap386(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(386, params={**params, "symbol": symbol})
    return _wrap(386, symbol=symbol, payload_key="dashboard_from_prompt", payload=payload)

async def _cap387(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(387, params={**params, "symbol": symbol})
    return _wrap(387, symbol=symbol, payload_key="scheduled_queries", payload=payload)

async def _cap388(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(388, params={**params, "symbol": symbol})
    return _wrap(388, symbol=symbol, payload_key="alerts_from_query_results", payload=payload)

async def _cap389(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(389, params={**params, "symbol": symbol})
    return _wrap(389, symbol=symbol, payload_key="data_lineage", payload=payload)

async def _cap390(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(390, params={**params, "symbol": symbol})
    return _wrap(390, symbol=symbol, payload_key="query_performance_governance", payload=payload)

async def _cap391(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(391, params={**params, "symbol": symbol})
    return _wrap(391, symbol=symbol, payload_key="white_label_embedded_analytics", payload=payload)

async def _cap392(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(392, params={**params, "symbol": symbol})
    return _wrap(392, symbol=symbol, payload_key="cross_domain_decision_layer", payload=payload)

async def _cap393(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(393, params={**params, "symbol": symbol})
    return _wrap(393, symbol=symbol, payload_key="tvl_intelligence", payload=payload)

async def _cap394(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(394, params={**params, "symbol": symbol})
    return _wrap(394, symbol=symbol, payload_key="chain_tvl_comparison", payload=payload)

async def _cap395(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(395, params={**params, "symbol": symbol})
    return _wrap(395, symbol=symbol, payload_key="protocol_directory", payload=payload)

async def _cap396(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(396, params={**params, "symbol": symbol})
    return _wrap(396, symbol=symbol, payload_key="fees_revenue", payload=payload)

async def _cap397(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(397, params={**params, "symbol": symbol})
    return _wrap(397, symbol=symbol, payload_key="dex_volume", payload=payload)

async def _cap398(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(398, params={**params, "symbol": symbol})
    return _wrap(398, symbol=symbol, payload_key="perps_volume", payload=payload)

async def _cap399(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(399, params={**params, "symbol": symbol})
    return _wrap(399, symbol=symbol, payload_key="options_volume", payload=payload)

async def _cap400(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(400, params={**params, "symbol": symbol})
    return _wrap(400, symbol=symbol, payload_key="stablecoins_intelligence", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    351: _cap351,
    352: _cap352,
    353: _cap353,
    354: _cap354,
    355: _cap355,
    356: _cap356,
    357: _cap357,
    358: _cap358,
    359: _cap359,
    360: _cap360,
    361: _cap361,
    362: _cap362,
    363: _cap363,
    364: _cap364,
    365: _cap365,
    366: _cap366,
    367: _cap367,
    368: _cap368,
    369: _cap369,
    370: _cap370,
    371: _cap371,
    372: _cap372,
    373: _cap373,
    374: _cap374,
    375: _cap375,
    376: _cap376,
    377: _cap377,
    378: _cap378,
    379: _cap379,
    380: _cap380,
    381: _cap381,
    382: _cap382,
    383: _cap383,
    384: _cap384,
    385: _cap385,
    386: _cap386,
    387: _cap387,
    388: _cap388,
    389: _cap389,
    390: _cap390,
    391: _cap391,
    392: _cap392,
    393: _cap393,
    394: _cap394,
    395: _cap395,
    396: _cap396,
    397: _cap397,
    398: _cap398,
    399: _cap399,
    400: _cap400,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH08_DEDICATED_IDS,
        overlap_batch01_ids=BATCH08_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch08: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in batch08 dedicated set",
    )
