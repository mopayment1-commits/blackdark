"""Tests — #72 MVRV Z-Score cycle + #99 Trading Journal Coach."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.mvrv_realignment import (
    cycle_zone_from_z,
    market_regime_label,
    top_bottom_probability,
    mvrv_cycle_context_for_decision_engine,
)
from bd_platform.trading_journal_coach import (
    detect_mistakes,
    import_exchange_trades,
    record_trade,
    weekly_report_card,
    _performance_metrics,
)


def test_cycle_zone_thresholds():
    assert cycle_zone_from_z(-1.0) == "undervalued"
    assert cycle_zone_from_z(0.5) == "fair_value"
    assert cycle_zone_from_z(4.2) == "overvalued"
    assert cycle_zone_from_z(8.0) == "bubble"


def test_late_bull_regime_label():
    assert "Late Bull" in market_regime_label(4.2)


def test_top_probability_late_bull():
    prob = top_bottom_probability(4.2)
    assert prob["event"] == "cycle_top"
    assert prob["probability_pct"] >= 55


@pytest.mark.asyncio
async def test_mvrv_cycle_context_mocked():
    fake = {
        "ok": True,
        "asset": "BTC",
        "z_score": 4.2,
        "latency_ms": 50,
        "sla_met": True,
    }
    with patch(
        "bd_platform.mvrv_realignment.compute_mvrv_realignment",
        new=AsyncMock(return_value=fake),
    ):
        out = await mvrv_cycle_context_for_decision_engine("BTC")
    assert out["ok"] is True
    assert out["feature"] == "#72"
    assert out["cycle_zone"] == "overvalued"
    assert "Late Bull" in out["headline"]
    assert out["risk_score_delta"] > 0


def test_trading_journal_performance_and_mistakes(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.trading_journal_coach._TRADES_PATH", tmp_path / "trades.enc.jsonl")
    monkeypatch.setattr("bd_platform.trading_journal_coach._DATA_BASE", tmp_path)
    uid = "coach-user-1"
    for i in range(6):
        record_trade(
            user_id=uid,
            pair="BTCUSDT",
            side="buy",
            entry_price=100.0,
            exit_price=98.0 if i < 4 else 110.0,
            size_usd=1000,
            fees_usd=2,
            mood="stressed" if i < 3 else "calm",
            ai_signal_followed=i % 2 == 0,
        )
    report = weekly_report_card(uid)
    assert report["ok"] is True
    assert report["feature"] == "#99"
    assert report["performance"]["closed_trades"] == 6
    assert report["sla_met"] is True
    mistakes = detect_mistakes(report.get("performance") and [])  # empty ok
    # load trades via report path
    from bd_platform.trading_journal_coach import _load_trades, _user_hash

    trades = _load_trades(_user_hash(uid))
    mistakes = detect_mistakes(trades)
    assert isinstance(mistakes, list)


def test_exchange_import_supported():
    out = import_exchange_trades(
        user_id="u1",
        exchange="binance",
        trades=[
            {
                "pair": "ETHUSDT",
                "side": "buy",
                "entry_price": 3000,
                "exit_price": 3100,
                "size_usd": 500,
                "fees_usd": 1,
            }
        ],
    )
    assert out["ok"] is True
    assert out["imported"] == 1


def test_performance_metrics_win_rate():
    trades = [
        {"status": "closed", "pnl_usd": 100},
        {"status": "closed", "pnl_usd": -50},
        {"status": "closed", "pnl_usd": 80},
    ]
    m = _performance_metrics(trades)
    assert m["win_rate_pct"] == pytest.approx(66.7, abs=0.2)
    assert m["total_pnl_usd"] == 130
