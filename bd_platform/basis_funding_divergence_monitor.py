"""
Basis/Funding Divergence Monitor — Feature #440 (merged into #429).

Derivatives arbitrage category — monitoring/analytics only.
Renamed from "Derivatives & Futures Arbitrage" — no buy/sell/open-position language.

Displays:
  - spot-perp basis %
  - funding rate APY
  - calendar spread % (term structure deviation)
  - implied holding cost
  - cumulative funding vs estimated holding cost (no position simulation v1)
  - index vs derivative basis

NOT standalone — Unified Arbitrage Engine category.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.BasisFundingDivergence")

_FEATURE_ID = 440
_TITLE = "Basis/Funding Divergence Monitor"
_LEGAL_NAME = "Basis/Funding Divergence Monitor"
_RENAMED_FROM = "Derivatives & Futures Arbitrage"
_STANDALONE = False
_MERGED_INTO = "Unified Arbitrage Engine (#429) / Derivatives Arbitrage"
_CATEGORY = "derivatives_arbitrage"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/basis_funding_divergence_seed.json")
_METHODOLOGY_VERSION = "1.0"

_BANNED_TERMS = (
    "buy",
    "sell",
    "open position",
    "execute",
    "شراء",
    "بيع",
    "فتح مراكز",
)

_DISCLAIMER = (
    "Basis/Funding Divergence Monitor — derivatives market analytics only. "
    "Shows spot-perp basis, funding APY, calendar spreads, and implied holding costs. "
    "Monitoring only — no position simulation, no execution language, not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("basis funding divergence seed load failed: %s", exc)
        return {"assets": {}}


def _spot_perp_basis_pct(spot: float, perp: float) -> float:
    if spot <= 0:
        return 0.0
    return round((perp - spot) / spot * 100, 4)


def _index_derivative_basis_pct(index: float, derivative: float) -> float:
    if index <= 0:
        return 0.0
    return round((derivative - index) / index * 100, 4)


def _funding_rate_apy(funding_rate: float, interval_hours: float) -> float:
    if interval_hours <= 0:
        return 0.0
    periods = (365 * 24) / interval_hours
    return round(funding_rate * periods * 100, 4)


def _implied_holding_cost_pct(seed: dict[str, Any]) -> float:
    comp = seed.get("holding_cost_components") or {}
    total = sum(float(comp.get(k, 0)) for k in (
        "fees_pct", "borrow_cost_pct", "slippage_pct", "basis_risk_penalty_pct"
    ))
    return round(total, 4)


def _calendar_spread_pct(contracts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Term structure deviation between dated contracts — monitoring only."""
    dated = [c for c in contracts if c.get("expiry")]
    if len(dated) < 2:
        return None
    dated.sort(key=lambda c: c.get("days_to_expiry", 0))
    near, far = dated[0], dated[-1]
    near_p = float(near.get("price", 0))
    far_p = float(far.get("price", 0))
    if near_p <= 0:
        return None
    spread_pct = round((far_p - near_p) / near_p * 100, 4)
    return {
        "near_contract": near.get("contract"),
        "far_contract": far.get("contract"),
        "near_price": near_p,
        "far_price": far_p,
        "calendar_spread_pct": spread_pct,
        "term_structure_deviation": spread_pct,
        "days_between": int(far.get("days_to_expiry", 0)) - int(near.get("days_to_expiry", 0)),
        "monitoring_only": True,
        "no_position_recommendation": True,
    }


def _perp_quarterly_spread(raw: dict[str, Any]) -> dict[str, Any] | None:
    pq = raw.get("quarterly_perp_spread") or {}
    perp = float(pq.get("perp_price", 0))
    quarterly = float(pq.get("quarterly_price", 0))
    if perp <= 0 or quarterly <= 0:
        return None
    return {
        "perp_price": perp,
        "quarterly_price": quarterly,
        "quarterly_expiry": pq.get("quarterly_expiry"),
        "perp_quarterly_spread_pct": round((quarterly - perp) / perp * 100, 4),
        "monitoring_only": True,
    }


