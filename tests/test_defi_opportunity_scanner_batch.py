"""Tests — #438 DeFi Scanner with #465 DEX Screener, #470 LP Risk, #473 Liquidity Risk."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import defi_opportunity_scanner as dos
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def dos_seed(tmp_path, monkeypatch):
    main = Path("data/defi_opportunity_scanner_seed.json")
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


def test_438_status(dos_seed):
    status = dos.defi_opportunity_scanner_status()
    assert status["feature_id"] == 438
    assert status["standalone"] is False
    assert status["components"]["dex_screener_465"] is True


def test_465_dex_screener_filters(dos_seed):
    screener = dos.screen_dex_pools()
    assert screener["filters_applied"]["min_liquidity_usd"] >= 100_000
    assert screener["filters_applied"]["min_volume_24h_usd"] >= 10_000
    assert screener["filters_applied"]["min_pool_age_days"] >= 7
    assert len(screener["dexs_v1"]) == 4


def test_465_pool_mapping(dos_seed):
    mapping = dos.map_pools_across_dexs()
    assert mapping["mapping_count"] >= 1
    assert "uniswap" in mapping["dexs_v1"]


def test_465_honeypot_flags(dos_seed):
    screener = dos.screen_dex_pools()
    honeypot_pools = [p for p in screener["pools"] if p["risk_flags"]["honeypot"]["is_honeypot"]]
    assert len(honeypot_pools) >= 1
    assert honeypot_pools[0]["risk_flags"]["honeypot"]["provider"] == "honeypot.is"


def test_465_risk_flags(dos_seed):
    screener = dos.screen_dex_pools()
    pool = screener["pools"][0]
    assert "contract_verified" in pool["risk_flags"]
    assert "liquidity_locked" in pool["risk_flags"]
    assert "tax_token" in pool["risk_flags"]


def test_470_lp_position_risk(dos_seed):
    panel = dos.build_lp_position_risk_panel()
    assert panel["count"] >= 1
    pos = panel["positions"][0]
    assert "Simulator" not in pos["legal_name"]
    assert pos["impermanent_loss_pct"] is not None
    assert pos["fee_offset_usd"] is not None
    assert pos["net_pnl_usd"] is not None


def test_470_collateral_integration(dos_seed):
    panel = dos.build_lp_position_risk_panel("lp_eth_usdc_demo")
    pos = panel["positions"][0]
    assert pos.get("collateral_grade_462") is not None


def test_473_liquidity_risk_protocols(dos_seed):
    liq = dos.analyze_all_liquidity_risks()
    assert liq["protocol_count_met"] is True
    assert liq["count"] >= 6
    assert liq["update_interval_minutes"] == 15


def test_473_mandatory_indicators(dos_seed):
    aave = dos.analyze_protocol_liquidity_risk("aave")
    ind = aave["indicators"]
    assert "tvl_trend_7d_pct" in ind
    assert "utilization_rate" in ind
    assert "borrow_supply_ratio" in ind
    assert "liquidation_threshold" in ind


def test_438_defi_panel(dos_seed):
    panel = dos.build_defi_panel()
    assert panel["dex_screener_465"]["count"] >= 1
    assert panel["liquidity_risk_473"]["count"] >= 6
    assert panel["lp_position_risk_470"]["count"] >= 1
    assert panel["count"] >= 1


def test_438_uae_delegation(dos_seed):
    opps = uae.scan_defi_opportunities()
    assert len(opps) >= 1
    assert any("collateral_grade_462" in o for o in opps)


def test_438_reconciliation(dos_seed):
    result = dos.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
