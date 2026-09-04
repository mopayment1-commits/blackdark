"""
CAP646 capability runtime — routes all 646 IDs to real canonical backends.
"""

from __future__ import annotations

from typing import Any

from cap646.catalog import canonical_id, catalog_by_id, is_duplicate, is_external, matrix_by_id
from cap646.entitlements import entitlement_engine
from cap646.evidence_class import ai_compliance_footer
from cap646.handlers.ai import handle_ai_capability
from cap646.handlers.alerts import handle_alerts_capability
from cap646.handlers.data import handle_data_capability
from cap646.handlers.derivatives import handle_derivatives_capability
from cap646.handlers.execution import handle_execution_capability
from cap646.handlers.institutional import handle_institutional_capability
from cap646.handlers.market import handle_market_capability
from cap646.handlers.onchain import handle_onchain_capability
from cap646.handlers.platform import handle_platform_capability
from cap646.handlers.verified import handle_verified_capability
from cap646.batch01_production import BATCH01_IDS
from cap646.batch02_production import BATCH02_IDS
from cap646.batch03_production import BATCH03_IDS
from cap646.batch04_production import BATCH04_IDS
from cap646.batch05_production import BATCH05_IDS
from cap646.batch_spine import execute_and_enrich_batch
from cap646.handlers.batch01 import handle_batch01_capability
from cap646.handlers.batch02 import handle_batch02_capability
from cap646.handlers.batch03 import handle_batch03_capability
from cap646.handlers.batch04 import handle_batch04_capability
from cap646.handlers.batch05 import handle_batch05_capability
from cap646.waves import WAVE_D

VERIFIED_IDS = frozenset({49, 50, 62, 63, 632, 638, 639, 640, 641})
OPTION_A_IDS = frozenset({338, 500, 507, 534}) | BATCH01_IDS | BATCH02_IDS | BATCH03_IDS | BATCH04_IDS | BATCH05_IDS
WAVE_D_SET = set(WAVE_D)


from cap646.rtm_classification import runtime_classification as _runtime_classification

def _route_handler(track: str, name: str, capability_id: int):
    nl = name.lower()
    if capability_id in OPTION_A_IDS:
        if capability_id in BATCH01_IDS:
            return handle_batch01_capability
        if capability_id in BATCH02_IDS:
            return handle_batch02_capability
        if capability_id in BATCH03_IDS:
            return handle_batch03_capability
        if capability_id in BATCH04_IDS:
            return handle_batch04_capability
        if capability_id in BATCH05_IDS:
            return handle_batch05_capability
        if capability_id in {338, 500}:
            return handle_data_capability
        return handle_market_capability
    if capability_id == 329:
        return handle_institutional_capability
    if capability_id in VERIFIED_IDS:
        return handle_verified_capability
    if track == "T03" or any(k in nl for k in ("data quality", "ingestion", "freshness", "storage", "pipeline", "normalization", "provenance")):
        return handle_data_capability
    if track in {"T04", "T11"} or any(k in nl for k in ("market", "order book", "spot", "reference rate", "ohlcv", "sentiment intelligence", "dex volume")):
        if "sentiment" in nl and track in {"T12", "T09"}:
            return handle_ai_capability
        return handle_market_capability
    if track in {"T05", "T08", "T10"} and any(k in nl for k in ("futures", "funding", "liquidation", "open interest", "options", "derivative", "perp")):
        return handle_derivatives_capability
    if track in {"T06", "T07", "T08"} and any(k in nl for k in ("arbitrage", "execution", "risk", "spread", "hedge", "trading")):
        return handle_execution_capability
    if track == "T09" or any(k in nl for k in ("on-chain", "on chain", "wallet", "whale", "transaction", "tvl", "gas")):
        if "alert" in nl:
            return handle_alerts_capability
        return handle_onchain_capability
    if track == "T13" or "alert" in nl:
        return handle_alerts_capability
    if track in {"T02", "T15", "T16", "T17", "T01"} and any(
        k in nl for k in ("institutional", "security", "api", "capacity", "chaos", "gateway", "entitlement", "architecture", "encryption", "backtesting", "delivery", "audit")
    ):
        return handle_institutional_capability
    if track in {"T12", "T14", "T16"} or any(k in nl for k in ("ai", "oracle", "decision", "prediction", "signal", "research", "nlp", "mcp")):
        return handle_ai_capability
    if track == "T13":
        return handle_alerts_capability
    if track == "T17" and capability_id in {638, 639, 640, 641, 642}:
        return handle_ai_capability
    if capability_id in WAVE_D_SET:
        return handle_platform_capability
    return handle_platform_capability


