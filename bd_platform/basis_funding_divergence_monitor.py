"""
Basis Divergence Scanner — Feature #440 (merged into #429).

Renamed from "Derivatives & Futures Arbitrage" / ambiguous "عقود" monitoring.
Spot vs perpetual basis monitoring — analytics only, no execution.

Displays per row:
  Spot Price | Perp Price | Basis % (gross) | Funding Rate (8h) | Net Basis (after fees) | Feasibility

Net Basis = gross basis − funding accumulation − entry fees − exit fees − slippage.
Signal suppressed when Net Basis ≤ 0.

Data pipeline via #146 Intermediate Data Store (invisible engineering layer).
NOT standalone — Unified Arbitrage Engine category.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.BasisDivergenceScanner")

_FEATURE_ID = 440
_INFRA_FEATURE_ID = 146
_TITLE = "Basis Divergence Scanner"
_LEGAL_NAME = "Basis Divergence Scanner"
_RENAMED_FROM = "Derivatives & Futures Arbitrage"
_STANDALONE = False
_MERGED_INTO = "Unified Arbitrage Engine (#429) / Derivatives Arbitrage"
_CATEGORY = "derivatives_arbitrage"
_SPRINT = 2
_PRIORITY = "medium"
_SEED_PATH = Path("data/basis_funding_divergence_seed.json")
_METHODOLOGY_VERSION = "1.1"

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
    "Basis Divergence Scanner — spot vs perpetual monitoring only. "
    "Shows gross basis, 8h funding, net basis after fees, and fill feasibility. "
    "Monitoring only — no execution, not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("basis divergence seed load failed: %s", exc)
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


def _funding_rate_8h_pct(funding_rate: float, interval_hours: float) -> float:
    """Funding accumulation for one 8h window — expressed as % of notional."""
    if interval_hours <= 0:
        return 0.0
    rate_8h = funding_rate * (8.0 / interval_hours)
    return round(rate_8h * 100, 4)


def _cost_components(seed: dict[str, Any]) -> dict[str, float]:
    comp = seed.get("holding_cost_components") or {}
    fees = float(comp.get("fees_pct", 0.12))
    return {
        "entry_fees_pct": float(comp.get("entry_fees_pct", fees / 2)),
        "exit_fees_pct": float(comp.get("exit_fees_pct", fees / 2)),
        "slippage_pct": float(comp.get("slippage_pct", 0.04)),
        "borrow_cost_pct": float(comp.get("borrow_cost_pct", 0.05)),
        "basis_risk_penalty_pct": float(comp.get("basis_risk_penalty_pct", 0.02)),
    }


def compute_net_basis(
    *,
    gross_basis_pct: float,
    funding_rate: float,
    funding_interval_hours: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Net Basis = gross basis − funding accumulation − entry fees − exit fees − slippage.
    Signal active only when net_basis_pct > 0.
    """
    seed = seed or _load_seed()
    costs = _cost_components(seed)
    funding_accum_pct = _funding_rate_8h_pct(funding_rate, funding_interval_hours)
    net = round(
        gross_basis_pct
        - funding_accum_pct
        - costs["entry_fees_pct"]
        - costs["exit_fees_pct"]
        - costs["slippage_pct"],
        4,
    )
    return {
        "gross_basis_pct": gross_basis_pct,
        "funding_accumulation_8h_pct": funding_accum_pct,
        "entry_fees_pct": costs["entry_fees_pct"],
        "exit_fees_pct": costs["exit_fees_pct"],
        "slippage_pct": costs["slippage_pct"],
        "net_basis_pct": net,
        "signal_active": net > 0,
        "signal_suppressed_reason": None if net > 0 else "net_basis_non_positive",
        "formula": "gross_basis - funding_8h - entry_fees - exit_fees - slippage",
        "price_deviation_accuracy": "±0.05%",
        "near_real_time": True,
    }


def _implied_holding_cost_pct(seed: dict[str, Any]) -> float:
    comp = _cost_components(seed)
    total = comp["entry_fees_pct"] + comp["exit_fees_pct"] + comp["slippage_pct"] + comp["borrow_cost_pct"] + comp["basis_risk_penalty_pct"]
    return round(total, 4)


