"""Batch09 reopening — semantic oracle tests for remediated canonical mappings."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def test_437_defi_risk_radar_distinct_from_mindshare_288(seed: dict):
    from bd_platform.defi_yield_intelligence_layer import defi_risk_radar_437
    from bd_platform.correlation_mindshare import compute_mindshare_correlation_288
    import asyncio

    out437 = defi_risk_radar_437(symbol="ETH", seed=seed)
    out288 = asyncio.run(compute_mindshare_correlation_288(symbol="ETH"))

    assert out437["ok"] is True
    assert out437["capability_id"] == 437
    assert "defi_risk_radar" in out437
    assert "risk_signals" in out437
    assert out437.get("canonical_distinct_from") == 288
    assert "mindshare" not in json.dumps(out437).lower()
    assert "correlation" not in out437.get("feature", "").lower()
    assert out288.get("ok") is True
    assert "mindshare" in out288
    assert "defi_risk_radar" in out437
    assert out437["defi_risk_radar"] != out288.get("mindshare", {}).get("galaxy_score", 0)


def test_441_oracle_risk_distinct_from_stat_arb_155(seed: dict):
    from bd_platform.defi_yield_intelligence_layer import oracle_risk_441
    from bd_platform.intelligence_analysis_layer import stat_arb_insight_155

    fresh = oracle_risk_441(symbol="BTC", seed=seed, primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_000_100)
    stale = oracle_risk_441(symbol="BTC", seed=seed, primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_030_000)
    stat = stat_arb_insight_155(pair_a="ETH", pair_b="BTC", seed=seed)

    assert fresh["ok"] is True
    assert fresh["capability_id"] == 441
    assert fresh.get("oracle_freshness_status") == "fresh"
    assert stale.get("oracle_freshness_status") in {"stale", "critical_stale"}
    assert stale["oracle_risk"] > fresh["oracle_risk"]
    assert fresh.get("canonical_distinct_from") == 155
    assert "z_score" not in fresh
    assert "stat_arb" not in json.dumps(fresh).lower()
    assert stat.get("ok") is True
    assert "oracle_risk" not in stat


@pytest.mark.parametrize("capability_id", [437, 441])
def test_remediated_bindings_via_registry(capability_id: int, seed: dict):
    import importlib

    from pdf_capability_registry import discover_bindings, execute_capability
    import asyncio

    mod_path, fn_name = discover_bindings()[capability_id]
    assert mod_path == "bd_platform.defi_yield_intelligence_layer"
    assert fn_name in {"defi_risk_radar_437", "oracle_risk_441"}

    out = asyncio.run(execute_capability(capability_id))
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id
