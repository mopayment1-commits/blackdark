"""Engineering closure tests for the locked 70-capability scope."""

from __future__ import annotations

import math

import pytest

from capability_spine.closure import build_reconciliation_manifest
from capability_spine.integration import enrich_opportunity_capabilities
from capability_spine.quant import (
    PositionLeg,
    amihud_illiquidity,
    beta_to_benchmark,
    cvar_expected_shortfall,
    delta_neutral_validator,
    kyles_lambda,
    max_drawdown_duration,
    monte_carlo_scenarios,
    nvt_ratio,
    sharpe_ratio,
    sortino_ratio,
    var_99,
    vwap_deviation_index,
    volume_velocity,
)
from capability_spine.registry import NOT_PRESENT_IDS, PARTIAL_IDS, scoped_capability_ids


@pytest.fixture
def sample_opportunity() -> dict:
    prices = [100 + i * 0.5 for i in range(30)]
    volumes = [1_000_000 + i * 10_000 for i in range(30)]
    book = {
        "asks": [[101.0, 500.0], [101.5, 1000.0], [102.0, 2000.0]],
        "bids": [[100.5, 500.0], [100.0, 1000.0], [99.5, 2000.0]],
        "mid": 100.75,
    }
    return {
        "symbol": "BTC",
        "asset": "BTC",
        "price": 100.75,
        "quote_amount": 10_000,
        "book": book,
        "price_history": prices,
        "volume_history": volumes,
        "btc_price_history": prices,
        "eth_price_history": [p * 0.05 for p in prices],
        "call_iv": 0.55,
        "put_iv": 0.62,
        "put_volume": 1000,
        "call_volume": 800,
        "venue_funding": {"binance": 0.0001, "okx": 0.0002},
        "market_cap": 1_000_000_000_000,
        "volume_24h": 20_000_000_000,
        "sentiment": {"fear_greed_index": 55, "fear_greed_label": "Neutral"},
        "evidence_class": "SIMULATED",
        "decision_id": "test-decision-1",
    }


def test_scope_lock_counts():
    assert len(PARTIAL_IDS) == 51
    assert len(NOT_PRESENT_IDS) == 19
    assert len(scoped_capability_ids()) == 70


def test_amihud_golden():
    prices = [100.0, 101.0, 100.5]
    volumes = [0.0, 1_000_000.0, 2_000_000.0]
    out = amihud_illiquidity(prices, volumes)
    assert out["ok"] is True
    assert out["sample_count"] == 2
    assert out["amihud_ratio"] > 0


def test_kyle_lambda_regression():
    flow = [1.0, 2.0, -1.0, 3.0]
    changes = [0.1, 0.2, -0.05, 0.25]
    out = kyles_lambda(changes, flow)
    assert out["ok"] is True
    assert out["lambda"] != 0


def test_vwap_deviation_golden():
    out = vwap_deviation_index([100.0, 102.0], [1000.0, 3000.0], reference_price=103.0)
    assert out["ok"] is True
    vwap = (100 * 1000 + 102 * 3000) / 4000
    assert math.isclose(out["vwap"], vwap, rel_tol=1e-6)


def test_var_99_is_99_not_95():
    prices = [100 + ((-1) ** i) * i for i in range(25)]
    out = var_99(prices, notional=10_000)
    assert out["ok"] is True
    assert out["confidence"] == 0.99


def test_cvar_tail_beyond_var():
    prices = [100 - i * 0.5 for i in range(30)]
    out = cvar_expected_shortfall(prices, confidence=0.95)
    assert out["ok"] is True
    assert out["cvar_return"] <= out["var_return"]


def test_monte_carlo_reproducible_seed():
    prices = [100 + i * 0.1 for i in range(20)]
    a = monte_carlo_scenarios(prices, seed=123)
    b = monte_carlo_scenarios(prices, seed=123)
    assert a["p50_return"] == b["p50_return"]


def test_sharpe_zero_volatility():
    prices = [100.0] * 10
    out = sharpe_ratio(prices)
    assert out["ok"] is True
    assert out["sharpe"] is None


def test_sortino_no_downside():
    prices = [100 + i for i in range(10)]
    out = sortino_ratio(prices)
    assert out["ok"] is True


def test_max_drawdown_duration_known_case():
    prices = [100, 110, 105, 95, 100, 115]
    out = max_drawdown_duration(prices)
    assert out["ok"] is True
    assert out["max_drawdown_duration_periods"] >= 1


def test_beta_not_correlation():
    asset = [100, 102, 104, 106, 108]
    bench = [200, 201, 202, 203, 204]
    out = beta_to_benchmark(asset, bench)
    assert out["ok"] is True
    assert out["beta"] > 1


def test_delta_neutral_validator():
    legs = [PositionLeg("spot", 1.0, 1.0), PositionLeg("perp", -1.0, 1.0)]
    out = delta_neutral_validator(legs, tolerance=0.01)
    assert out["ok"] is True
    assert out["neutral"] is True


def test_nvt_proxy_label():
    out = nvt_ratio(1e12, None, cex_volume_proxy=1e9)
    assert out["ok"] is True
    assert out["proxy"] is True
    assert out["proxy_label"] == "PROXY"


def test_enrich_all_70_capabilities(sample_opportunity):
    enriched = enrich_opportunity_capabilities(sample_opportunity, portfolio={"capital_usd": 50_000, "max_risk": 0.8})
    caps = enriched["capability_spine"]
    assert len(caps) == 70
    for cap_id in scoped_capability_ids():
        assert cap_id in caps, f"missing {cap_id}"


@pytest.mark.parametrize("cap_id", scoped_capability_ids())
def test_capability_present(cap_id, sample_opportunity):
    enriched = enrich_opportunity_capabilities(sample_opportunity)
    assert cap_id in enriched["capability_spine"]


def test_slippage_impact_vector_multilevel(sample_opportunity):
    from capability_spine.execution import slippage_impact_vector

    out = slippage_impact_vector(sample_opportunity["book"], notional_usd=10_000, book_age_ms=100)
    assert out["ok"] is True
    assert out["levels_walked"] >= 1
    assert out["slippage_bps"] >= 0


def test_required_size_liquidity_gate(sample_opportunity):
    from capability_spine.execution import required_size_liquidity_gate

    out = required_size_liquidity_gate(sample_opportunity["book"], notional_usd=10_000, book_age_ms=100)
    assert out["ok"] is True
    assert "gate_state" in out


def test_opportunity_score_invariant(sample_opportunity):
    enriched = enrich_opportunity_capabilities(sample_opportunity)
    score = enriched["capability_spine"]["CAP-34"]["score"]
    assert 0 <= score <= 100


def test_reconciliation_manifest_complete(sample_opportunity):
    manifest = build_reconciliation_manifest(sample_opportunity)
    assert manifest["ACTUAL_RECORD_COUNT"] == 70
    assert manifest["MISSING_IDS"] == []
    assert manifest["DUPLICATE_IDS"] == []
    assert manifest["UNKNOWN_IDS"] == []
    assert manifest["PASS_ENGINEERING_COUNT"] == 70
    assert manifest["NOT_COMPLETE_COUNT"] == 0


def test_decision_truth_pipeline_integration(sample_opportunity):
    from decision_truth.pipeline import evaluate_decision_truth

    out = evaluate_decision_truth(sample_opportunity, portfolio={"capital_usd": 100_000, "max_risk": 1.0})
    assert "capability_spine" in out
    assert len(out["capability_spine"]) == 70
