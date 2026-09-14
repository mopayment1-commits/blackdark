"""Official Batch 07 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 07 (IDs 151–175).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH07_IDS: frozenset[int] = frozenset(range(151, 176))
BATCH07_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH07_DEDICATED_IDS: frozenset[int] = frozenset({151, 152, 153, 154, 155, 156, 157, 158, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    151: "quarterly_protocol_performance_reports",
    152: "governance_proposal_intelligence",
    153: "project_monitoring_coverage_registry",
    154: "ai_crypto_copilot",
    155: "ai_deep_research",
    156: "crypto_knowledge_graph",
    157: "research_library",
    158: "institutional_research_feed",
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
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap151(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        151,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="quarterly_protocol_performance_reports",
        params=params,
    )

async def _cap152(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        152,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="governance_proposal_intelligence",
        params=params,
    )

async def _cap153(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        153,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="project_monitoring_coverage_registry",
        params=params,
    )

async def _cap154(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        154,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="ai_crypto_copilot",
        params=params,
    )

async def _cap155(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        155,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="ai_deep_research",
        params=params,
    )

async def _cap156(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        156,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="crypto_knowledge_graph",
        params=params,
    )

async def _cap157(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        157,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="research_library",
        params=params,
    )

async def _cap158(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        158,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="institutional_research_feed",
        params=params,
    )

async def _cap160(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        160,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="pay_per_request_data_access",
        params=params,
    )

async def _cap161(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        161,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="institutional_data_delivery_entitlements",
        params=params,
    )

async def _cap162(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        162,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="evidence_provenance_layer",
        params=params,
    )

async def _cap163(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        163,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_domain_research_to_decision_intelligence",
        params=params,
    )

async def _cap164(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        164,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="token_unlock_actionability_score",
        params=params,
    )

async def _cap165(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        165,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="fundraising_momentum_score",
        params=params,
    )

async def _cap166(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        166,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="research_confidence_score",
        params=params,
    )

async def _cap167(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        167,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="social_volume_intelligence",
        params=params,
    )

async def _cap168(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        168,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="social_dominance_intelligence",
        params=params,
    )

async def _cap169(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        169,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="unique_social_volume",
        params=params,
    )

async def _cap170(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        170,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="trending_words",
        params=params,
    )

async def _cap171(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        171,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="trending_coins",
        params=params,
    )

async def _cap172(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        172,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="historical_crypto_trends",
        params=params,
    )

async def _cap173(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        173,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="key_narratives_intelligence",
        params=params,
    )

async def _cap174(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        174,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="alpha_narratives_intelligence",
        params=params,
    )

async def _cap175(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        175,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="social_sentiment_intelligence",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    151: _cap151,
    152: _cap152,
    153: _cap153,
    154: _cap154,
    155: _cap155,
    156: _cap156,
    157: _cap157,
    158: _cap158,
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
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH07_DEDICATED_IDS,
        overlap_batch01_ids=BATCH07_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch07",
        not_dedicated_error=f"batch07: not a dedicated capability",
    )