def _funding_vs_holding_cost(
    cumulative_funding_7d_pct: float,
    implied_holding_cost_pct: float,
) -> dict[str, Any]:
    """Cumulative funding vs estimated holding cost — no position simulation."""
    net_edge = round(cumulative_funding_7d_pct - implied_holding_cost_pct, 4)
    return {
        "cumulative_funding_7d_pct": cumulative_funding_7d_pct,
        "estimated_holding_cost_pct": implied_holding_cost_pct,
        "net_after_holding_cost_pct": net_edge,
        "funding_exceeds_holding_cost": cumulative_funding_7d_pct > implied_holding_cost_pct,
        "no_position_simulation_v1": True,
        "display": (
            f"7d cumulative funding {cumulative_funding_7d_pct:+.3f}% vs "
            f"estimated holding cost {implied_holding_cost_pct:.3f}%"
        ),
    }


def analyze_asset_divergence(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    raw = (seed.get("assets") or {}).get(asset.upper())
    if not raw:
        return {"ok": False, "error": "asset_not_found", "asset": asset}

    spot = float(raw.get("spot_price", 0))
    perp = float(raw.get("perp_price", 0))
    index = float(raw.get("index_price", 0))
    funding_rate = float(raw.get("funding_rate", 0))
    interval_h = float(raw.get("funding_interval_hours", seed.get("funding_interval_hours_default", 8)))
    holding_cost = _implied_holding_cost_pct(seed)
    cumulative_7d = float(raw.get("cumulative_funding_7d_pct", 0))

    basis_pct = _spot_perp_basis_pct(spot, perp)
    funding_apy = _funding_rate_apy(funding_rate, interval_h)
    calendar = _calendar_spread_pct(raw.get("calendar_contracts") or [])
    perp_q = _perp_quarterly_spread(raw)
    index_basis = _index_derivative_basis_pct(index, perp)
    funding_holding = _funding_vs_holding_cost(cumulative_7d, holding_cost)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "opportunity_type": "derivatives_basis_funding",
        "category": _CATEGORY,
        "legal_name": _LEGAL_NAME,
        "asset": asset.upper(),
        "venue": raw.get("venue"),
        "spot_perp_basis_pct": basis_pct,
        "funding_rate_apy": funding_apy,
        "calendar_spread": calendar,
        "perp_quarterly_spread": perp_q,
        "index_derivative_basis_pct": index_basis,
        "implied_holding_cost_pct": holding_cost,
        "funding_vs_holding_cost": funding_holding,
        "prices": {
            "spot": spot,
            "perp": perp,
            "index": index,
            "funding_rate": funding_rate,
            "funding_interval_hours": interval_h,
        },
        "monitoring_only": True,
        "no_position_simulation_v1": seed.get("no_position_simulation_v1", True),
        "no_execution_language": True,
        "timestamp": _utcnow(),
    }