def _calendar_spread_pct(contracts: list[dict[str, Any]]) -> dict[str, Any] | None:
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


def _build_feasibility_display(
    *,
    net_basis: dict[str, Any],
    proposed_position_usd: float,
    max_executable_usd: float | None = None,
) -> dict[str, Any]:
    """#415 fill feasibility hook — display-only sizing context."""
    executable = max_executable_usd if max_executable_usd is not None else proposed_position_usd * 0.85
    executable = min(executable, proposed_position_usd)
    gross = float(net_basis.get("gross_basis_pct", 0))
    net = float(net_basis.get("net_basis_pct", 0))
    display = (
        f"الفارق {gross:.2f}% | بعد التكاليف {net:.2f}% | "
        f"حجم قابل للتنفيذ: ${executable:,.0f}"
    )
    display_en = (
        f"Gross basis {gross:.2f}% | Net after costs {net:.2f}% | "
        f"Executable size: ${executable:,.0f}"
    )
    return {
        "proposed_position_usd": proposed_position_usd,
        "max_executable_usd": round(executable, 2),
        "verdict": "feasible" if net > 0 and executable > 0 else "not_feasible",
        "monitoring_only": True,
        "no_auto_execution": True,
        "display": display,
        "display_en": display_en,
    }


def _evaluate_risk_alert(
    *,
    gross_basis_pct: float,
    net_basis: dict[str, Any],
    seed: dict[str, Any],
) -> dict[str, Any]:
    """#410 — alert when gross basis exceeds threshold but net edge / risk context is weak."""
    cfg = seed.get("risk_alert_config") or {}
    gross_threshold = float(cfg.get("gross_basis_alert_threshold_pct", 0.5))
    high_risk_score = float(cfg.get("high_risk_score_threshold", 70))
    risk_score = float(cfg.get("default_risk_score", 45))
    if abs(gross_basis_pct) >= gross_threshold and not net_basis.get("signal_active"):
        risk_score = max(risk_score, high_risk_score + 5)
    alert = abs(gross_basis_pct) >= gross_threshold and risk_score >= high_risk_score
    message = None
    if alert and net_basis.get("signal_active"):
        message = "فرصة لكن مخاطرة — gross basis elevated with elevated risk context"
    elif alert:
        message = "فرصة لكن مخاطرة — basis divergence exceeds threshold; net basis non-positive"
    return {
        "alert": alert,
        "risk_score": risk_score,
        "gross_basis_threshold_pct": gross_threshold,
        "message": message,
        "worth_studying_not_execution": True,
        "feature_ref": 410,
    }


def _scanner_row(
    *,
    asset: str,
    spot: float,
    perp: float,
    funding_rate: float,
    interval_h: float,
    net_basis: dict[str, Any],
    feasibility: dict[str, Any],
    venue: str | None,
) -> dict[str, Any]:
    """Canonical scanner row — Spot | Perp | Basis gross | Funding 8h | Net | Feasibility."""
    funding_8h = _funding_rate_8h_pct(funding_rate, interval_h)
    return {
        "asset": asset.upper(),
        "venue": venue,
        "spot_price": spot,
        "perp_price": perp,
        "basis_gross_pct": net_basis["gross_basis_pct"],
        "funding_rate_8h_pct": funding_8h,
        "net_basis_pct": net_basis["net_basis_pct"],
        "feasibility": feasibility,
        "signal_active": net_basis["signal_active"],
        "columns": [
            "spot_price",
            "perp_price",
            "basis_gross_pct",
            "funding_rate_8h_pct",
            "net_basis_pct",
            "feasibility",
        ],
    }


def _hydrate_from_data_store(asset: str, raw: dict[str, Any]) -> dict[str, Any]:
    """#146 — ingest normalized snapshot (warm tier); seed remains fallback."""
    try:
        from bd_platform.intermediate_data_store import ingest_basis_market_batch

        ingest_basis_market_batch([{**raw, "asset": asset}])
    except Exception:
        logger.debug("intermediate data store hydrate skipped", exc_info=True)
    return raw


