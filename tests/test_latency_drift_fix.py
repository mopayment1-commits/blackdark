"""Tests for latency + drift remediation."""

from __future__ import annotations

import pytest

from ml.drift_monitor import enforce_drift_actions, ood_score
from risk_manager import is_trading_frozen, unfreeze_trading


def test_ood_fail_closed_without_envelope(monkeypatch):
    monkeypatch.setattr("ml.drift_monitor.load_feature_envelope", lambda: None)
    monkeypatch.setattr("ml.drift_monitor.config.ML_OOD_FAIL_CLOSED", True)
    result = ood_score({"price": 50000, "ret_1h": 1.0})
    assert result["is_ood"] is True
    assert result["reason"] == "no_envelope_fail_closed"


def test_enforce_drift_freezes_on_high_severity():
    unfreeze_trading()
    report = {
        "drift_detected": True,
        "alerts": [{"feature": "volatility", "psi": 0.55, "severity": "high"}],
    }
    action = enforce_drift_actions(report)
    assert action["action"] == "freeze_trading"
    assert is_trading_frozen() is True
    unfreeze_trading()


def test_enforce_drift_warns_on_medium_only():
    unfreeze_trading()
    report = {
        "drift_detected": True,
        "alerts": [{"feature": "ret_1h", "psi": 0.3, "severity": "medium"}],
    }
    action = enforce_drift_actions(report)
    assert action["action"] == "warn"
    assert is_trading_frozen() is False


@pytest.mark.asyncio
async def test_get_market_snapshots_ws_first_skips_rest(monkeypatch):
    from arbitrage_service import get_market_snapshots

    ws_books = {"binance": {"BTC/USDT": {"bids": [[1, 1]], "asks": [[2, 1]]}}}
    monkeypatch.setattr(
        "live_book_hub.get_live_books_if_fresh",
        lambda **kw: (ws_books, 50.0),
    )

    async def fake_cached():
        return {}, {}, "database", 999.0

    monkeypatch.setattr("market_cache.get_market_snapshots_cached", fake_cached)

    async def should_not_call(*args, **kwargs):
        raise AssertionError("REST fetch should not run when WS books are fresh")

    monkeypatch.setattr("arbitrage_service.fetch_live_market_snapshots", should_not_call)

    books, funding, source, age = await get_market_snapshots(prefer_live=True, force_rest=False)
    assert source == "websocket_live"
    assert books == ws_books
    assert age == 0.05
