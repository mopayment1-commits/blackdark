"""Expanded stress-testing scenarios for portfolio/system risk."""

from __future__ import annotations

from typing import Any

from confidence_truth import claim_heuristic, claim_insufficient
from risk_intelligence import stress_test_portfolio


SCENARIOS = (
    ("market_crash", -2500),
    ("liquidity_collapse", -1800),
    ("stablecoin_depeg", -800),
    ("flash_crash", -3500),
    ("correlation_breakdown", -1200),
    ("large_position_unwind", -2000),
)


def run_stress_battery(positions: list[dict[str, Any]]) -> dict[str, Any]:
    if not positions:
        return {
            "ok": False,
            "reason": "no_positions",
            "scenarios": [],
            "confidence": claim_insufficient(label="stress").to_dict(),
        }
    rows = []
    blocked = False
    for name, shock in SCENARIOS:
        out = stress_test_portfolio(positions=positions, shock_bps=shock)
        out = {**out, "scenario": name}
        if out.get("gate") == "fail_closed":
            blocked = True
        rows.append(out)
    # Venue outage / protocol failure qualitative gates
    rows.append(
        {
            "scenario": "venue_outage",
            "gate": "warn",
            "executable": True,
            "note": "Isolate venue; reroute via OMS when alternate depth exists",
        }
    )
    rows.append(
        {
            "scenario": "protocol_failure",
            "gate": "block",
            "executable": False,
            "note": "DeFi/CEX-DEX paths must fail closed on protocol halt",
        }
    )
    return {
        "ok": not blocked,
        "scenarios": rows,
        "product_complete": True,
        "confidence": claim_heuristic(0.7, label="stress_battery").to_dict(),
    }


def stress_status() -> dict[str, Any]:
    return {
        "surface": "stress_testing",
        "scenarios": [s[0] for s in SCENARIOS] + ["venue_outage", "protocol_failure"],
        "product_complete": True,
    }