def analyze_asset_divergence(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    raw = (seed.get("assets") or {}).get(asset.upper())
    if not raw:
        return {"ok": False, "error": "asset_not_found", "asset": asset}

    raw = _hydrate_from_data_store(asset, raw)
    spot = float(raw.get("spot_price", 0))
    perp = float(raw.get("perp_price", 0))
    index = float(raw.get("index_price", 0))
    funding_rate = float(raw.get("funding_rate", 0))
    interval_h = float(raw.get("funding_interval_hours", seed.get("funding_interval_hours_default", 8)))
    holding_cost = _implied_holding_cost_pct(seed)
    cumulative_7d = float(raw.get("cumulative_funding_7d_pct", 0))
    proposed_usd = float(raw.get("proposed_position_usd", seed.get("default_proposed_position_usd", 5000)))

    basis_pct = _spot_perp_basis_pct(spot, perp)
    net_basis = compute_net_basis(
        gross_basis_pct=basis_pct,
        funding_rate=funding_rate,
        funding_interval_hours=interval_h,
        seed=seed,
    )
    max_exec = float(raw.get("max_executable_usd", proposed_usd * float(raw.get("executable_ratio", 0.85))))
    feasibility = _build_feasibility_display(
        net_basis=net_basis,
        proposed_position_usd=proposed_usd,
        max_executable_usd=max_exec,
    )
    risk_alert = _evaluate_risk_alert(gross_basis_pct=basis_pct, net_basis=net_basis, seed=seed)
    scanner_row = _scanner_row(
        asset=asset,
        spot=spot,
        perp=perp,
        funding_rate=funding_rate,
        interval_h=interval_h,
        net_basis=net_basis,
        feasibility=feasibility,
        venue=raw.get("venue"),
    )

    funding_apy = _funding_rate_apy(funding_rate, interval_h)
    calendar = _calendar_spread_pct(raw.get("calendar_contracts") or [])
    perp_q = _perp_quarterly_spread(raw)
    index_basis = _index_derivative_basis_pct(index, perp)
    funding_holding = _funding_vs_holding_cost(cumulative_7d, holding_cost)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "infra_feature_ref": _INFRA_FEATURE_ID,
        "opportunity_type": "derivatives_basis_funding",
        "category": _CATEGORY,
        "legal_name": _LEGAL_NAME,
        "asset": asset.upper(),
        "venue": raw.get("venue"),
        "scanner_row": scanner_row,
        "spot_perp_basis_pct": basis_pct,
        "basis_gross_pct": basis_pct,
        "funding_rate_8h_pct": scanner_row["funding_rate_8h_pct"],
        "net_basis": net_basis,
        "net_basis_pct": net_basis["net_basis_pct"],
        "signal_active": net_basis["signal_active"],
        "feasibility": feasibility,
        "risk_alert_410": risk_alert,
        "funding_rate_apy": funding_apy,
        "calendar_spread": calendar,
        "perp_quarterly_spread": perp_q,
        "index_derivative_basis_pct": index_basis,
        "implied_holding_cost_pct": holding_cost,
        "funding_vs_holding_cost": funding_holding,
        "proposed_position_usd": proposed_usd,
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
    active_only: bool = True,
) -> list[dict[str, Any]]:
    """#440 — scan assets; suppress opportunities with net_basis ≤ 0 when active_only."""
    seed = seed or _load_seed()
    targets = assets or list((seed.get("assets") or {}).keys())
    results = []
    for asset in targets:
        analysis = analyze_asset_divergence(asset, seed=seed)
        if not analysis.get("ok"):
            continue
        if active_only and not analysis.get("signal_active"):
            continue
        opp = _to_unified_opportunity(analysis, seed=seed)
        results.append(opp)
    results.sort(key=lambda o: float(o.get("net_basis_pct", 0)), reverse=True)
    return results


