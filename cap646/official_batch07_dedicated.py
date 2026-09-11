"""Official batch 07 — from-scratch dedicated backends (IDs 151–175)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH07_IDS: frozenset[int] = frozenset(range(151, 176))
BATCH07_DEDICATED_IDS: frozenset[int] = frozenset({151, 152, 153, 154, 155, 156, 157, 158, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175})
BATCH07_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

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

async def _cap151(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap151 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap152(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap152 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap153(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap153 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap154(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap154 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap155(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap155 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap156(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap156 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap157(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap157 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap158(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap158 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap160(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap160 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap161(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap161 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap162(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap162 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap163(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap163 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap164(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap164 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap165(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap165 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap166(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap166 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap167(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap167 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap168(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap168 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap169(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap169 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap170(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap170 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap171(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap171 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap172(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap172 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap173(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap173 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap174(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap174 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap175(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch07_dedicated import _cap175 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

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
        overlap_error="batch01 overlap for official batch07",
        not_dedicated_error=f"official batch07: not dedicated",
    )