def scan_derivatives_divergence(
    assets: list[str] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#440 — scan all assets for basis/funding divergence opportunities (monitoring)."""
    seed = seed or _load_seed()
    targets = assets or list((seed.get("assets") or {}).keys())
    results = []
    for asset in targets:
        analysis = analyze_asset_divergence(asset, seed=seed)
        if not analysis.get("ok"):
            continue
        opp = _to_unified_opportunity(analysis, seed=seed)
        results.append(opp)
    results.sort(key=lambda o: abs(float(o.get("gross_spread_bps", 0))), reverse=True)
    return results


def _to_unified_opportunity(analysis: dict[str, Any], *, seed: dict[str, Any]) -> dict[str, Any]:
    """Map monitor output to #429 canonical opportunity schema."""
    asset = analysis["asset"]
    basis_pct = float(analysis.get("spot_perp_basis_pct", 0))
    gross_bps = round(abs(basis_pct) * 100, 4)  # % to bps approx for ranking
    quote_usd = 1000.0

    try:
        from bd_platform.spread_calculation_engine import compute_arbitrage_economics

        econ = compute_arbitrage_economics(
            gross_spread_bps=gross_bps,
            quote_usd=quote_usd,
            trading_fee_bps=float((seed.get("holding_cost_components") or {}).get("fees_pct", 0.12)) * 100,
            slippage_bps=4.0,
            leg_count=2,
        )
        net_edge_usdt = float(econ.get("net_edge_usdt", 0))
        net_edge_bps = float(econ.get("net_edge_bps", 0))
    except Exception:
        logger.debug("economics enrichment skipped", exc_info=True)
        net_edge_usdt = 0.0
        net_edge_bps = 0.0
        econ = {}

    fh = analysis.get("funding_vs_holding_cost") or {}
    display = (
        f"{asset} basis {basis_pct:+.3f}% | funding APY {analysis.get('funding_rate_apy', 0):+.2f}% | "
        f"7d funding vs holding cost {fh.get('net_after_holding_cost_pct', 0):+.3f}% (monitoring)"
    )

    return {
        "opportunity_id": f"deriv_{asset.lower()}_{analysis.get('venue', 'unknown')}",
        "opportunity_type": "derivatives_basis_funding",
        "feature_ref": _FEATURE_ID,
        "legal_name": _LEGAL_NAME,
        "category": _CATEGORY,
        "asset": asset,
        "symbol": f"{asset}/USDT",
        "venue": analysis.get("venue"),
        "gross_spread_bps": gross_bps,
        "net_edge_usdt": net_edge_usdt,
        "net_edge_bps": net_edge_bps,
        "quote_usd": quote_usd,
        "basis_funding_monitor_440": analysis,
        "spot_perp_basis_pct": basis_pct,
        "funding_rate_apy": analysis.get("funding_rate_apy"),
        "calendar_spread_pct": (analysis.get("calendar_spread") or {}).get("calendar_spread_pct"),
        "implied_holding_cost_pct": analysis.get("implied_holding_cost_pct"),
        "funding_vs_holding_cost": fh,
        "economics_engine_ref": 427,
        "economics": econ,
        "monitoring_only": True,
        "no_auto_execution": True,
        "no_position_simulation_v1": True,
        "simulation_only": True,
        "display": display,
    }


def build_divergence_panel(
    asset: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    if asset:
        items = [analyze_asset_divergence(asset, seed=seed)]
    else:
        items = [analyze_asset_divergence(a, seed=seed) for a in (seed.get("assets") or {})]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "category": _CATEGORY,
        "analyses": [i for i in items if i.get("ok")],
        "count": sum(1 for i in items if i.get("ok")),
        "cancelled_sla": seed.get("cancelled_sla"),
        "monitoring_only": True,
        "no_position_simulation_v1": seed.get("no_position_simulation_v1", True),
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def basis_funding_divergence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "category": _CATEGORY,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "monitoring_only": True,
        "no_position_simulation_v1": seed.get("no_position_simulation_v1", True),
        "outputs": [
            "spot_perp_basis_pct",
            "funding_rate_apy",
            "calendar_spread_pct",
            "implied_holding_cost_pct",
            "funding_vs_holding_cost",
            "index_derivative_basis_pct",
        ],
        "cancelled_sla": seed.get("cancelled_sla"),
        "banned_language": seed.get("banned_language"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "429 merge"})
    checks.append({"id": "renamed_monitor", "passed": "Arbitrage" not in seed.get("legal_name", ""), "detail": seed.get("legal_name")})
    checks.append({"id": "no_position_sim_v1", "passed": seed.get("no_position_simulation_v1") is True, "detail": "v1"})
    checks.append({"id": "sla_cancelled", "passed": (seed.get("cancelled_sla") or {}).get("accuracy_95_pct") is True, "detail": "SLA"})

    btc = analyze_asset_divergence("BTC", seed=seed)
    checks.append({"id": "spot_perp_basis", "passed": "spot_perp_basis_pct" in btc, "detail": str(btc.get("spot_perp_basis_pct"))})
    checks.append({"id": "funding_apy", "passed": "funding_rate_apy" in btc, "detail": str(btc.get("funding_rate_apy"))})
    checks.append({"id": "calendar_spread", "passed": btc.get("calendar_spread") is not None, "detail": "term structure"})
    checks.append({"id": "holding_cost", "passed": btc.get("implied_holding_cost_pct") is not None, "detail": "cost"})
    checks.append({"id": "funding_vs_holding", "passed": btc.get("funding_vs_holding_cost", {}).get("no_position_simulation_v1") is True, "detail": "440"})

    opps = scan_derivatives_divergence(seed=seed)
    checks.append({"id": "unified_opportunity_schema", "passed": len(opps) >= 1 and opps[0].get("feature_ref") == 440, "detail": f"count={len(opps)}"})

    display = opps[0].get("display", "").lower() if opps else ""
    checks.append({
        "id": "no_execution_language",
        "passed": not any(term in display for term in ("buy", "sell", "open position", "execute")),
        "detail": "banned terms",
    })

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
