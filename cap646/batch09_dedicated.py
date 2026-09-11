"""Batch 09 prep dedicated backends — IDs 401–450 (Run 021)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.batch09_underlying import invoke_underlying
from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH09_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
OFFICIAL_BATCH09_IDS: frozenset[int] = frozenset(range(401, 451))
BATCH09_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH09_IDS

EXPECTED_SURFACE: dict[int, str] = {
    401: 'bridges_intelligence',
    402: 'yields_screener',
    403: 'yield_history',
    404: 'borrowing_rates',
    405: 'liquid_staking_intelligence',
    406: 'rwa_intelligence',
    407: 'raises_funding_rounds',
    408: 'investor_profiles',
    409: 'unlocks',
    410: 'treasury_intelligence',
    411: 'airdrop_incentive_intelligence',
    412: 'capital_formation_radar',
    413: 'defi_opportunity_screener',
    414: 'defi_risk_passport',
    415: 'api_aggregation_layer',
    416: 'cross_defi_decision_intelligence',
    417: 'cross_chain_fundamentals',
    418: 'protocol_fundamentals',
    419: 'stablecoin_intelligence',
    420: 'stablecoin_activity_breakdown',
    421: 'developer_activity',
    422: 'sector_ecosystem_comparables',
    423: 'equities_crypto_research',
    424: 'consensus_estimates',
    425: 'ai_analyst',
    426: 'thesis_research_workspace',
    427: 'comparable_company_protocol_analysis',
    428: 'excel_sheets_integration',
    429: 'api_data_platform',
    430: 'research_templates',
    431: 'dashboards',
    432: 'stablecoin_payment_intelligence',
    433: 'on_chain_usage_intelligence',
    434: 'revenue_fees_economic_activity',
    435: 'cross_market_research_copilot',
    436: 'investment_thesis_scoring',
    437: 'defi_risk_radar',
    438: 'lending_market_risk',
    439: 'collateral_risk',
    440: 'liquidation_risk',
    441: 'oracle_risk',
    442: 'liquidity_risk',
    443: 'protocol_exploit_intelligence',
    444: 'stablecoin_risk_intelligence',
    445: 'defi_strategy_risk',
    446: 'real_time_risk_alerts',
    447: 'dao_treasury_risk',
    448: 'institutional_risk_api',
    449: 'curated_on_chain_dashboards',
    450: 'narrative_driven_research',
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
        merged["data_source"] = f"cap646.batch09_dedicated#cap{capability_id:03d}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )


async def _cap401(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(401, params={**params, "symbol": symbol})
    return _wrap(401, symbol=symbol, payload_key="bridges_intelligence", payload=payload)

async def _cap402(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(402, params={**params, "symbol": symbol})
    return _wrap(402, symbol=symbol, payload_key="yields_screener", payload=payload)

async def _cap403(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(403, params={**params, "symbol": symbol})
    return _wrap(403, symbol=symbol, payload_key="yield_history", payload=payload)

async def _cap404(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(404, params={**params, "symbol": symbol})
    return _wrap(404, symbol=symbol, payload_key="borrowing_rates", payload=payload)

async def _cap405(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(405, params={**params, "symbol": symbol})
    return _wrap(405, symbol=symbol, payload_key="liquid_staking_intelligence", payload=payload)

async def _cap406(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(406, params={**params, "symbol": symbol})
    return _wrap(406, symbol=symbol, payload_key="rwa_intelligence", payload=payload)

async def _cap407(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(407, params={**params, "symbol": symbol})
    return _wrap(407, symbol=symbol, payload_key="raises_funding_rounds", payload=payload)

async def _cap408(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(408, params={**params, "symbol": symbol})
    return _wrap(408, symbol=symbol, payload_key="investor_profiles", payload=payload)

async def _cap409(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(409, params={**params, "symbol": symbol})
    return _wrap(409, symbol=symbol, payload_key="unlocks", payload=payload)

async def _cap410(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(410, params={**params, "symbol": symbol})
    return _wrap(410, symbol=symbol, payload_key="treasury_intelligence", payload=payload)

async def _cap411(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(411, params={**params, "symbol": symbol})
    return _wrap(411, symbol=symbol, payload_key="airdrop_incentive_intelligence", payload=payload)

async def _cap412(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(412, params={**params, "symbol": symbol})
    return _wrap(412, symbol=symbol, payload_key="capital_formation_radar", payload=payload)

async def _cap413(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(413, params={**params, "symbol": symbol})
    return _wrap(413, symbol=symbol, payload_key="defi_opportunity_screener", payload=payload)

async def _cap414(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(414, params={**params, "symbol": symbol})
    return _wrap(414, symbol=symbol, payload_key="defi_risk_passport", payload=payload)

async def _cap415(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(415, params={**params, "symbol": symbol})
    return _wrap(415, symbol=symbol, payload_key="api_aggregation_layer", payload=payload)

async def _cap416(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(416, params={**params, "symbol": symbol})
    return _wrap(416, symbol=symbol, payload_key="cross_defi_decision_intelligence", payload=payload)

async def _cap417(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(417, params={**params, "symbol": symbol})
    return _wrap(417, symbol=symbol, payload_key="cross_chain_fundamentals", payload=payload)

async def _cap418(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(418, params={**params, "symbol": symbol})
    return _wrap(418, symbol=symbol, payload_key="protocol_fundamentals", payload=payload)

async def _cap419(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(419, params={**params, "symbol": symbol})
    return _wrap(419, symbol=symbol, payload_key="stablecoin_intelligence", payload=payload)

async def _cap420(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(420, params={**params, "symbol": symbol})
    return _wrap(420, symbol=symbol, payload_key="stablecoin_activity_breakdown", payload=payload)

async def _cap421(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(421, params={**params, "symbol": symbol})
    return _wrap(421, symbol=symbol, payload_key="developer_activity", payload=payload)

async def _cap422(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(422, params={**params, "symbol": symbol})
    return _wrap(422, symbol=symbol, payload_key="sector_ecosystem_comparables", payload=payload)

async def _cap423(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(423, params={**params, "symbol": symbol})
    return _wrap(423, symbol=symbol, payload_key="equities_crypto_research", payload=payload)

async def _cap424(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(424, params={**params, "symbol": symbol})
    return _wrap(424, symbol=symbol, payload_key="consensus_estimates", payload=payload)

async def _cap425(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(425, params={**params, "symbol": symbol})
    return _wrap(425, symbol=symbol, payload_key="ai_analyst", payload=payload)

async def _cap426(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(426, params={**params, "symbol": symbol})
    return _wrap(426, symbol=symbol, payload_key="thesis_research_workspace", payload=payload)

async def _cap427(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(427, params={**params, "symbol": symbol})
    return _wrap(427, symbol=symbol, payload_key="comparable_company_protocol_analysis", payload=payload)

async def _cap428(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(428, params={**params, "symbol": symbol})
    return _wrap(428, symbol=symbol, payload_key="excel_sheets_integration", payload=payload)

async def _cap429(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(429, params={**params, "symbol": symbol})
    return _wrap(429, symbol=symbol, payload_key="api_data_platform", payload=payload)

async def _cap430(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(430, params={**params, "symbol": symbol})
    return _wrap(430, symbol=symbol, payload_key="research_templates", payload=payload)

async def _cap431(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(431, params={**params, "symbol": symbol})
    return _wrap(431, symbol=symbol, payload_key="dashboards", payload=payload)

async def _cap432(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(432, params={**params, "symbol": symbol})
    return _wrap(432, symbol=symbol, payload_key="stablecoin_payment_intelligence", payload=payload)

async def _cap433(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(433, params={**params, "symbol": symbol})
    return _wrap(433, symbol=symbol, payload_key="on_chain_usage_intelligence", payload=payload)

async def _cap434(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(434, params={**params, "symbol": symbol})
    return _wrap(434, symbol=symbol, payload_key="revenue_fees_economic_activity", payload=payload)

async def _cap435(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(435, params={**params, "symbol": symbol})
    return _wrap(435, symbol=symbol, payload_key="cross_market_research_copilot", payload=payload)

async def _cap436(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(436, params={**params, "symbol": symbol})
    return _wrap(436, symbol=symbol, payload_key="investment_thesis_scoring", payload=payload)

async def _cap437(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(437, params={**params, "symbol": symbol})
    return _wrap(437, symbol=symbol, payload_key="defi_risk_radar", payload=payload)

async def _cap438(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(438, params={**params, "symbol": symbol})
    return _wrap(438, symbol=symbol, payload_key="lending_market_risk", payload=payload)

async def _cap439(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(439, params={**params, "symbol": symbol})
    return _wrap(439, symbol=symbol, payload_key="collateral_risk", payload=payload)

async def _cap440(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(440, params={**params, "symbol": symbol})
    return _wrap(440, symbol=symbol, payload_key="liquidation_risk", payload=payload)

async def _cap441(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(441, params={**params, "symbol": symbol})
    return _wrap(441, symbol=symbol, payload_key="oracle_risk", payload=payload)

async def _cap442(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(442, params={**params, "symbol": symbol})
    return _wrap(442, symbol=symbol, payload_key="liquidity_risk", payload=payload)

async def _cap443(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(443, params={**params, "symbol": symbol})
    return _wrap(443, symbol=symbol, payload_key="protocol_exploit_intelligence", payload=payload)

async def _cap444(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(444, params={**params, "symbol": symbol})
    return _wrap(444, symbol=symbol, payload_key="stablecoin_risk_intelligence", payload=payload)

async def _cap445(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(445, params={**params, "symbol": symbol})
    return _wrap(445, symbol=symbol, payload_key="defi_strategy_risk", payload=payload)

async def _cap446(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(446, params={**params, "symbol": symbol})
    return _wrap(446, symbol=symbol, payload_key="real_time_risk_alerts", payload=payload)

async def _cap447(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(447, params={**params, "symbol": symbol})
    return _wrap(447, symbol=symbol, payload_key="dao_treasury_risk", payload=payload)

async def _cap448(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(448, params={**params, "symbol": symbol})
    return _wrap(448, symbol=symbol, payload_key="institutional_risk_api", payload=payload)

async def _cap449(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(449, params={**params, "symbol": symbol})
    return _wrap(449, symbol=symbol, payload_key="curated_on_chain_dashboards", payload=payload)

async def _cap450(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(450, params={**params, "symbol": symbol})
    return _wrap(450, symbol=symbol, payload_key="narrative_driven_research", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    401: _cap401,
    402: _cap402,
    403: _cap403,
    404: _cap404,
    405: _cap405,
    406: _cap406,
    407: _cap407,
    408: _cap408,
    409: _cap409,
    410: _cap410,
    411: _cap411,
    412: _cap412,
    413: _cap413,
    414: _cap414,
    415: _cap415,
    416: _cap416,
    417: _cap417,
    418: _cap418,
    419: _cap419,
    420: _cap420,
    421: _cap421,
    422: _cap422,
    423: _cap423,
    424: _cap424,
    425: _cap425,
    426: _cap426,
    427: _cap427,
    428: _cap428,
    429: _cap429,
    430: _cap430,
    431: _cap431,
    432: _cap432,
    433: _cap433,
    434: _cap434,
    435: _cap435,
    436: _cap436,
    437: _cap437,
    438: _cap438,
    439: _cap439,
    440: _cap440,
    441: _cap441,
    442: _cap442,
    443: _cap443,
    444: _cap444,
    445: _cap445,
    446: _cap446,
    447: _cap447,
    448: _cap448,
    449: _cap449,
    450: _cap450,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH09_DEDICATED_IDS,
        overlap_batch01_ids=BATCH09_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch09: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in batch09 dedicated set",
    )
