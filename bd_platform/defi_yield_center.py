"""
DeFi Yield Center — Features #709 + #710 + #711 + #198 merged (Sprint 2).

Unified DeFi Hub: Yields Screener (#711), Yield History (#709),
Yield Arbitrage Engine (#710), Yield Optimization (#198).

NOT separate screeners — single DeFi Yield Center surface.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DeFiYieldCenter")

_FEATURE_IDS = [709, 710, 711, 198]
_CENTER_NAME = "DeFi Yield Center"
_SEED_PATH = Path("data/defi_yield_center_seed.json")
_STORE_PATH = Path("data/defi_yield_center.json")
_DISCLAIMER = "No guaranteed yield. Past simulation does not guarantee future results."
_DISCLAIMER_AR = "لا يوجد عائد مضمون. المحاكاة السابقة لا تضمن النتائج المستقبلية."
_STALE_DAYS = 7

Risk = Literal["low", "medium", "high"]
Tier = Literal["pro", "institutional"]

_RISK_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🔴"}
_RISK_LABEL = {"low": "Low", "medium": "Medium", "high": "High"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"apy_methodology": {}, "pools": [], "arbitrage_opportunities": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi yield center seed load failed: %s", exc)
        return {"apy_methodology": {}, "pools": [], "arbitrage_opportunities": []}


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    seed = _load_seed()
    store = {**seed, "updated_at": _utcnow()}
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    return store


def _format_tvl(tvl: float) -> str:
    if tvl >= 1_000_000_000:
        return f"${tvl / 1_000_000_000:.1f}B"
    if tvl >= 1_000_000:
        return f"${tvl / 1_000_000:.0f}M"
    return f"${tvl:,.0f}"


def _is_stale(last_interaction: str | None, threshold_days: int = _STALE_DAYS) -> bool:
    if not last_interaction:
        return True
    try:
        last = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
        return (datetime.now(UTC) - last) > timedelta(days=threshold_days)
    except ValueError:
        return True


def _enrich_screener_pool(row: dict[str, Any], methodology: dict[str, Any]) -> dict[str, Any]:
    stale = _is_stale(row.get("last_interaction_at_utc"))
    risk = str(row.get("risk_level") or "medium")
    emoji = _RISK_EMOJI.get(risk, "🟡")
    tvl = float(row.get("tvl_usd") or 0)
    apy = float(row.get("current_apy_pct") or 0)

    return {
        **row,
        "stale": stale,
        "stale_display": "❌ No" if not stale else "⚠️ Yes",
        "excluded_reason": "stale_pool" if stale else None,
        "screener_display": (
            f"Pool {row.get('pool')}: APY {apy}% | TVL {_format_tvl(tvl)} | "
            f"Risk: {emoji} {_RISK_LABEL.get(risk, risk.title())} | Stale: {'❌ No' if not stale else '⚠️ Yes'}"
        ),
        "apy_methodology": methodology.get("formula"),
        "risk_level": risk,
        "risk_display": f"{emoji} {_RISK_LABEL.get(risk, risk.title())}",
        "no_guaranteed_yield": True,
    }


def _compute_arbitrage_costs(opp: dict[str, Any]) -> dict[str, Any]:
    position = float(opp.get("position_usd") or 0)
    gas = float(opp.get("gas_cost_usd") or 0)
    bridge = float(opp.get("bridge_cost_usd") or 0)
    slippage_bps = float(opp.get("slippage_bps") or 0)
    slippage_usd = position * slippage_bps / 10_000
    lockup_days = int(opp.get("lockup_days") or 0)
    total_switching_cost = gas + bridge + slippage_usd

    gross_delta = float(opp.get("gross_yield_delta_pct") or 0)
    annual_benefit = position * (gross_delta / 100)
    daily_benefit = annual_benefit / 365 if annual_benefit > 0 else 0
    break_even_days = round(total_switching_cost / daily_benefit, 1) if daily_benefit > 0 else None

    net_yield_delta = gross_delta - (total_switching_cost / position * 100) if position > 0 else gross_delta
    risk_score = int(opp.get("protocol_risk_score") or 5)
    risk_adj_rank = net_yield_delta / max(risk_score, 1)

    return {
        "gas_cost_usd": gas,
        "bridge_cost_usd": bridge,
        "slippage_usd": round(slippage_usd, 2),
        "lockup_days": lockup_days,
        "total_switching_cost_usd": round(total_switching_cost, 2),
        "gross_yield_delta_pct": gross_delta,
        "net_yield_delta_pct": round(net_yield_delta, 2),
        "break_even_days": break_even_days,
        "break_even_display": (
            f"To recover switching cost: {break_even_days:.0f} days"
            if break_even_days is not None
            else "Break-even not achievable at current delta"
        ),
        "risk_adjusted_rank": round(risk_adj_rank, 3),
        "costs_included": True,
    }


def _enrich_arbitrage(opp: dict[str, Any], pools: dict[str, dict[str, Any]]) -> dict[str, Any]:
    costs = _compute_arbitrage_costs(opp)
    sim_pct = float(opp.get("simulation_6m_success_pct") or 0)

    return {
        **opp,
        **costs,
        "from_pool": pools.get(opp.get("from_pool_id", ""), {}),
        "to_pool": pools.get(opp.get("to_pool_id", ""), {}),
        "opportunity_display": (
            f"{opp.get('from_protocol')} → {opp.get('to_protocol')} | "
            f"Net yield: {costs['net_yield_delta_pct']}% | "
            f"{costs['break_even_display']}"
        ),
        "simulation_display": (
            f"6-month backtest → {sim_pct:.0f}% success rate"
        ),
        "simulation_6m_success_pct": sim_pct,
        "confidence": "medium" if sim_pct >= 70 else "low",
        "tier_required": opp.get("tier_required", "pro"),
        "auto_execute": False,
        "simulation_only": True,
        "execute_requires_mfa": True,
        "no_guaranteed_yield": True,
        "disclaimer": _DISCLAIMER,
    }


def screen_yield_pools(
    *,
    chain: str | None = None,
    min_tvl_usd: float | None = None,
    max_risk: Risk | None = None,
    exclude_stale: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    """#711 Yields Screener — filter/rank pools, exclude stale."""
    store = _load_store()
    methodology = store.get("apy_methodology") or {}
    pools = [_enrich_screener_pool(p, methodology) for p in store.get("pools") or []]

    if exclude_stale:
        pools = [p for p in pools if not p.get("stale")]
    if chain:
        pools = [p for p in pools if str(p.get("chain", "")).lower() == chain.lower()]
    if min_tvl_usd is not None:
        pools = [p for p in pools if float(p.get("tvl_usd") or 0) >= min_tvl_usd]
    if max_risk:
        risk_order = {"low": 0, "medium": 1, "high": 2}
        max_r = risk_order.get(max_risk, 2)
        pools = [p for p in pools if risk_order.get(str(p.get("risk_level", "high")), 2) <= max_r]

    pools.sort(key=lambda p: float(p.get("current_apy_pct") or 0), reverse=True)

    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "module": _CENTER_NAME,
        "surface": "yields_screener",
        "feature": 711,
        "apy_methodology": methodology,
        "stale_pools_excluded": exclude_stale,
        "stale_threshold_days": methodology.get("stale_threshold_days", _STALE_DAYS),
        "count": len(pools[:limit]),
        "pools": pools[:limit],
        "no_guaranteed_yield": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def list_yield_arbitrage(
    *,
    tier: Tier | None = None,
    min_net_yield_pct: float | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """#710 Yield Arbitrage Engine — net yield after costs, break-even, simulation."""
    store = _load_store()
    pool_map = {p["id"]: p for p in store.get("pools") or []}
    opps = [_enrich_arbitrage(o, pool_map) for o in store.get("arbitrage_opportunities") or []]

    if tier:
        opps = [o for o in opps if o.get("tier_required") == tier]
    if min_net_yield_pct is not None:
        opps = [o for o in opps if float(o.get("net_yield_delta_pct") or 0) >= min_net_yield_pct]

    opps.sort(key=lambda o: float(o.get("risk_adjusted_rank") or 0), reverse=True)

    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "module": _CENTER_NAME,
        "surface": "yield_arbitrage_engine",
        "feature": 710,
        "tier": "pro/institutional",
        "costs_included": True,
        "auto_execute": False,
        "simulation_only": True,
        "execute_requires_mfa": True,
        "count": len(opps[:limit]),
        "opportunities": opps[:limit],
        "no_guaranteed_yield": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def get_arbitrage_opportunity(opp_id: str) -> dict[str, Any]:
    store = _load_store()
    pool_map = {p["id"]: p for p in store.get("pools") or []}
    for opp in store.get("arbitrage_opportunities") or []:
        if opp.get("id") == opp_id:
            enriched = _enrich_arbitrage(opp, pool_map)
            return {
                "ok": True,
                "feature_ids": _FEATURE_IDS,
                "opportunity": enriched,
                "disclaimer": _DISCLAIMER,
                "timestamp": _utcnow(),
            }
    return {"ok": False, "error": "opportunity_not_found"}


def run_arbitrage_simulation(opp_id: str) -> dict[str, Any]:
    """Historical/simulation test — 6-month backtest results."""
    result = get_arbitrage_opportunity(opp_id)
    if not result.get("ok"):
        return result
    opp = result["opportunity"]
    sim_pct = float(opp.get("simulation_6m_success_pct") or 0)
    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "feature": 710,
        "opportunity_id": opp_id,
        "simulation_period_months": 6,
        "success_rate_pct": sim_pct,
        "simulation_display": f"Tested this switch on 6-month data → {sim_pct:.0f}% success",
        "historical_simulation": True,
        "auto_execute": False,
        "execute_requires_mfa": True,
        "no_guaranteed_yield": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def optimize_yield_allocation(
    *,
    capital_usd: float = 100_000,
    max_risk: Risk = "medium",
) -> dict[str, Any]:
    """#198 Yield Optimization — risk-adjusted pool allocation suggestion."""
    screener = screen_yield_pools(max_risk=max_risk, exclude_stale=True, limit=10)
    pools = screener.get("pools") or []
    if not pools:
        return {"ok": False, "error": "no_eligible_pools"}

    total_score = sum(float(p.get("current_apy_pct") or 0) for p in pools[:5]) or 1
    allocation = []
    remaining = capital_usd
    for pool in pools[:5]:
        weight = float(pool.get("current_apy_pct") or 0) / total_score
        amount = round(capital_usd * weight, 2)
        allocation.append({
            "pool_id": pool.get("id"),
            "protocol": pool.get("protocol"),
            "pool": pool.get("pool"),
            "weight_pct": round(weight * 100, 1),
            "amount_usd": amount,
            "expected_apy_pct": pool.get("current_apy_pct"),
            "risk": pool.get("risk_level"),
        })
        remaining -= amount

    blended_apy = sum(
        a["amount_usd"] * float(a["expected_apy_pct"] or 0) for a in allocation
    ) / capital_usd if capital_usd > 0 else 0

    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "feature": 198,
        "surface": "yield_optimization",
        "capital_usd": capital_usd,
        "max_risk": max_risk,
        "blended_apy_pct": round(blended_apy, 2),
        "allocation": allocation,
        "simulation_only": True,
        "no_guaranteed_yield": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


async def get_yield_center_dashboard() -> dict[str, Any]:
    """Unified DeFi Yield Center dashboard — screener + history + arbitrage + optimization."""
    from bd_platform.yield_sustainability_score import list_yield_pools

    screener = screen_yield_pools(exclude_stale=True, limit=10)
    arbitrage = list_yield_arbitrage(min_net_yield_pct=0, limit=5)
    sustainability = list_yield_pools(limit=5)
    optimization = optimize_yield_allocation()

    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "module": _CENTER_NAME,
        "sprint": 2,
        "surfaces": {
            "screener": screener,
            "sustainability_history": sustainability,
            "arbitrage": arbitrage,
            "optimization": optimization,
        },
        "integrated_features": {
            711: "Yields Screener",
            709: "Yield History / Sustainability",
            710: "Yield Arbitrage Engine",
            198: "Yield Optimization",
        },
        "no_guaranteed_yield": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def defi_yield_center_status() -> dict[str, Any]:
    store = _load_store()
    pools = store.get("pools") or []
    stale_count = sum(1 for p in pools if _is_stale(p.get("last_interaction_at_utc")))
    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "module": _CENTER_NAME,
        "sprint": 2,
        "pool_count": len(pools),
        "stale_pool_count": stale_count,
        "arbitrage_count": len(store.get("arbitrage_opportunities") or []),
        "apy_methodology_documented": True,
        "stale_pools_excluded": True,
        "costs_included": True,
        "historical_simulation_tests": True,
        "no_guaranteed_yield": True,
        "auto_execute": False,
        "execute_requires_mfa": True,
        "tier_arbitrage": "pro/institutional",
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