def _to_unified_opportunity(analysis: dict[str, Any], *, seed: dict[str, Any]) -> dict[str, Any]:
    """Map scanner output to #429 canonical opportunity schema."""
    asset = analysis["asset"]
    basis_pct = float(analysis.get("spot_perp_basis_pct", 0))
    net_basis_pct = float(analysis.get("net_basis_pct", 0))
    gross_bps = round(abs(basis_pct) * 100, 4)
    quote_usd = float(analysis.get("proposed_position_usd", 5000))
    venue = str(analysis.get("venue") or "unknown")

    try:
        from bd_platform.spread_calculation_engine import compute_arbitrage_economics

        costs = _cost_components(seed)
        econ = compute_arbitrage_economics(
            gross_spread_bps=gross_bps,
            quote_usd=quote_usd,
            trading_fee_bps=costs["entry_fees_pct"] * 100,
            slippage_bps=costs["slippage_pct"] * 100,
            leg_count=2,
        )
        net_edge_usdt = float(econ.get("net_edge_usdt", 0))
        net_edge_bps = float(econ.get("net_edge_bps", 0))
    except Exception:
        logger.debug("economics enrichment skipped", exc_info=True)
        net_edge_usdt = round(quote_usd * net_basis_pct / 100, 4)
        net_edge_bps = round(net_basis_pct * 100, 4)
        econ = {}

    feasibility = analysis.get("feasibility") or {}
    display = feasibility.get("display_en") or (
        f"{asset} basis {basis_pct:+.3f}% | net {net_basis_pct:+.3f}% (monitoring)"
    )

    return {
        "opportunity_id": f"deriv_{asset.lower()}_{venue}",
        "opportunity_type": "derivatives_basis_funding",
        "feature_ref": _FEATURE_ID,
        "legal_name": _LEGAL_NAME,
        "category": _CATEGORY,
        "asset": asset,
        "symbol": f"{asset}/USDT",
        "venue": venue,
        "buy_venue": f"{venue}_spot",
        "sell_venue": f"{venue}_perp",
        "gross_spread_bps": gross_bps,
        "net_edge_usdt": net_edge_usdt,
        "net_edge_bps": net_edge_bps,
        "net_basis_pct": net_basis_pct,
        "quote_usd": quote_usd,
        "basis_divergence_scanner_440": analysis,
        "scanner_row": analysis.get("scanner_row"),
        "spot_perp_basis_pct": basis_pct,
        "basis_gross_pct": basis_pct,
        "funding_rate_8h_pct": analysis.get("funding_rate_8h_pct"),
        "funding_rate_apy": analysis.get("funding_rate_apy"),
        "feasibility": feasibility,
        "risk_alert_410": analysis.get("risk_alert_410"),
        "calendar_spread_pct": (analysis.get("calendar_spread") or {}).get("calendar_spread_pct"),
        "implied_holding_cost_pct": analysis.get("implied_holding_cost_pct"),
        "funding_vs_holding_cost": analysis.get("funding_vs_holding_cost"),
        "economics_engine_ref": 427,
        "economics": econ,
        "signal_active": analysis.get("signal_active"),
        "monitoring_only": True,
        "no_auto_execution": True,
        "no_position_simulation_v1": True,
        "simulation_only": True,
        "display": display,
    }


