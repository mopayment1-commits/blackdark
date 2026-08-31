"""Tests — #440 Basis Divergence Scanner + #146 Intermediate Data Store (merged into #429)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import basis_funding_divergence_monitor as bfd
from bd_platform import intermediate_data_store as ids
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def bfd_seed(tmp_path, monkeypatch):
    main = Path("data/basis_funding_divergence_seed.json")
    p = tmp_path / "basis_funding_divergence_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(bfd, "_SEED_PATH", p)
    return p


@pytest.fixture
def uae_seed(tmp_path, monkeypatch):
    main = Path("data/unified_arbitrage_engine_seed.json")
    p = tmp_path / "unified_arbitrage_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(uae, "_SEED_PATH", p)
    return p


@pytest.fixture
def ids_warm(tmp_path, monkeypatch):
    p = tmp_path / "intermediate_store_warm.json"
    monkeypatch.setattr(ids, "_WARM_TIER_PATH", p)
    return p


def test_146_infra_status(ids_warm):
    status = ids.intermediate_data_store_status()
    assert status["feature_id"] == 146
    assert status["ui_visible"] is False
    assert status["engineering_only"] is True
    assert ids.route_for_domain("funding_rates") == "influxdb"


def test_146_pipeline_roundtrip(ids_warm):
    result = ids.run_reconciliation_tests()
    assert result["ok"] is True


def test_440_status(bfd_seed):
    status = bfd.basis_funding_divergence_status()
    assert status["feature_id"] == 440
    assert status["legal_name"] == "Basis Divergence Scanner"
    assert status["standalone"] is False
    assert status["infra_feature_ref"] == 146
    assert status["acceptance"]["near_real_time"] is True


def test_440_net_basis_formula(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    nb = btc["net_basis"]
    assert nb["formula"] == "gross_basis - funding_8h - entry_fees - exit_fees - slippage"
    assert btc["signal_active"] is True
    assert btc["net_basis_pct"] > 0


def test_440_scanner_row_columns(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    row = btc["scanner_row"]
    assert row["spot_price"] == 64800.0
    assert row["perp_price"] == 65050.0
    assert "basis_gross_pct" in row
    assert "funding_rate_8h_pct" in row
    assert "net_basis_pct" in row
    assert row["feasibility"]["max_executable_usd"] > 0


def test_440_feasibility_display(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    feas = btc["feasibility"]
    assert "Executable size" in feas["display_en"] or "حجم قابل" in feas["display"]
    assert feas["no_auto_execution"] is True


def test_440_risk_alert_hook(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert "risk_alert_410" in btc


def test_440_spot_perp_basis(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert btc["spot_perp_basis_pct"] is not None
    assert btc["spot_perp_basis_pct"] > 0


def test_440_funding_8h(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert btc["funding_rate_8h_pct"] is not None


def test_440_calendar_spread(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    cal = btc["calendar_spread"]
    assert cal is not None
    assert cal["no_position_recommendation"] is True


def test_440_no_execution_language(bfd_seed):
    opps = bfd.scan_derivatives_divergence(active_only=True)
    assert len(opps) >= 1
    display = opps[0]["display"].lower()
    for term in ("buy", "sell", "open position", "execute"):
        assert term not in display


def test_440_scan_unified_schema(bfd_seed):
    opps = bfd.scan_derivatives_divergence(active_only=True)
    opp = opps[0]
    assert opp["feature_ref"] == 440
    assert opp["opportunity_type"] == "derivatives_basis_funding"
    assert opp["buy_venue"] and opp["sell_venue"]
    assert opp["net_basis_pct"] > 0


def test_440_basis_monitor_widget(bfd_seed):
    widget = bfd.build_basis_monitor_widget(limit=5)
    assert widget["widget"] == "Basis Monitor"
    assert widget["count"] >= 1
    assert widget["top_opportunities"][0]["net_basis_pct"] is not None


def test_440_panel(bfd_seed):
    panel = bfd.build_divergence_panel()
    assert panel["ok"] is True
    assert panel["count"] >= 3
    assert len(panel["scanner_rows"]) >= 3


def test_440_unified_feed_integration(uae_seed, bfd_seed):
    raw = uae.collect_all_opportunities()
    deriv = [o for o in raw if o.get("opportunity_type") == "derivatives_basis_funding"]
    assert len(deriv) >= 1
    enriched = uae.enrich_opportunity(deriv[0])
    assert enriched.get("buy_venue")
    assert enriched.get("sell_venue")


def test_440_market_radar_integration(uae_seed, bfd_seed):
    radar = uae.build_market_radar_integration()
    assert radar.get("basis_monitor_440") is not None
    assert radar["basis_monitor_440"]["count"] >= 1


def test_440_alert_fillable_derivatives(uae_seed, bfd_seed):
    opps = bfd.scan_derivatives_divergence(active_only=True)
    enriched = uae.enrich_opportunity(opps[0])
    alert = uae.evaluate_opportunity_alert(enriched)
    assert alert["checks"]["fillable"] is True or alert["eligible_for_alert"] is False


def test_440_reconciliation(bfd_seed, ids_warm):
    result = bfd.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["feature_id"] == 440
