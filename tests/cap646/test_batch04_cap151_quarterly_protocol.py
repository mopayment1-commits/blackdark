"""Capability #151 — Quarterly Protocol Performance Reports (Batch04 execution gates)."""

from __future__ import annotations

import re

import pytest

from cap646.batch04_quarterly_protocol import build_quarterly_protocol_report, quarter_label


@pytest.mark.parametrize("symbol", ["BTC", "ETH", "SOL"])
@pytest.mark.asyncio
async def test_cap151_runtime_quarterly_report_shape(symbol: str):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        151,
        skip_entitlement=True,
        params={"symbol": symbol, "tier": "pro"},
    )
    assert result["success"] is True
    assert result["surface"] == "quarterly_protocol_performance_reports"
    assert result["production_spine"] == "batch04"
    report = result["quarterly_protocol_performance_reports"]
    assert report["reporting_period"] == "quarterly"
    assert re.match(r"^\d{4}-Q[1-4]$", report["quarter_label"])
    assert report["protocol_symbol"] == symbol
    assert report["protocol_tvl_usd"] > 0
    assert 0 <= report["performance_score"] <= 100
    assert "quarterly_summary" in report["protocol_performance"]
    assert "dimension_breakdown" in report["protocol_performance"]


@pytest.mark.asyncio
async def test_cap151_entitlement_denied_without_skip(monkeypatch):
    from cap646 import entitlements

    async def _deny(*_a, **_k):
        return {"allowed": False, "reason": "test_denied"}

    monkeypatch.setattr(entitlements.entitlement_engine, "check", _deny)
    from cap646.runtime import execute_capability

    result = await execute_capability(151, params={"symbol": "BTC"}, skip_entitlement=False)
    assert result["success"] is False
    assert "entitlement" in result


def test_build_quarterly_protocol_report_missing_defi_defaults():
    report = build_quarterly_protocol_report(
        symbol="BTC",
        explanation={"opportunity_score": 70, "risk_score": 3, "breakdown": {"cvd": {"value": "positive"}}},
        defi_snapshot={},
    )
    assert report["protocol_tvl_usd"] == 0
    assert report["performance_score"] >= 0


def test_quarter_label_format():
    assert re.match(r"^\d{4}-Q[1-4]$", quarter_label())
