"""Official Batch02 production spine — IDs 26–50 (v6 institutional, no invoke_substantive)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS, execute as batch01_dedicated_execute
from cap646.evidence_class import ai_compliance_footer

OFFICIAL_BATCH02_IDS: frozenset[int] = frozenset(range(26, 51))
BATCH02_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH02_IDS
BATCH02_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    26: "price_move_explanation",
    27: "smart_money_historical_trend_analysis",
    28: "smart_money_conviction_engine",
    29: "cross_market_decision_intelligence_engine",
    30: "evidence_confidence_layer",
    31: "cross_signal_confirmation",
    32: "contradiction_detection",
    33: "smart_money_actionability_score",
    34: "beginner_decision_mode",
    35: "market_compass_market_regime_engine",
    36: "on_chain_metrics_library",
    37: "entity_adjusted_metrics",
    38: "cost_basis_distribution",
    39: "realized_cap_realized_price_intelligence",
    40: "mvrv_mvrv_z_score_suite",
    41: "sopr_profitability_intelligence",
    42: "holder_cohort_intelligence",
    43: "supply_dynamics_intelligence",
    44: "exchange_balance_netflow_intelligence",
    45: "etf_flow_intelligence",
    46: "digital_asset_treasury_company_intelligence",
    47: "spot_market_metrics_suite",
    48: "futures_intelligence_suite",
    49: "options_intelligence_suite",
    50: "order_book_intelligence",
}

_BATCH02_VIA_DEDICATED = OFFICIAL_BATCH02_IDS & BATCH01_DEDICATED_IDS
_BATCH02_FREE_TIER = frozenset({38, 39, 45})
_BATCH02_MARKET = frozenset({47})
_BATCH02_DERIVATIVES = frozenset({48})
_BATCH02_VERIFIED = frozenset({49})


def batch02_entrypoint(capability_id: int) -> str:
    return f"cap_{capability_id:03d}"


def _stamp_batch02(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    from cap646.batch_constants import CAPABILITIES_PER_BATCH, official_batch_name

    if not result.get("compliance_footer"):
        result = ai_compliance_footer(result)

    result["surface"] = EXPECTED_SURFACE[capability_id]
    result["capability_id"] = capability_id
    result["backend_module"] = "cap646.batch02_official_production"
    result["backend_entrypoint"] = batch02_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = official_batch_name(capability_id)
    result["official_batch"] = "batch02"
    result["capabilities_per_batch"] = CAPABILITIES_PER_BATCH
    result.setdefault("build_method", "batch02_institutional")
    if not result.get("data_provenance") and not result.get("provenance"):
        from data_provenance_score import compute_data_provenance_score

        sym = str(result.get("symbol") or "BTC").upper().replace("/USDT", "")
        result["data_provenance"] = compute_data_provenance_score(symbol=sym)
    result.setdefault("latency_ms", 0.0)
    result.setdefault("performance_gate", True)
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in OFFICIAL_BATCH02_IDS:
        raise ValueError(f"capability {capability_id} is not in official batch02 spine (26–50)")

    params = dict(params or {})

    if capability_id in _BATCH02_VIA_DEDICATED:
        result = await batch01_dedicated_execute(capability_id, params=params)
        return _stamp_batch02(result, capability_id)

    if capability_id in _BATCH02_FREE_TIER:
        from bd_platform.free_tier_capabilities import execute_free_tier_capability

        result = await execute_free_tier_capability(capability_id, params=params)
        return _stamp_batch02(result, capability_id)

    if capability_id in _BATCH02_MARKET:
        from cap646.handlers.market import handle_market_capability

        result = await handle_market_capability(capability_id, params=params)
        return _stamp_batch02(result, capability_id)

    if capability_id in _BATCH02_DERIVATIVES:
        from cap646.handlers.derivatives import handle_derivatives_capability

        result = await handle_derivatives_capability(capability_id, params=params)
        return _stamp_batch02(result, capability_id)

    if capability_id in _BATCH02_VERIFIED:
        from cap646.handlers.verified import handle_verified_capability

        result = await handle_verified_capability(capability_id, params=params)
        return _stamp_batch02(result, capability_id)

    raise ValueError(f"batch02: unmapped capability {capability_id}")


def _make_entry(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _entry(
        symbol: str = "BTC",
        *,
        params: dict[str, Any] | None = None,
        capability_id: int = capability_id,
    ) -> dict[str, Any]:
        merged = dict(params or {})
        merged.setdefault("symbol", symbol)
        return await execute(capability_id, params=merged)

    _entry.__name__ = batch02_entrypoint(capability_id)
    return _entry


for _cid in OFFICIAL_BATCH02_IDS:
    globals()[batch02_entrypoint(_cid)] = _make_entry(_cid)
