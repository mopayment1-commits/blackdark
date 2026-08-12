"""Portfolio intelligence — holdings, PnL, exposure, concentration, scenarios."""

from __future__ import annotations

from typing import Any

from canonical_adoption import adopt_positions
from confidence_truth import claim_heuristic, claim_insufficient
from risk_intelligence import correlation_contagion_risk, stress_test_portfolio


def analyze_portfolio(positions: list[dict[str, Any]]) -> dict[str, Any]:
    if not positions:
        return {
            "holdings": 0,
            "gross_exposure_usd": 0.0,
            "net_exposure_usd": 0.0,
            "pnl_usd": 0.0,
            "concentration": {},
            "executable_analysis": False,
            "reason": "no_positions",
            "confidence": claim_insufficient(label="portfolio").to_dict(),
            "canonical_adopted": True,
        }
    positions = adopt_positions(positions, source="portfolio_intelligence")
    gross = 0.0
    net = 0.0
    pnl = 0.0
    by_asset: dict[str, float] = {}
    for p in positions:
        notional = p.get("notional_usd")
        if notional is None:
            return {
                "holdings": len(positions),
                "executable_analysis": False,
                "reason": "notional_unknown",
                "confidence": claim_insufficient(label="portfolio").to_dict(),
                "canonical_adopted": True,
            }
        n = float(notional)
        side = str(p.get("side") or "long").lower()
        signed = n if side == "long" else -n
        gross += abs(n)
        net += signed
        pnl += float(p.get("unrealized_pnl_usd") or 0.0)
        asset = str(p.get("asset") or p.get("symbol") or "UNK")
        by_asset[asset] = by_asset.get(asset, 0.0) + abs(n)

    conc = {a: round(v / gross, 6) if gross else 0.0 for a, v in by_asset.items()}
    herfindahl = sum(v * v for v in conc.values())
    corr = correlation_contagion_risk(positions=positions)
    stress = stress_test_portfolio(positions=positions, shock_bps=-1500)
    blocked = (not corr.get("executable", True)) or (stress.get("gate") == "fail_closed")
    return {
        "holdings": len(positions),
        "gross_exposure_usd": round(gross, 4),
        "net_exposure_usd": round(net, 4),
        "pnl_usd": round(pnl, 4),
        "concentration": conc,
        "herfindahl": round(herfindahl, 6),
        "correlation": corr,
        "stress": stress,
        "liquidity_note": "exitability requires venue depth probes (whale_execution_evidence)",
        "decision_relevance": True,
        "executable_analysis": not blocked,
        "gate": "block" if blocked else "pass",
        "confidence": claim_heuristic(min(1.0, herfindahl), label="concentration").to_dict(),
        "canonical_adopted": True,
        "product_complete": True,
    }


def holdings_from_dashboard_assets(assets: list[Any]) -> list[dict[str, Any]]:
    """Map dashboard /portfolio/analyze body into institutional position rows."""
    positions: list[dict[str, Any]] = []
    for item in assets or []:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or item.get("asset") or "").strip()
        if not symbol:
            continue
        qty = float(item.get("quantity") or item.get("amount") or item.get("qty") or 0)
        price = float(item.get("price") or item.get("mark_price") or item.get("avg_price") or 0)
        notional = item.get("notional_usd")
        if notional is None and qty and price:
            notional = qty * price
        if notional is None and item.get("value_usd") is not None:
            notional = item.get("value_usd")
        positions.append(
            {
                "asset": symbol.split("/")[0].upper() if symbol else "UNK",
                "symbol": symbol.upper(),
                "side": str(item.get("side") or "long").lower(),
                "notional_usd": float(notional) if notional is not None else None,
                "unrealized_pnl_usd": float(item.get("unrealized_pnl_usd") or item.get("pnl") or 0),
                "venue": item.get("venue") or item.get("exchange"),
            }
        )
    return positions


def portfolio_status() -> dict[str, Any]:
    return {
        "surface": "portfolio_intelligence",
        "product_complete": True,
        "modules": ["analyze_portfolio", "correlation", "stress", "canonical_adoption"],
        "api": ["/portfolio/analyze", "/api/institutional/portfolio/analyze"],
    }
