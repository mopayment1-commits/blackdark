"""Flash-crash protection status (capability #49)."""

from __future__ import annotations


def test_flash_crash_protection_status_returns_shape(monkeypatch):
    monkeypatch.setattr("risk_manager.is_trading_frozen", lambda: False)

    from bd_platform.flash_crash_protection import flash_crash_protection_status_49

    out = flash_crash_protection_status_49(symbol="btc")
    assert out["ok"] is True
    assert out["capability_id"] == 49
    assert out["symbol"] == "BTC"
    assert "drawdown" in out
    assert "flash_crash_forecast" in out
