"""Registry for the locked 70-capability closure scope."""

from __future__ import annotations

from typing import Any, Literal

CapabilityState = Literal["PARTIAL", "NOT_PRESENT", "VERIFIED_OUT_OF_SCOPE"]

PARTIAL_IDS: tuple[str, ...] = (
    "CAP-03",
    "CAP-05",
    "CAP-07",
    "CAP-08",
    "CAP-09",
    "CAP-10",
    "CAP-11",
    "CAP-12",
    "CAP-13",
    "CAP-15",
    "CAP-16",
    "CAP-19",
    "CAP-20",
    "CAP-22",
    "CAP-24",
    "CAP-25",
    "CAP-26",
    "CAP-28",
    "CAP-34",
    "CAP-35",
    "CAP-36",
    "CAP-37",
    "CAP-38",
    "CAP-39",
    "CAP-41",
    "CAP-43",
    "CAP-44",
    "CAP-45",
    "CAP-46",
    "CAP-47",
    "CAP-48",
    "CAP-49",
    "CAP-50",
    "CAP-53",
    "CAP-55",
    "CAP-58",
    "CAP-59",
    "CAP-60",
    "CAP-63",
    "CAP-67",
    "CAP-68",
    "CAP-70",
    "CAP-72",
    "CAP-75",
    "EC-03",
    "EC-04",
    "EC-06",
    "EC-09",
    "EC-10",
    "UX-01",
    "UX-03",
)

NOT_PRESENT_IDS: tuple[str, ...] = (
    "CAP-01",
    "CAP-02",
    "CAP-04",
    "CAP-06",
    "CAP-14",
    "CAP-17",
    "CAP-18",
    "CAP-21",
    "CAP-23",
    "CAP-27",
    "CAP-40",
    "CAP-51",
    "CAP-52",
    "CAP-54",
    "CAP-73",
    "CAP-74",
    "EC-01",
    "EC-07",
    "UX-02",
)

VERIFIED_OUT_OF_SCOPE_IDS: tuple[str, ...] = (
    "CAP-29",
    "CAP-30",
    "CAP-31",
    "CAP-32",
    "CAP-33",
    "CAP-42",
    "CAP-56",
    "CAP-57",
    "CAP-61",
    "CAP-62",
    "CAP-64",
    "CAP-65",
    "CAP-66",
    "CAP-69",
    "CAP-71",
    "EC-02",
    "EC-05",
    "EC-08",
    "UX-04",
)

CAPABILITY_NAMES: dict[str, str] = {
    "CAP-01": "Amihud Illiquidity Ratio",
    "CAP-02": "Kyle's Lambda",
    "CAP-03": "Slippage Impact Vector",
    "CAP-04": "VWAP Deviation Index",
    "CAP-05": "Volume-Velocity Tracker",
    "CAP-06": "Order Cancellation Velocity",
    "CAP-07": "VaR 99%",
    "CAP-08": "CVaR / Expected Shortfall",
    "CAP-09": "Monte Carlo Probabilistic Scenarios",
    "CAP-10": "Sharpe Ratio",
    "CAP-11": "Sortino Ratio",
    "CAP-12": "Maximum Drawdown Duration",
    "CAP-13": "Beta to BTC",
    "CAP-14": "Beta to ETH",
    "CAP-15": "Correlation Decay Matrix",
    "CAP-16": "De-Peg Risk Score",
    "CAP-17": "Large-vs-Small Trade Participation Ratio",
    "CAP-18": "Maker/Taker Net Delta",
    "CAP-19": "OI Momentum Delta",
    "CAP-20": "Funding Momentum Shift",
    "CAP-21": "Derivative-to-Spot Volume Multiple",
    "CAP-22": "Effective Basis Yield",
    "CAP-23": "Delta-Neutral Validator",
    "CAP-24": "Funding Spread Matrix",
    "CAP-25": "Estimated Liquidation Cascade Risk",
    "CAP-26": "IV Skew",
    "CAP-27": "Put/Call Ratio",
    "CAP-28": "NVT",
    "CAP-34": "Opportunity Score 0–100",
    "CAP-35": "Opportunity Score Explanation",
    "CAP-36": "Opportunity Lifetime Tracker",
    "CAP-37": "Opportunity Survival / Decay Model",
    "CAP-38": "Historical Opportunity Disappearance Ledger",
    "CAP-39": "Required-Size Liquidity Gate",
    "CAP-40": "Order-Book Integrity / Anti-Spoofing Gate",
    "CAP-41": "Per-Source / Per-Feature Freshness SLO",
    "CAP-43": "Time-Sync / Clock-Skew Detection",
    "CAP-44": "Venue Trading-Status Gate",
    "CAP-45": "Network Compatibility Validator",
    "CAP-46": "New-Asset Probation / Confidence Gate",
    "CAP-47": "User Capital Constraint",
    "CAP-48": "User Risk Constraint",
    "CAP-49": "Paper Trading Engine",
    "CAP-50": "Opportunity Snapshot-at-Detection",
    "CAP-51": "Expected-vs-Simulated Execution Reconciliation",
    "CAP-52": "Expected-vs-Observed Slippage Reconciliation",
    "CAP-53": "Opportunity Failure Classification",
    "CAP-54": "Executable Opportunity Ratio",
    "CAP-55": "Prediction / Opportunity Outcome Reconciliation",
    "CAP-58": "Opportunity Explainability",
    "CAP-59": "Missing-Evidence Disclosure",
    "CAP-60": "Performance Evidence Type",
    "CAP-63": "Opportunity / Decision Audit Trail",
    "CAP-67": "End-to-End Trace ID",
    "CAP-68": "Exponential Backoff + Jitter",
    "CAP-70": "Upstream Cost Guard",
    "CAP-72": "Network Health Matrix",
    "CAP-73": "M2 Liquidity Context",
    "CAP-74": "Interest-Rate / Monetary Policy Context",
    "CAP-75": "Fear & Greed Context",
    "EC-01": "Selective Mutation Testing for Critical Paths",
    "EC-03": "Chaos / Failure Injection Testing",
    "EC-04": "Release Intelligence Quality Gate",
    "EC-06": "Tiered Hot/Warm/Cold Retention Architecture",
    "EC-07": "Anomaly Labels + Calibrated Normal-State Training Sample",
    "EC-09": "WebSocket Lifecycle & Reconnect Reliability",
    "EC-10": "Venue Progressive Rollout / Certification",
    "UX-01": "Calm Decision Surface",
    "UX-02": "Complete Opportunity Card",
    "UX-03": "Progressive Disclosure",
}


def scoped_capability_ids() -> list[str]:
    return list(PARTIAL_IDS) + list(NOT_PRESENT_IDS)


def _build_registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for cap_id in PARTIAL_IDS:
        registry[cap_id] = {
            "id": cap_id,
            "name": CAPABILITY_NAMES[cap_id],
            "original_state": "PARTIAL",
            "methodology_version": "capability_spine_v1",
        }
    for cap_id in NOT_PRESENT_IDS:
        registry[cap_id] = {
            "id": cap_id,
            "name": CAPABILITY_NAMES[cap_id],
            "original_state": "NOT_PRESENT",
            "methodology_version": "capability_spine_v1",
        }
    return registry


CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = _build_registry()

assert len(PARTIAL_IDS) == 51
assert len(NOT_PRESENT_IDS) == 19
assert len(scoped_capability_ids()) == 70