async def execute_capability(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
    org_id: str | None = None,
    params: dict[str, Any] | None = None,
    skip_entitlement: bool = False,
) -> dict[str, Any]:
    params = dict(params or {})
    row = catalog_by_id().get(capability_id)
    if not row:
        return ai_compliance_footer({"success": False, "error": "unknown_capability_id", "capability_id": capability_id})

    if is_external(capability_id):
        return ai_compliance_footer(
            {
                "success": False,
                "capability_id": capability_id,
                "classification": "EXTERNAL/BLOCKED",
                "capability": row["capability"],
                "track": row["track"],
                "reason": matrix_by_id()[capability_id].get("reason"),
            }
        )

    target_id = canonical_id(capability_id)

    if not skip_entitlement:
        ent = await entitlement_engine.check(target_id, user=user, org_id=org_id)
        if not ent.get("allowed"):
            return ai_compliance_footer(
                {
                    "success": False,
                    "capability_id": target_id,
                    "capability": row["capability"],
                    "entitlement": ent,
                }
            )

    from bd_platform.free_tier_capabilities import FREE_TIER_BASE_IDS, execute_free_tier_capability

    if capability_id in BATCH01_IDS:
        return await execute_and_enrich_batch(
            handle_batch01_capability, capability_id, row=row, params=params
        )

    if capability_id in BATCH02_IDS:
        return await execute_and_enrich_batch(
            handle_batch02_capability, capability_id, row=row, params=params
        )

    if capability_id in BATCH03_IDS:
        return await execute_and_enrich_batch(
            handle_batch03_capability, capability_id, row=row, params=params
        )

    if capability_id in BATCH04_IDS:
        return await execute_and_enrich_batch(
            handle_batch04_capability, capability_id, row=row, params=params
        )

    if capability_id in BATCH05_IDS:
        return await execute_and_enrich_batch(
            handle_batch05_capability, capability_id, row=row, params=params
        )

    if is_duplicate(capability_id) and target_id != capability_id:
        canonical = await execute_capability(target_id, user=user, org_id=org_id, params=params, skip_entitlement=skip_entitlement)
        canonical["duplicate_of"] = target_id
        canonical["requested_capability_id"] = capability_id
        canonical["classification"] = "DUPLICATE/ALREADY_COVERED"
        return canonical

    # Batch spine is reached only via direct BATCH0x_IDS (L112-125) or duplicate
    # recursion (L128-133). No further target_id batch delegation exists in catalog.

    if capability_id in FREE_TIER_BASE_IDS:
        free_result = await execute_free_tier_capability(capability_id, params=params)
        free_result.setdefault("capability", row["capability"])
        free_result.setdefault("track", row["track"])
        free_result.setdefault("classification", _runtime_classification(free_result))
        from cap646.domain_enrichment import enrich_capability_result

        return await enrich_capability_result(capability_id, ai_compliance_footer(free_result), params=params)

    handler = _route_handler(row["track"], row["capability"], target_id)
    try:
        if handler is handle_institutional_capability:
            result = await handler(target_id, params=params, user=user, org_id=org_id)
        else:
            result = await handler(target_id, params=params)
    except Exception as exc:
        result = {
            "success": False,
            "error": str(exc),
            "handler": handler.__name__,
        }

    result.setdefault("capability_id", target_id)
    result.setdefault("capability", row["capability"])
    result.setdefault("track", row["track"])
    result.setdefault("classification", _runtime_classification(result))
    if "backend_module" not in result:
        result["backend_module"] = getattr(handler, "__module__", "cap646.handlers")
        result["backend_entrypoint"] = getattr(handler, "__name__", "unknown")
    from cap646.domain_enrichment import enrich_capability_result

    return await enrich_capability_result(target_id, ai_compliance_footer(result), params=params)
