"""Tests — Execution Rejected features registry and E2E."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import execution_rejected_layer as er


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def test_execution_rejected_registry(seed):
    registry = er.execution_rejected_registry(seed=seed)
    assert registry["insight_only_platform"] is True
    assert registry["feature_count"] >= 20
    refs = {f["feature_ref"] for f in registry["features"]}
    assert {78, 119, 216}.issubset(refs)


def test_whale_behavior_analysis_route(seed):
    whale = er.whale_behavior_analysis_216(seed=seed)
    assert whale["route"] == "/oracle/on-chain/whale/behavior-analysis"
    assert whale["counter_trading_rejected"] is True


def test_78_impact_enhanced(seed):
    from bd_platform.whales_institutional_layer import build_impact_analysis_78

    impact = build_impact_analysis_78(order_usd=100_000, venue="binance", seed=seed)
    assert impact["available_liquidity_usd"] > 0
    assert "depth_participation_pct" in impact


def test_execution_rejected_e2e(seed):
    assert er.run_execution_rejected_e2e(seed=seed)["all_passed"] is True
