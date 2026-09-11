"""Batch 04 prep dedicated backends — IDs 151–200 (Run 011 opening)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.batch04_underlying import invoke_underlying
from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH04_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()  # 175 resolved Run 011
OFFICIAL_BATCH04_IDS: frozenset[int] = frozenset(range(151, 201))
BATCH04_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH04_IDS

EXPECTED_SURFACE: dict[int, str] = {
    151: "quarterly_protocol_performance_reports",
    152: "governance_proposal_intelligence",
    153: "project_monitoring_coverage_registry",
    154: "ai_crypto_copilot",
    155: "ai_deep_research",
    156: "crypto_knowledge_graph",
    157: "research_library",
    158: "institutional_research_feed",
    159: "api_data_platform",
    160: "pay_per_request_data_access",
    161: "institutional_data_delivery_entitlements",
    162: "evidence_provenance_layer",
    163: "cross_domain_research_to_decision_intelligence",
    164: "token_unlock_actionability_score",
    165: "fundraising_momentum_score",
    166: "research_confidence_score",
    167: "social_volume_intelligence",
    168: "social_dominance_intelligence",
    169: "unique_social_volume",
    170: "trending_words",
    171: "trending_coins",
    172: "historical_crypto_trends",
    173: "key_narratives_intelligence",
    174: "alpha_narratives_intelligence",
    175: "social_sentiment_intelligence",
    176: "weighted_social_sentiment",
    177: "social_sentiment_balance",
    178: "social_source_breakdown",
    179: "development_activity_intelligence",
    180: "development_activity_contributors",
    181: "ecosystem_development_dashboard",
    182: "developer_activity_change_detection",
    183: "whale_transaction_intelligence",
    184: "whale_shark_holder_cohorts",
    185: "top_holders_intelligence",
    186: "historical_wallet_balance_tool",
    187: "exchange_inflow_intelligence",
    188: "exchange_outflow_intelligence",
    189: "exchange_netflow_intelligence",
    190: "exchange_supply_balance_intelligence",
    191: "exchange_user_activity",
    192: "network_activity_intelligence",
    193: "transaction_volume_intelligence",
    194: "nvt_intelligence",
    195: "mvrv_intelligence",
    196: "realized_cap_realized_value_intelligence",
    197: "daily_active_addresses",
    198: "age_consumed_dormancy_intelligence",
    199: "mean_dollar_invested_age",
    200: "token_circulation_intelligence",
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
    """Batch04 wrap — BCBS 239 top-level provenance (Run 011)."""
    merged: dict[str, Any] = dict(extra or {})
    if isinstance(payload, dict):
        src = payload.get("data_source") or payload.get("source")
        if src and not merged.get("data_source"):
            merged["data_source"] = src
        ts = payload.get("timestamp") or payload.get("attached_at")
        if ts and not merged.get("timestamp"):
            merged["timestamp"] = ts
    if not merged.get("data_source"):
        merged["data_source"] = f"cap646.batch04_dedicated#cap{capability_id:03d}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )

async def _cap151(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(151, params={**params, "symbol": symbol})
    return _wrap(151, symbol=symbol, payload_key="quarterly_protocol_performance_reports", payload=payload)

async def _cap152(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(152, params={**params, "symbol": symbol})
    return _wrap(152, symbol=symbol, payload_key="governance_proposal_intelligence", payload=payload)

async def _cap153(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(153, params={**params, "symbol": symbol})
    return _wrap(153, symbol=symbol, payload_key="project_monitoring_coverage_registry", payload=payload)

async def _cap154(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(154, params={**params, "symbol": symbol})
    return _wrap(154, symbol=symbol, payload_key="ai_crypto_copilot", payload=payload)

async def _cap155(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(155, params={**params, "symbol": symbol})
    return _wrap(155, symbol=symbol, payload_key="ai_deep_research", payload=payload)

async def _cap156(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(156, params={**params, "symbol": symbol})
    return _wrap(156, symbol=symbol, payload_key="crypto_knowledge_graph", payload=payload)

async def _cap157(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(157, params={**params, "symbol": symbol})
    return _wrap(157, symbol=symbol, payload_key="research_library", payload=payload)

async def _cap158(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(158, params={**params, "symbol": symbol})
    return _wrap(158, symbol=symbol, payload_key="institutional_research_feed", payload=payload)

async def _cap159(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(159, params={**params, "symbol": symbol})
    return _wrap(159, symbol=symbol, payload_key="api_data_platform", payload=payload, extra={"catalog_link": {"duplicate_of": 103, "classification": "DUPLICATE-LINK"}})

async def _cap160(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(160, params={**params, "symbol": symbol})
    return _wrap(160, symbol=symbol, payload_key="pay_per_request_data_access", payload=payload)

async def _cap161(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(161, params={**params, "symbol": symbol})
    return _wrap(161, symbol=symbol, payload_key="institutional_data_delivery_entitlements", payload=payload)

async def _cap162(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(162, params={**params, "symbol": symbol})
    return _wrap(162, symbol=symbol, payload_key="evidence_provenance_layer", payload=payload)

async def _cap163(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(163, params={**params, "symbol": symbol})
    return _wrap(163, symbol=symbol, payload_key="cross_domain_research_to_decision_intelligence", payload=payload)

async def _cap164(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(164, params={**params, "symbol": symbol})
    return _wrap(164, symbol=symbol, payload_key="token_unlock_actionability_score", payload=payload)

async def _cap165(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(165, params={**params, "symbol": symbol})
    return _wrap(165, symbol=symbol, payload_key="fundraising_momentum_score", payload=payload)

async def _cap166(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(166, params={**params, "symbol": symbol})
    return _wrap(166, symbol=symbol, payload_key="research_confidence_score", payload=payload)

async def _cap167(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(167, params={**params, "symbol": symbol})
    return _wrap(167, symbol=symbol, payload_key="social_volume_intelligence", payload=payload)

async def _cap168(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(168, params={**params, "symbol": symbol})
    return _wrap(168, symbol=symbol, payload_key="social_dominance_intelligence", payload=payload)

async def _cap169(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(169, params={**params, "symbol": symbol})
    return _wrap(169, symbol=symbol, payload_key="unique_social_volume", payload=payload)

async def _cap170(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(170, params={**params, "symbol": symbol})
    return _wrap(170, symbol=symbol, payload_key="trending_words", payload=payload)

async def _cap171(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(171, params={**params, "symbol": symbol})
    return _wrap(171, symbol=symbol, payload_key="trending_coins", payload=payload)

async def _cap172(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(172, params={**params, "symbol": symbol})
    return _wrap(172, symbol=symbol, payload_key="historical_crypto_trends", payload=payload)

async def _cap173(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(173, params={**params, "symbol": symbol})
    return _wrap(173, symbol=symbol, payload_key="key_narratives_intelligence", payload=payload)

async def _cap174(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(174, params={**params, "symbol": symbol})
    return _wrap(174, symbol=symbol, payload_key="alpha_narratives_intelligence", payload=payload)

async def _cap175(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(175, params={**params, "symbol": symbol})
    return _wrap(175, symbol=symbol, payload_key="social_sentiment_intelligence", payload=payload)

async def _cap176(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(176, params={**params, "symbol": symbol})
    return _wrap(176, symbol=symbol, payload_key="weighted_social_sentiment", payload=payload)

async def _cap177(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(177, params={**params, "symbol": symbol})
    return _wrap(177, symbol=symbol, payload_key="social_sentiment_balance", payload=payload)

async def _cap178(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(178, params={**params, "symbol": symbol})
    return _wrap(178, symbol=symbol, payload_key="social_source_breakdown", payload=payload)

async def _cap179(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(179, params={**params, "symbol": symbol})
    return _wrap(179, symbol=symbol, payload_key="development_activity_intelligence", payload=payload)

async def _cap180(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(180, params={**params, "symbol": symbol})
    return _wrap(180, symbol=symbol, payload_key="development_activity_contributors", payload=payload)

async def _cap181(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(181, params={**params, "symbol": symbol})
    return _wrap(181, symbol=symbol, payload_key="ecosystem_development_dashboard", payload=payload)

async def _cap182(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(182, params={**params, "symbol": symbol})
    return _wrap(182, symbol=symbol, payload_key="developer_activity_change_detection", payload=payload)

async def _cap183(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(183, params={**params, "symbol": symbol})
    return _wrap(183, symbol=symbol, payload_key="whale_transaction_intelligence", payload=payload)

async def _cap184(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(184, params={**params, "symbol": symbol})
    return _wrap(184, symbol=symbol, payload_key="whale_shark_holder_cohorts", payload=payload)

async def _cap185(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(185, params={**params, "symbol": symbol})
    return _wrap(185, symbol=symbol, payload_key="top_holders_intelligence", payload=payload)

async def _cap186(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(186, params={**params, "symbol": symbol})
    return _wrap(186, symbol=symbol, payload_key="historical_wallet_balance_tool", payload=payload)

async def _cap187(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(187, params={**params, "symbol": symbol})
    return _wrap(187, symbol=symbol, payload_key="exchange_inflow_intelligence", payload=payload)

async def _cap188(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(188, params={**params, "symbol": symbol})
    return _wrap(188, symbol=symbol, payload_key="exchange_outflow_intelligence", payload=payload)

async def _cap189(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(189, params={**params, "symbol": symbol})
    return _wrap(189, symbol=symbol, payload_key="exchange_netflow_intelligence", payload=payload)

async def _cap190(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(190, params={**params, "symbol": symbol})
    return _wrap(190, symbol=symbol, payload_key="exchange_supply_balance_intelligence", payload=payload)

async def _cap191(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(191, params={**params, "symbol": symbol})
    return _wrap(191, symbol=symbol, payload_key="exchange_user_activity", payload=payload)

async def _cap192(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(192, params={**params, "symbol": symbol})
    return _wrap(192, symbol=symbol, payload_key="network_activity_intelligence", payload=payload)

async def _cap193(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(193, params={**params, "symbol": symbol})
    return _wrap(193, symbol=symbol, payload_key="transaction_volume_intelligence", payload=payload)

async def _cap194(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(194, params={**params, "symbol": symbol})
    return _wrap(194, symbol=symbol, payload_key="nvt_intelligence", payload=payload)

async def _cap195(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(195, params={**params, "symbol": symbol})
    return _wrap(195, symbol=symbol, payload_key="mvrv_intelligence", payload=payload)

async def _cap196(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    """FREE_TIER parity — same realized_cap_metrics as free_tier ID 196 (Run 012 split-brain fix)."""
    from bd_platform.free_tier_capabilities import realized_cap_metrics

    metrics = await realized_cap_metrics(symbol=symbol)
    return _wrap(
        196,
        symbol=symbol,
        payload_key="realized_cap_realized_value_intelligence",
        payload=metrics,
        extra={
            "data": metrics,
            "parity_binding": "free_tier.realized_cap_metrics",
            "methodology": "defillama_market_proxy_realized_cap",
        },
    )

async def _cap197(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(197, params={**params, "symbol": symbol})
    return _wrap(197, symbol=symbol, payload_key="daily_active_addresses", payload=payload)

async def _cap198(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(198, params={**params, "symbol": symbol})
    return _wrap(198, symbol=symbol, payload_key="age_consumed_dormancy_intelligence", payload=payload)

async def _cap199(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(199, params={**params, "symbol": symbol})
    return _wrap(199, symbol=symbol, payload_key="mean_dollar_invested_age", payload=payload)

async def _cap200(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(200, params={**params, "symbol": symbol})
    return _wrap(200, symbol=symbol, payload_key="token_circulation_intelligence", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    151: _cap151,
    152: _cap152,
    153: _cap153,
    154: _cap154,
    155: _cap155,
    156: _cap156,
    157: _cap157,
    158: _cap158,
    159: _cap159,
    160: _cap160,
    161: _cap161,
    162: _cap162,
    163: _cap163,
    164: _cap164,
    165: _cap165,
    166: _cap166,
    167: _cap167,
    168: _cap168,
    169: _cap169,
    170: _cap170,
    171: _cap171,
    172: _cap172,
    173: _cap173,
    174: _cap174,
    175: _cap175,
    176: _cap176,
    177: _cap177,
    178: _cap178,
    179: _cap179,
    180: _cap180,
    181: _cap181,
    182: _cap182,
    183: _cap183,
    184: _cap184,
    185: _cap185,
    186: _cap186,
    187: _cap187,
    188: _cap188,
    189: _cap189,
    190: _cap190,
    191: _cap191,
    192: _cap192,
    193: _cap193,
    194: _cap194,
    195: _cap195,
    196: _cap196,
    197: _cap197,
    198: _cap198,
    199: _cap199,
    200: _cap200,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH04_DEDICATED_IDS,
        overlap_batch01_ids=BATCH04_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch04: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in batch04 dedicated set",
    )
