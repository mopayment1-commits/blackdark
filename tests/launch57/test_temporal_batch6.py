"""B6 temporal batch — Launch #5/#43 net-edge / arbitrage timing (SPEC §15)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from datetime import timedelta

from launch57.net_edge_timing_common import build_opportunity_timing_context, enrich_opportunity_rows
from launch57.temporal_common import to_rfc3339, utc_now
from launch57.trust_batch1 import net_edge_truth_score


def _future_times():
    now = utc_now()
    quote = to_rfc3339(now)
    detection = to_rfc3339(now + timedelta(seconds=1))
    book = to_rfc3339(now - timedelta(seconds=1))
    transfer = to_rfc3339(now + timedelta(seconds=2))
    funding = to_rfc3339(now + timedelta(minutes=5))
    return quote, detection, book, transfer, funding


def _valid_opportunity(**extra):
    quote, detection, book, transfer, funding = _future_times()
    base = {
        "net_profit_usdt": 5.0,
        "quote_amount": 1000.0,
        "total_slippage_bps": 2,
        "withdrawal_fee_usdt": 0.1,
        "trading_fees_usdt": 0.2,
        "quote_age_ms": 100,
        "estimated_recipients": 1,
        "quote_time": quote,
        "detection_time": detection,
        "order_book_snapshot_time": book,
        "transfer_estimate_time": transfer,
        "funding_timestamp": funding,
    }
    base.update(extra)
    return base


def test_trust_batch1_net_edge_uses_b6_bridge_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "trust_batch1.py").read_text(encoding="utf-8")
    assert "finalize_b6_net_edge_surface" in source
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            imports.append(node.module)
    assert imports == []


def test_opportunity_timing_preserves_spec_fields():
    opp = _valid_opportunity()
    timing = build_opportunity_timing_context({}, opportunity=opp)
    assert timing is not None
    assert timing.quote_time == opp["quote_time"]
    assert timing.detection_time == opp["detection_time"]
    assert timing.order_book_snapshot_time == opp["order_book_snapshot_time"]
    assert timing.funding_timestamp == opp["funding_timestamp"]
    assert timing.transfer_estimate_time == opp["transfer_estimate_time"]
    assert timing.expected_execution_window["start"] == opp["detection_time"]
    assert timing.stale_threshold_ms == 2500.0
    assert timing.presented_as_current is True


def test_stale_opportunity_not_presented_as_current():
    timing = build_opportunity_timing_context({}, opportunity=_valid_opportunity(quote_age_ms=5000))
    assert timing is not None
    assert timing.presented_as_current is False
    assert timing.expired_reason == "quote_stale"


def test_display_timezone_does_not_mutate_canonical_quote_time():
    opp = _valid_opportunity()
    utc = build_opportunity_timing_context({}, opportunity=opp, display_timezone="UTC")
    cairo = build_opportunity_timing_context({}, opportunity=opp, display_timezone="Africa/Cairo")
    assert utc is not None and cairo is not None
    assert utc.quote_time == cairo.quote_time == opp["quote_time"]
    assert utc.detection_time == cairo.detection_time


def test_enrich_opportunity_rows_filters_expired_from_current():
    rows = [
        _valid_opportunity(kind="spot_futures"),
        _valid_opportunity(kind="funding", quote_age_ms=9000),
    ]
    current, all_rows = enrich_opportunity_rows(rows, payload={})
    assert len(all_rows) == 2
    assert len(current) == 1
    assert current[0]["opportunity_timing"]["presented_as_current"] is True
    assert all_rows[1]["opportunity_timing"]["presented_as_current"] is False


@pytest.mark.asyncio
async def test_net_edge_surface_rejects_stale_opportunity():
    out = await net_edge_truth_score(
        symbol="BTC",
        params={"opportunity": _valid_opportunity(quote_age_ms=9000)},
    )
    assert out["success"] is False
    assert out["error"] == "quote_stale"
    assert out["presented_as_current"] is False
    assert out["opportunity_timing"]["quote_time"]
    assert out["b6_net_edge_timing"]["activated"] is True
    assert out["b6_isolation_leakage"] == 0


@pytest.mark.asyncio
async def test_net_edge_surface_includes_timing_on_success():
    opp = _valid_opportunity()
    out = await net_edge_truth_score(
        symbol="BTC",
        params={"opportunity": opp},
    )
    assert out["success"] is True
    assert out["opportunity_timing"]["quote_time"] == opp["quote_time"]
    assert out["opportunity_timing"]["detection_time"] == opp["detection_time"]
    assert out["presented_as_current"] is True


@pytest.mark.asyncio
async def test_spot_perp_filters_expired_opportunities(monkeypatch):
    from failure.freshness import FreshnessState
    from launch57.edge_ui_batch1 import spot_perp_arbitrage_scanner

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 50000.0,
            "data_spine": {},
        }

    async def fake_scan(**kwargs):
        quote, detection, *_ = _future_times()
        return {
            "opportunities": [
                {
                    "kind": "spot_futures",
                    "net_profit_usdt": 1.0,
                    "quote_time": quote,
                    "detection_time": detection,
                    "quote_age_ms": 100,
                },
                {
                    "kind": "funding",
                    "net_profit_usdt": 2.0,
                    "quote_time": quote,
                    "detection_time": detection,
                    "quote_age_ms": 9000,
                },
            ],
            "counts": {"spot_futures": 1, "funding": 1},
            "data_source": "test",
            "data_age_sec": 1.0,
            "timestamp": detection,
        }

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("arbitrage_service.scan_arbitrage_opportunities", fake_scan)
    out = await spot_perp_arbitrage_scanner(symbol="BTC", params={})
    block = out["spot_perp_arbitrage"]
    assert out["launch_item_id"] == 43
    assert len(block["opportunities"]) == 1
    assert len(block["opportunities_all"]) == 2
    assert block["arbitrage_timing"]["expired_filtered"] == 1
    assert out["b6_net_edge_timing"]["activated"] is True