def build_basis_monitor_widget(
    *,
    limit: int = 5,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Market Radar widget — top-N basis opportunities (#440 / #429 integration)."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    rows: list[dict[str, Any]] = []
    for asset in (seed.get("assets") or {}):
        analysis = analyze_asset_divergence(asset, seed=seed)
        if not analysis.get("ok"):
            continue
        row = dict(analysis.get("scanner_row") or {})
        row["rank_score"] = float(analysis.get("net_basis_pct", 0))
        row["risk_alert"] = analysis.get("risk_alert_410")
        rows.append(row)
    rows.sort(key=lambda r: r.get("rank_score", 0), reverse=True)
    top = rows[:limit]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "widget": "Basis Monitor",
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "legal_name": _LEGAL_NAME,
        "top_opportunities": top,
        "count": len(top),
        "limit": limit,
        "columns": [
            "spot_price",
            "perp_price",
            "basis_gross_pct",
            "funding_rate_8h_pct",
            "net_basis_pct",
            "feasibility",
        ],
        "near_real_time": True,
        "monitoring_only": True,
        "no_auto_execution": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
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
    ok_items = [i for i in items if i.get("ok")]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "category": _CATEGORY,
        "analyses": ok_items,
        "scanner_rows": [i.get("scanner_row") for i in ok_items if i.get("scanner_row")],
        "count": len(ok_items),
        "cancelled_sla": seed.get("cancelled_sla"),
        "acceptance": seed.get("acceptance"),
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
        "infra_feature_ref": _INFRA_FEATURE_ID,
        "monitoring_only": True,
        "no_position_simulation_v1": seed.get("no_position_simulation_v1", True),
        "outputs": [
            "spot_price",
            "perp_price",
            "basis_gross_pct",
            "funding_rate_8h_pct",
            "net_basis_pct",
            "feasibility",
            "calendar_spread_pct",
            "funding_vs_holding_cost",
        ],
        "cancelled_sla": seed.get("cancelled_sla"),
        "acceptance": seed.get("acceptance"),
        "banned_language": seed.get("banned_language"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


# Backward-compatible alias
basis_divergence_scanner_status = basis_funding_divergence_status


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "429 merge"})
    checks.append({"id": "renamed_scanner", "passed": seed.get("legal_name") == _LEGAL_NAME, "detail": seed.get("legal_name")})
    checks.append({"id": "no_position_sim_v1", "passed": seed.get("no_position_simulation_v1") is True, "detail": "v1"})
    checks.append({"id": "near_real_time_sla", "passed": (seed.get("acceptance") or {}).get("near_real_time") is True, "detail": "SLA"})

    btc = analyze_asset_divergence("BTC", seed=seed)
    checks.append({"id": "scanner_row_columns", "passed": "scanner_row" in btc and "net_basis_pct" in (btc.get("scanner_row") or {}), "detail": "columns"})
    checks.append({"id": "net_basis_formula", "passed": btc.get("net_basis", {}).get("formula") is not None, "detail": "net basis"})
    checks.append({"id": "signal_active_btc", "passed": btc.get("signal_active") is True, "detail": str(btc.get("net_basis_pct"))})
    checks.append({"id": "feasibility_415", "passed": (btc.get("feasibility") or {}).get("max_executable_usd", 0) > 0, "detail": "fill size"})
    checks.append({"id": "risk_alert_410", "passed": "risk_alert_410" in btc, "detail": "risk hook"})
    checks.append({"id": "funding_8h", "passed": btc.get("funding_rate_8h_pct") is not None, "detail": "8h funding"})
    checks.append({"id": "calendar_spread", "passed": btc.get("calendar_spread") is not None, "detail": "term structure"})

    opps = scan_derivatives_divergence(seed=seed, active_only=True)
    checks.append({"id": "unified_opportunity_schema", "passed": len(opps) >= 1 and opps[0].get("feature_ref") == 440, "detail": f"count={len(opps)}"})
    checks.append({"id": "buy_sell_venues_429", "passed": bool(opps[0].get("buy_venue") and opps[0].get("sell_venue")), "detail": "415 hook"})

    display = opps[0].get("display", "").lower() if opps else ""
    checks.append({
        "id": "no_execution_language",
        "passed": not any(term in display for term in ("buy", "sell", "open position", "execute")),
        "detail": "banned terms",
    })

    widget = build_basis_monitor_widget(limit=5, seed=seed)
    checks.append({"id": "market_radar_widget", "passed": widget.get("count", 0) >= 1, "detail": f"top={widget.get('count')}"})

    try:
        from bd_platform.intermediate_data_store import run_reconciliation_tests as ids_tests

        ids = ids_tests()
        checks.append({"id": "infra_146", "passed": ids.get("ok") is True, "detail": f"{ids.get('passed')}/{ids.get('total')}"})
    except Exception:
        checks.append({"id": "infra_146", "passed": False, "detail": "import failed"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
