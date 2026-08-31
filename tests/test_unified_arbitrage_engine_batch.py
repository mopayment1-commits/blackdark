"""Tests — #429 Unified Arbitrage Engine + #428 Triangular Price Divergence Scanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def uae_seed(tmp_path, monkeypatch):
    main = Path("data/unified_arbitrage_engine_seed.json")
    p = tmp_path / "unified_arbitrage_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(uae, "_SEED_PATH", p)
    return p


def test_429_status_core_module(uae_seed):
    status = uae.unified_arbitrage_engine_status()
    assert status["feature_id"] == 429
    assert status["standalone"] is False
    assert status["no_real_money_auto_execution"] is True
    assert status["triangular_scanner"]["feature_id"] == 428


def test_427_deterministic_economics(uae_seed):
    a = uae.compute_arbitrage_economics(
        gross_spread_bps=25, quote_usd=1000, trading_fee_bps=10, slippage_bps=8
    )
    b = uae.compute_arbitrage_economics(
        gross_spread_bps=25, quote_usd=1000, trading_fee_bps=10, slippage_bps=8
    )
    assert a == b
    assert a["economics_engine_ref"] == 427


def test_428_triangular_rule_based(uae_seed):
    loops = uae.scan_triangular_divergence()
    assert len(loops) >= 1
    assert loops[0]["opportunity_type"] == "triangular_divergence"
    assert loops[0]["feature_ref"] == 428
    assert loops[0]["no_auto_execution"] is True
    assert len(loops[0]["legs"]) == 3


def test_428_stablecoin_depeg(uae_seed):
    stable = uae.scan_stablecoin_depeg()
    assert len(stable) >= 1
    assert stable[0]["opportunity_type"] == "stablecoin_depeg"


def test_429_deduplication(uae_seed):
    raw = uae.collect_all_opportunities()
    deduped = uae.dedupe_opportunities(raw)
    assert len(deduped) < len(raw)


def test_429_canonical_schema(uae_seed):
    feed = uae.build_unified_feed()
    assert feed["ok"] is True
    assert feed["ranked_by"] == "executable_net_edge_usdt"
    opp = feed["opportunities"][0]
    for field in ("net_edge_usdt", "gross_spread_bps", "confidence", "sla"):
        assert field in opp


def test_429_ranked_by_net_edge(uae_seed):
    feed = uae.build_unified_feed()
    opps = feed["opportunities"]
    if len(opps) >= 2:
        assert opps[0]["net_edge_usdt"] >= opps[-1]["net_edge_usdt"]


def test_428_triangular_panel_no_ml(uae_seed):
    panel = uae.build_triangular_panel()
    assert panel["feature_id"] == 428
    assert panel["ml_disabled"] is True
    assert panel["rule_based_v1"] is True
    assert panel["cancelled_scope"]["sharpe_drawdown_winrate_sla"] is True


def test_429_sla_no_auto_execution(uae_seed):
    feed = uae.build_unified_feed()
    assert feed["sla"]["no_real_money_auto_execution"] is True
    assert feed["opportunities"][0]["sla"]["simulation_only"] is True


def test_429_reconciliation(uae_seed):
    result = uae.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
