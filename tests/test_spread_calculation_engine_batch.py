"""Tests — #427 Spread Calculation Engine (Economics Engine for #429)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from bd_platform import spread_calculation_engine as sce
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def sce_seed(tmp_path, monkeypatch):
    main = Path("data/spread_calculation_engine_seed.json")
    p = tmp_path / "spread_calculation_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(sce, "_SEED_PATH", p)
    return p


@pytest.fixture
def uae_seed(tmp_path, monkeypatch):
    main = Path("data/unified_arbitrage_engine_seed.json")
    p = tmp_path / "unified_arbitrage_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(uae, "_SEED_PATH", p)
    return p


def test_427_status(sce_seed):
    status = sce.spread_calculation_engine_status()
    assert status["feature_id"] == 427
    assert status["standalone"] is False
    assert status["decimal_precision"] is True
    assert status["stale_books_rejected"] is True
    assert status["fee_slippage_included"] is True


def test_427_deterministic_economics(sce_seed):
    a = sce.compute_arbitrage_economics(
        gross_spread_bps=25, quote_usd=1000, trading_fee_bps=10, slippage_bps=8, leg_count=3
    )
    b = sce.compute_arbitrage_economics(
        gross_spread_bps=25, quote_usd=1000, trading_fee_bps=10, slippage_bps=8, leg_count=3
    )
    assert a == b
    assert a["economics_engine_ref"] == 427
    assert a["decimal_precision"] is True
    assert a["fee_slippage_included"] is True


def test_427_executable_spread_fresh(sce_seed):
    fixture = sce_seed  # noqa: F841 — ensures monkeypatched seed
    seed = sce._load_seed()
    fx = next(f for f in seed["regression_fixtures"] if f["id"] == "cross_venue_btc_fresh")
    result = sce.compute_executable_spread(**fx["input"], seed=seed)
    assert result["reject"] is False
    assert result["net_spread_usdt"] is not None
    assert result["executable_size"] is not None
    assert result["fee_slippage_included"] is True
    assert result["source_venues"]["buy"] == "okx"


def test_427_stale_book_rejected(sce_seed):
    seed = sce._load_seed()
    fx = next(f for f in seed["regression_fixtures"] if f["id"] == "stale_book_rejected")
    result = sce.compute_executable_spread(**fx["input"], seed=seed)
    assert result["reject"] is True
    assert result["rejection_reason"] == "stale_book"


def test_427_timestamp_drift_rejected(sce_seed):
    seed = sce._load_seed()
    fx = next(f for f in seed["regression_fixtures"] if f["id"] == "timestamp_drift_rejected")
    result = sce.compute_executable_spread(**fx["input"], seed=seed)
    assert result["reject"] is True
    assert result["rejection_reason"] == "timestamp_not_synchronized"


def test_427_insufficient_depth_rejected(sce_seed):
    seed = sce._load_seed()
    fx = next(f for f in seed["regression_fixtures"] if f["id"] == "insufficient_depth_rejected")
    result = sce.compute_executable_spread(**fx["input"], seed=seed)
    assert result["reject"] is True
    assert result["rejection_reason"] == "insufficient_executable_depth"


def test_427_decimal_precision_no_float_drift(sce_seed):
    gross = Decimal("1000") * (Decimal("25") / Decimal("10000"))
    assert str(gross) == "2.5000"
    result = sce.compute_arbitrage_economics(
        gross_spread_bps=25, quote_usd=1000, trading_fee_bps=10, slippage_bps=8, leg_count=2
    )
    assert "decimal_fields" in result
    assert result["decimal_fields"]["gross_spread_usdt"] == "2.500000"


def test_427_regression_fixtures(sce_seed):
    result = sce.run_regression_fixtures()
    assert result["ok"] is True
    assert result["passed"] == result["total"]


def test_427_reconciliation(sce_seed):
    result = sce.run_reconciliation_tests()
    assert result["ok"] is True


def test_427_unified_arbitrage_integration(uae_seed, sce_seed):
    feed = uae.build_unified_feed()
    cross = [o for o in feed["opportunities"] if o.get("opportunity_type") == "cross_venue"]
    raw_cross = [o for o in uae.collect_all_opportunities() if o.get("opportunity_type") == "cross_venue"]
    assert len(raw_cross) >= 1
    opp = raw_cross[0]
    assert "spread_calculation_427" in opp or opp.get("reject") is True
    if not opp.get("reject"):
        assert opp.get("executable_size") is not None
        assert opp.get("source_venues") is not None
    if cross:
        assert cross[0].get("spread_calculation_427") is not None or cross[0].get("net_edge_usdt") is not None


def test_427_unified_delegate(uae_seed):
    a = uae.compute_arbitrage_economics(
        gross_spread_bps=20, quote_usd=1000, trading_fee_bps=10, slippage_bps=8
    )
    assert a["economics_engine_ref"] == 427
    assert a["deterministic"] is True
