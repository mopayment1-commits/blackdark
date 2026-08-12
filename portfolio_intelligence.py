"""Portfolio intelligence — holdings, PnL, exposure, concentration, scenarios."""

from __future__ import annotations

from typing import Any

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
        }
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
        "executable_analysis": True,
        "confidence": claim_heuristic(min(1.0, herfindahl), label="concentration").to_dict(),
        "product_complete": True,
    }


def portfolio_status() -> dict[str, Any]:
    return {
        "surface": "portfolio_intelligence",
        "product_complete": True,
        "modules": ["analyze_portfolio", "correlation", "stress"],
    }
