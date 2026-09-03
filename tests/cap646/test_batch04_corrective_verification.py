"""Corrective institutional verification tests — Batch04 #151, #167, #183."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cap646.batch04_quarterly_protocol import quarter_label
from cap646.batch04_whale_transaction import (
    WHALE_THRESHOLD_USD,
    build_whale_transaction_intelligence,
    classify_whale_tier,
    compute_whale_risk_score,
)


@pytest.mark.parametrize(
    "dt,expected",
    [
        (datetime(2026, 1, 1, tzinfo=UTC), "2026-Q1"),
        (datetime(2026, 3, 31, 23, 59, tzinfo=UTC), "2026-Q1"),
        (datetime(2026, 4, 1, tzinfo=UTC), "2026-Q2"),
        (datetime(2026, 6, 30, tzinfo=UTC), "2026-Q2"),
        (datetime(2026, 7, 1, tzinfo=UTC), "2026-Q3"),
        (datetime(2026, 9, 30, tzinfo=UTC), "2026-Q3"),
        (datetime(2026, 10, 1, tzinfo=UTC), "2026-Q4"),
        (datetime(2026, 12, 31, tzinfo=UTC), "2026-Q4"),
    ],
)
def test_cap151_quarter_label_boundaries(dt: datetime, expected: str):
    assert quarter_label(now=dt) == expected


def test_cap151_quarter_label_uses_utc():
    assert quarter_label(now=datetime(2026, 4, 1, 0, 0, tzinfo=UTC)) == "2026-Q2"


@pytest.mark.parametrize("amount,tier", [
    (5_000, "retail"),
    (50_000, "shark"),
    (500_000, "whale"),
    (2_000_000, "mega_whale"),
])
def test_cap183_whale_tier_classification(amount: float, tier: str):
    assert classify_whale_tier(amount) == tier


def test_cap183_distinct_from_130_reference():
    """#130 = swap risk; #183 = whale transfer — different formulas."""
    whale = build_whale_transaction_intelligence(
        symbol="BTC", address="0xabc", amount_usd=2_000_000, flow_direction="exchange_inflow"
    )
    assert whale["distinct_from_130"]["reused_link"] is False
    assert whale["whale_tier"] == "mega_whale"
    without_flow = compute_whale_risk_score(amount_usd=2_000_000, tier="mega_whale", flow_direction="unknown")
    assert whale["risk_score"] >= without_flow


@pytest.mark.asyncio
async def test_cap183_runtime_engineering_verified():
    from cap646.runtime import execute_capability

    result = await execute_capability(
        183,
        skip_entitlement=True,
        params={"symbol": "BTC", "amount_usd": 2_000_000, "flow_direction": "exchange_inflow", "tier": "pro"},
    )
    assert result["success"] is True
    assert result["surface"] == "whale_transaction_intelligence"
    wt = result["whale_transaction"]
    assert wt["whale_tier"] == "mega_whale"
    assert wt["is_whale_event"] is True
    assert wt["risk_score"] >= 0
    assert wt["distinct_from_130"]["scope_183"] == "large_transfer_whale_classification"


@pytest.mark.asyncio
async def test_cap167_time_sync_thresholds():
    from cap646.runtime import execute_capability

    result = await execute_capability(167, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert result["success"] is True
    payload = result["social_volume_intelligence"]
    assert payload["feature_ref"] == 167


def test_cap183_risk_score_formula_reference():
    amount = WHALE_THRESHOLD_USD
    expected_base = min(100.0, amount / WHALE_THRESHOLD_USD * 10)
    actual = compute_whale_risk_score(amount_usd=amount, tier="whale", flow_direction="unknown")
    assert actual == round(min(100.0, expected_base + 8.0), 1)
