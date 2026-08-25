"""Tests — #156 Exit Zone, #160 DeFi Safety, #162 Unified API, #174/#176 Sheets."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bd_platform import defi_safety_layer as dsl
from bd_platform import exit_strategy_assistant as esa
from bd_platform import spreadsheet_integration as si
from bd_platform import unified_api_platform as uap


# ── #156 Exit Strategy ───────────────────────────────────────────────────────


def test_exit_strategy_status():
    status = esa.exit_strategy_status()
    assert status["feature_id"] == 156
    assert status["not_mandatory_sell"] is True
    assert status["editable_zones"] is True


def test_save_user_exit_zone(tmp_path, monkeypatch):
    prefs = tmp_path / "prefs.json"
    monkeypatch.setattr(esa, "_PREFS_PATH", prefs)
    result = esa.save_user_exit_zone("BTC", zone_low=45000, zone_high=48000, user_id="test")
    assert result["ok"] is True
    assert result["zone"]["zone_low"] == 45000


@pytest.mark.asyncio
async def test_compute_exit_zone_mocked(monkeypatch):
    async def fake_snap(asset):
        return {"mark_price": 50000, "change_24h_pct": 2.0, "timestamp": "2026-01-01T00:00:00+00:00"}

    monkeypatch.setattr("bd_platform.free_market_data.binance_futures_snapshot", fake_snap)
    monkeypatch.setattr(
        "technical_analysis.build_ta_bundle",
        AsyncMock(return_value={"rsi": 72}),
    )
    monkeypatch.setattr(
        "bd_platform.liquidity_health_check.analyze_liquidity_health",
        AsyncMock(return_value={"ok": True, "concentration": {"concentration_risk": "high"}}),
    )
    monkeypatch.setattr(
        "ai_oracle.get_single_sentence_oracle",
        AsyncMock(return_value=type("O", (), {"verdict": "WAIT", "sentence": "test"})()),
    )

    result = await esa.compute_recommended_exit_zone("BTC")
    assert result["ok"] is True
    assert result["not_mandatory_sell"] is True
    assert result["exit_zone"]["editable"] is True
    assert result["sla_met"] is True
    assert "اقتراح" in result["display_ar"]


# ── #160 DeFi Safety ─────────────────────────────────────────────────────────


def test_scan_text_for_flags_selfdestruct():
    flags = dsl._scan_text_for_flags("function destroy() external onlyOwner { selfdestruct(msg.sender); }")
    ids = {f["flag_id"] for f in flags}
    assert "owner_selfdestruct" in ids


def test_defi_safety_status():
    status = dsl.defi_safety_status()
    assert status["feature_id"] == 160
    assert status["protection_guarantee"] is False


@pytest.mark.asyncio
async def test_scan_contract_invalid_address():
    result = await dsl.scan_contract_risk("not-an-address")
    assert result["ok"] is False


@pytest.mark.asyncio
async def test_scan_contract_with_abi_mocked(monkeypatch):
    async def fake_context(addr, chain):
        return {
            "sources": ["etherscan_abi_public"],
            "text_blob": "function pause() external onlyowner mint unlimited",
        }

    monkeypatch.setattr(dsl, "_fetch_contract_context", fake_context)
    result = await dsl.scan_contract_risk("0x" + "a" * 40)
    assert result["ok"] is True
    assert result["flag_count"] >= 1
    assert result["protection_guarantee"] is False


# ── #162 Unified API ───────────────────────────────────────────────────────────


def test_unified_api_status():
    status = uap.unified_api_status()
    assert status["feature_id"] == 162
    assert status["api_version"] == "v1"
    assert status["endpoint_count"] >= 8
    assert status["freshness_metadata"] is True


def test_envelope_schema():
    env = uap._envelope({"ok": True, "metric": "price", "price_usd": 100}, asset="BTC")
    assert env["api_version"] == "v1"
    assert env["metadata"]["idempotent_read"] is True
    assert env["metadata"]["freshness_tz"] == "UTC"


@pytest.mark.asyncio
async def test_fetch_price_mocked(monkeypatch):
    async def fake_snap(asset):
        return {"mark_price": 100000, "change_24h_pct": 1.5, "timestamp": "2026-01-01", "source": "test"}

    monkeypatch.setattr("bd_platform.free_market_data.binance_futures_snapshot", fake_snap)
    resp = await uap.fetch_price("BTC")
    assert resp["ok"] is True
    assert resp["data"]["price_usd"] == 100000
    assert resp["metadata"]["source"] == "test"


# ── #174/#176 Spreadsheet ────────────────────────────────────────────────────


def test_spreadsheet_status():
    status = si.spreadsheet_integration_status()
    assert 174 in status["feature_ids"]
    assert 176 in status["feature_ids"]
    assert "BLACKDARK" in status["function_syntax"]


@pytest.mark.asyncio
async def test_sheet_invalid_symbol():
    result = await si.evaluate_blackdark_function("", "price")
    assert "#N/A" in result["cell_value"]


@pytest.mark.asyncio
async def test_sheet_invalid_metric():
    result = await si.evaluate_blackdark_function("BTC", "invalid_metric")
    assert "#N/A" in result["cell_value"]


@pytest.mark.asyncio
async def test_sheet_price_mocked(monkeypatch):
    async def fake_fetch(asset, exchange=None):
        return {"data": {"price_usd": 99999}}

    monkeypatch.setattr("bd_platform.unified_api_platform.fetch_price", fake_fetch)
    monkeypatch.setattr("bd_platform.unified_api_platform.check_api_rate_limit", lambda k: None)
    result = await si.evaluate_blackdark_function("BTC", "price")
    assert result["ok"] is True
    assert result["cell_value"] == 99999
