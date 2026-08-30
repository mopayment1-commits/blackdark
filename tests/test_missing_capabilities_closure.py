"""Tests for the four previously-missing PDF checklist capabilities."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_ma_intelligence_report_structure():
    from ma_intelligence_service import build_ma_intelligence_report

    report = await build_ma_intelligence_report(symbol="BTC")
    assert report["feature_ref"] == "ma_intelligence#113"
    assert report["capability_id"] == 113
    assert report["ok"] is True
    assert "merger_spread" in report
    assert "acquisition_comps" in report
    assert report["no_execution"] is True


@pytest.mark.asyncio
async def test_deposit_currencies_open():
    from exchange_currency_status import deposit_currencies_open, reset_currency_status_cache

    reset_currency_status_cache()
    row = await deposit_currencies_open(exchange="binance")
    assert row["feature_ref"] == "exchange_currency_status#380"
    assert row["capability_id"] == 380
    assert isinstance(row["deposit_open"], list)
    assert row["ok"] is True


@pytest.mark.asyncio
async def test_withdrawal_currencies_closed():
    from exchange_currency_status import reset_currency_status_cache, withdrawal_currencies_closed

    reset_currency_status_cache()
    row = await withdrawal_currencies_closed(exchange="binance")
    assert row["feature_ref"] == "exchange_currency_status#381"
    assert row["capability_id"] == 381
    assert isinstance(row["withdrawal_closed"], list)
    assert row["ok"] is True


@pytest.mark.asyncio
async def test_comparison_engine_live():
    from comparison_engine import run_comparison_engine

    report = await run_comparison_engine(symbol="BTC")
    assert report["feature_ref"] == "comparison_engine#627"
    assert report["capability_id"] == 627
    assert "venues" in report
    assert report["no_execution"] is True


def test_accessibility_static_audit():
    from accessibility_audit_service import run_static_wcag_audit

    audit = run_static_wcag_audit()
    assert audit["templates_scanned"] >= 10
    assert audit["standard"].startswith("WCAG")
    assert audit["ok"] is True


@pytest.mark.asyncio
async def test_accessibility_api_report():
    from accessibility_audit_service import build_accessibility_audit_report

    report = await build_accessibility_audit_report()
    assert report["feature_ref"] == "accessibility_audit#wcag"
    assert report["templates_scanned"] >= 1
