"""Batch 04 dedicated backends — catalog-aligned payloads for IDs 151–200.

IDs 175 is batch01 overlap: no dedicated backend here; runtime routes via
``LEGACY_BATCH01_EXTENSION_IDS`` (see ``BATCH04_OVERLAP_BATCH01_IDS``).

Catalog is functional truth (ISO 25010): handlers emit goal-specific surfaces,
not misaligned hero wrappers. Blockers #159/#183 remain NOT_COMPLETE per owner
decisions — no REUSED-LINK stamps until canonical readiness (#103) or DISTINCT
path (#183 Option B approved).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import seed as _seed
from cap646.dedicated_common import sym as _sym

BATCH04_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset({175})
BATCH04_DEDICATED_IDS: frozenset[int] = frozenset(range(151, 201)) - BATCH04_OVERLAP_BATCH01_IDS

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
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

_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _catalog_payload(capability_id: int, symbol: str, **extra: Any) -> dict[str, Any]:
  """Catalog-aligned core payload — ok + feature_ref required by acceptance."""
  payload: dict[str, Any] = {
      "ok": True,
      "feature_ref": capability_id,
      "symbol": symbol,
      "catalog_goal": EXPECTED_SURFACE[capability_id],
  }
  payload.update(extra)
  return payload


async def _cap_catalog(
    capability_id: int,
    *,
    symbol: str,
    address: str,
    params: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = EXPECTED_SURFACE[capability_id]
    payload = _catalog_payload(capability_id, symbol, **(extra or {}))
    return _wrap(capability_id, symbol=symbol, payload_key=root, payload=payload)


def _make_catalog_handler(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _handler(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
        return await _cap_catalog(capability_id, symbol=symbol, address=address, params=params)

    _handler.__name__ = f"_cap{capability_id}"
    return _handler


async def _cap_hero_bridge(capability_id: int, *, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch04_hero_bridge import build_hero_payload

    payload = build_hero_payload(capability_id, symbol=symbol, params=params, seed=_seed())
    root = EXPECTED_SURFACE[capability_id]
    return _wrap(capability_id, symbol=symbol, payload_key=root, payload=payload)


def _make_hero_handler(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _handler(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
        return await _cap_hero_bridge(capability_id, symbol=symbol, address=address, params=params)

    _handler.__name__ = f"_cap{capability_id}"
    return _handler


async def _cap151(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import explain_opportunity_151, ingest_defillama_149
    from cap646.batch04_quarterly_protocol import build_quarterly_protocol_report

    explanation = explain_opportunity_151(asset=symbol, seed=_seed())
    defi_snapshot = ingest_defillama_149(seed=_seed())
    payload = build_quarterly_protocol_report(
        symbol=symbol,
        explanation=explanation,
        defi_snapshot=defi_snapshot,
    )
    return _wrap(151, symbol=symbol, payload_key="quarterly_protocol_performance_reports", payload=payload)


async def _cap159(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.handlers.institutional import handle_institutional_capability

    canonical = await handle_institutional_capability(103, params=params)
    platform = {
        "ok": True,
        "feature_ref": 159,
        "institutional_api": canonical.get("institutional_api") or "/api/institutional",
        "graphql": canonical.get("graphql") or "/graphql",
        "hot_storage": canonical.get("hot_storage"),
        "blocker": "BLOCKER-159-103",
        "canonical_overlap": 103,
        "canonical_status": "OVERLAP-PARTIAL",
        "owner_decision": "NOT_COMPLETE — no REUSED-LINK until #103 matures (Tolerate 2026-10-03) or DISTINCT ADR",
    }
    return _wrap(
        159,
        symbol=symbol,
        payload_key="api_data_platform",
        payload=platform,
        extra={"classification": "NOT_COMPLETE", "blocker": "BLOCKER-159-103"},
    )


async def _cap161(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.handlers.institutional import handle_institutional_capability

    raw = await handle_institutional_capability(161, params=params)
    payload = _catalog_payload(
        161,
        symbol,
        isolation=raw.get("isolation"),
        role_matrix=raw.get("role_matrix"),
        entitlements=raw.get("role_matrix"),
    )
    return _wrap(161, symbol=symbol, payload_key="institutional_data_delivery_entitlements", payload=payload)


async def _cap162(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_common import provenance_hot_storage_payload

    provenance = provenance_hot_storage_payload(symbol)
    provenance["catalog_link"] = {"duplicate_of": 106, "classification": "REUSED-LINK"}
    payload = _catalog_payload(162, symbol, provenance=provenance.get("provenance"), hot_storage=provenance.get("hot_storage"))
    return _wrap(162, symbol=symbol, payload_key="evidence_provenance_layer", payload=payload)


async def _cap183(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    amount = float(params.get("amount_usd") or params.get("value_usd") or 1_000_000)
    whale = {
        "ok": True,
        "feature_ref": 183,
        "symbol": symbol,
        "address": address,
        "amount_usd": amount,
        "risk_score": min(100.0, max(0.0, amount / 100_000)),
        "classification": "whale_transaction",
        "owner_decision": "DISTINCT-only Option B — no REUSED-LINK to #130; #130 stays PRODUCTION-ALIGNED in Batch03",
    }
    return _wrap(
        183,
        symbol=symbol,
        payload_key="whale_transaction",
        payload=whale,
        extra={"classification": "NOT_COMPLETE", "blocker": "BLOCKER-183-130"},
    )


async def _cap189(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_common import exchange_netflow_probe

    exchange, netflow = exchange_netflow_probe(params, symbol)
    payload = _catalog_payload(189, symbol, exchange=exchange, netflow=netflow, netflow_proxy=netflow.get("netflow_proxy"))
    return _wrap(189, symbol=symbol, payload_key="exchange_netflow_intelligence", payload=payload)


_DISPATCH_OVERRIDES: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    151: _cap151,
    159: _cap159,
    161: _cap161,
    162: _cap162,
    183: _cap183,
    189: _cap189,
}

_HERO_BRIDGE_IDS = frozenset(range(152, 201)) - {159, 175, 183} - frozenset(_DISPATCH_OVERRIDES.keys())

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    cid: _DISPATCH_OVERRIDES.get(cid, _make_hero_handler(cid) if cid in _HERO_BRIDGE_IDS else _make_catalog_handler(cid))
    for cid in sorted(BATCH04_DEDICATED_IDS)
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH04_DEDICATED_IDS,
        overlap_batch01_ids=BATCH04_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error=(
            f"capability {capability_id} is batch01 overlap — use cap646.batch01_production"
        ),
        not_dedicated_error=f"capability {capability_id} is not in batch04 dedicated spine",
    )
