"""
BLACKDARK — Execution Risk % (0–100) for arb opportunities.

Complementary to binary risk_manager.evaluate_execution_risk() gate.
Higher score = more dangerous / less executable.
"""

from __future__ import annotations

from typing import Any


def score_execution_risk(opportunity: dict[str, Any] | None) -> dict[str, Any]:
    """Return execution_risk_pct and component breakdown."""
    opp = opportunity or {}
    slippage = float(opp.get("total_slippage_bps") or opp.get("slippage_bps") or 0)
    data_age = float(opp.get("data_age_sec") or opp.get("quote_age_sec") or 0)
    feasibility = str(opp.get("execution_feasibility") or "").lower()
    net = float(opp.get("net_profit_usdt") or opp.get("net_profit") or 0)
    risk_factors = list(opp.get("risk_factors") or [])
    confidence = float(opp.get("confidence_percent") or 50)

    # Slippage: 0–40
    slip_score = min(40.0, (slippage / 100.0) * 40.0)
    # Staleness: 0–25 ( >5s starts hurting; >30s maxes)
    age_score = 0.0
    if data_age > 0:
        age_score = min(25.0, (data_age / 30.0) * 25.0)
    # Feasibility label: 0–20
    feas_map = {
        "high": 0.0,
        "medium": 10.0,
        "low": 18.0,
        "blocked": 20.0,
        "rejected": 20.0,
    }
    feas_score = feas_map.get(feasibility, 8.0)
    # Thin edge / negative: 0–10
    if net > 5:
        edge_score = 0.0
    elif net > 0:
        edge_score = 5.0
    else:
        edge_score = 10.0
    # Extra risk factors: 0–5
    factor_score = min(5.0, float(len(risk_factors)) * 1.5)
    # Low confidence adds risk: 0–10
    conf_score = max(0.0, (60.0 - confidence) / 60.0 * 10.0)

    total = slip_score + age_score + feas_score + edge_score + factor_score + conf_score
    pct = round(min(100.0, max(0.0, total)), 1)

    if pct < 25:
        band = "low"
    elif pct < 50:
        band = "moderate"
    elif pct < 75:
        band = "elevated"
    else:
        band = "high"

    return {
        "execution_risk_pct": pct,
        "execution_risk_band": band,
        "components": {
            "slippage": round(slip_score, 1),
            "staleness": round(age_score, 1),
            "feasibility": round(feas_score, 1),
            "edge": round(edge_score, 1),
            "risk_factors": round(factor_score, 1),
            "confidence": round(conf_score, 1),
        },
        "note": "Advisory score — binary kill-switch still applies via evaluate_execution_risk().",
    }


def attach_execution_risk(row: dict[str, Any]) -> dict[str, Any]:
    scored = score_execution_risk(row)
    row = dict(row)
    row["execution_risk_pct"] = scored["execution_risk_pct"]
    row["execution_risk_band"] = scored["execution_risk_band"]
    row["execution_risk"] = scored
    return row
