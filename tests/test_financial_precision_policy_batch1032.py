"""Tests — Financial Precision Policy (#1032)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

import money_decimal as md
from bd_platform.financial_precision_policy_engine import (
    attach_financial_audit,
    check_production_gate_1032,
    financial_precision_status_1032,
    reset_financial_precision_state,
    run_financial_precision_e2e_1032,
    scan_financial_paths,
)


@pytest.fixture
def fp_seed() -> dict:
    return json.loads(Path("data/financial_precision_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset():
    reset_financial_precision_state()
    yield
    reset_financial_precision_state()


def test_1032_status_no_standalone(fp_seed):
    status = financial_precision_status_1032(seed=fp_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["float_forbidden_in_financial_paths"] is True
    assert status["policy"]["crypto_decimal_places"] == 8
    assert status["policy"]["fiat_decimal_places"] == 2


def test_crypto_money_8dp_round_half_up():
    assert md.crypto_money("1.123456789") == Decimal("1.12345679")
    assert md.crypto_money("1.123456784") == Decimal("1.12345678")


def test_fiat_money_2dp_round_half_up():
    assert md.fiat_money("10.125") == Decimal("10.13")
    assert md.fiat_money("10.124") == Decimal("10.12")


def test_financial_audit_metadata():
    meta = md.financial_audit_metadata(asset_type="crypto")
    assert meta["type_used"] == "Decimal"
    assert meta["precision"] == 8
    assert meta["rounding_method"] == "round_half_up"
    assert meta["financial_precision_ref"] == 1032


def test_attach_financial_audit(fp_seed):
    out = attach_financial_audit({"net_profit_usdt": 1.5}, context="test_pnl", seed=fp_seed)
    assert "financial_precision" in out
    assert out["provenance_financial_type"] == "Decimal"
    assert out["financial_precision"]["fee_db"]["fee_db_logged"] is True


def test_settlement_lint_clean(fp_seed):
    result = scan_financial_paths(seed=fp_seed)
    assert result["ok"] is True
    assert result["violation_count"] == 0


def test_production_gate(fp_seed):
    gate = check_production_gate_1032(seed=fp_seed)
    assert gate["lint_passed"] is True
    assert gate["checks"]["crypto_precision_8dp"] is True


def test_pnl_still_decimal_model():
    import profit_fee_algorithms as pfa

    buy = {"bids": [[99.0, 100.0]], "asks": [[100.0, 100.0]]}
    sell = {"bids": [[102.0, 100.0]], "asks": [[103.0, 100.0]]}
    row = pfa.net_cross_exchange_profit(
        buy, sell, buy_exchange="binance", sell_exchange="okx", symbol="BTC/USDT", notional=100.0
    )
    assert row is not None
    assert row["money_model"] == "decimal_half_even"


def test_institutional_activation_uses_decimal():
    from billing.institutional_activation import _contract_months

    assert _contract_months(15000) == 12
    assert _contract_months(8000) == 6
    assert _contract_months(1500) == 12


def test_e2e_1032(fp_seed):
    result = run_financial_precision_e2e_1032(seed=fp_seed)
    assert result["all_passed"] is True
    assert result["ok"] is True


def test_lint_script_exit_zero():
    import subprocess
    import sys

    proc = subprocess.run([sys.executable, "scripts/financial_precision_lint.py"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
