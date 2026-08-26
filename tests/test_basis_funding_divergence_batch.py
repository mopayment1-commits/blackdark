"""Tests — #440 Basis/Funding Divergence Monitor (merged into #429)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import basis_funding_divergence_monitor as bfd
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


def test_440_status(bfd_seed):
    status = bfd.basis_funding_divergence_status()
    assert status["feature_id"] == 440
    assert status["standalone"] is False
    assert "Arbitrage" not in status["legal_name"]
    assert status["no_position_simulation_v1"] is True
    assert status["cancelled_sla"]["accuracy_95_pct"] is True


def test_440_spot_perp_basis(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert btc["ok"] is True
    assert btc["spot_perp_basis_pct"] is not None
    assert btc["spot_perp_basis_pct"] > 0


def test_440_funding_apy(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert btc["funding_rate_apy"] is not None
    assert abs(btc["funding_rate_apy"]) > 0


def test_440_calendar_spread(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    cal = btc["calendar_spread"]
    assert cal is not None
    assert cal["calendar_spread_pct"] is not None
    assert cal["no_position_recommendation"] is True


def test_440_implied_holding_cost(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert btc["implied_holding_cost_pct"] is not None
    fh = btc["funding_vs_holding_cost"]
    assert fh["no_position_simulation_v1"] is True
    assert "cumulative_funding_7d_pct" in fh


def test_440_index_basis(bfd_seed):
    btc = bfd.analyze_asset_divergence("BTC")
    assert btc["index_derivative_basis_pct"] is not None


def test_440_no_execution_language(bfd_seed):
    opps = bfd.scan_derivatives_divergence()
    assert len(opps) >= 1
    display = opps[0]["display"].lower()
    for term in ("buy", "sell", "open position", "execute"):
        assert term not in display


def test_440_scan_unified_schema(bfd_seed):
    opps = bfd.scan_derivatives_divergence()
    opp = opps[0]
    assert opp["feature_ref"] == 440
    assert opp["opportunity_type"] == "derivatives_basis_funding"
    assert opp["basis_funding_monitor_440"] is not None
    assert opp["monitoring_only"] is True


def test_440_panel(bfd_seed):
    panel = bfd.build_divergence_panel()
    assert panel["ok"] is True
    assert panel["count"] >= 3


def test_440_unified_feed_integration(uae_seed, bfd_seed):
    raw = uae.collect_all_opportunities()
    deriv = [o for o in raw if o.get("opportunity_type") == "derivatives_basis_funding"]
    assert len(deriv) >= 1
    assert deriv[0]["feature_ref"] == 440


def test_440_reconciliation(bfd_seed):
    result = bfd.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["feature_id"] == 440
