"""Tests for risk_manager — slippage, poisoning, stop-loss."""

from risk_manager import (
    check_slippage,
    check_stop_losses,
    detect_data_poisoning,
    evaluate_execution_risk,
    freeze_trading,
    is_trading_frozen,
    register_stop_loss,
    unfreeze_trading,
)


def test_slippage_blocks_high():
    v = check_slippage(150.0)
    assert not v.allowed
    assert "slippage" in v.reason


def test_slippage_allows_low():
    v = check_slippage(10.0)
    assert v.allowed


def test_data_poisoning_detects_deviation():
    unfreeze_trading()
    v = detect_data_poisoning(
        {"BTC": 100000},
        reference_prices={"BTC": 50000},
    )
    assert not v.allowed
    assert v.poison_detected
    assert is_trading_frozen()


def test_data_poisoning_allows_normal():
    unfreeze_trading()
    v = detect_data_poisoning(
        {"BTC": 50100},
        reference_prices={"BTC": 50000},
    )
    assert v.allowed


def test_stop_loss_triggers_on_buy():
    register_stop_loss("BTC", 50000.0, "buy", stop_pct=2.0)
    triggered = check_stop_losses({"BTC": 48000.0})
    assert len(triggered) == 1
    assert triggered[0]["symbol"] == "BTC"


def test_evaluate_execution_respects_freeze():
    freeze_trading("test")
    v = evaluate_execution_risk({"asset": "BTC", "total_slippage_bps": 5})
    assert not v.allowed
    unfreeze_trading()


def test_freeze_unfreeze_cycle():
    unfreeze_trading()
    assert not is_trading_frozen()
    freeze_trading("unit_test", duration_sec=1)
    assert is_trading_frozen()
    unfreeze_trading()
    assert not is_trading_frozen()
