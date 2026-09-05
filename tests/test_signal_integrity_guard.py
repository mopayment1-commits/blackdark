"""Signal Integrity Guard (#1053) tests."""

from __future__ import annotations

from signal_integrity_guard import (
    detect_spoof_patterns,
    run_signal_integrity_e2e,
    signal_integrity_status,
    validate_signal_integrity,
)
from signal_registry import register_signal


def test_signal_integrity_status():
    status = signal_integrity_status()
    assert status["standalone_rejected"] is True
    assert len(status["patterns"]) >= 5


def test_wash_trading_detected():
    flags = detect_spoof_patterns(features={"buyer_address": "0x1", "seller_address": "0x1"})
    assert any(f["pattern"] == "wash_trading" for f in flags)


def test_volume_spike_pattern():
    flags = detect_spoof_patterns(features={"volume_change_pct": 500, "price_change_pct": 0.2})
    assert any(f["pattern"] == "volume_spike_no_price" for f in flags)


def test_validate_rejects_wash():
    result = validate_signal_integrity(
        signal_type="arb",
        asset="BTC",
        features={"buyer": "addr1", "seller": "addr1"},
    )
    assert result["rejected"] is True
    assert result["manipulation_flag"] is True


def test_register_signal_rejects_spoof():
    out = register_signal(
        signal_type="test_spoof",
        asset="BTC",
        features={"buyer_address": "0xdead", "seller_address": "0xdead"},
        persist=False,
    )
    assert out.get("rejected") is True


def test_e2e():
    assert run_signal_integrity_e2e()["all_passed"] is True
