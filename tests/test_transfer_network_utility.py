"""Tests — #108 Transfer Network Utility + #120 Network Used."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.transfer_network_utility import (
    _composite_score,
    _cost_score,
    _security_score,
    _speed_score,
    get_user_network_preference,
    set_user_network_preference,
    rank_transfer_networks,
    transfer_network_widget,
    transfer_network_status,
)


def test_scoring_helpers():
    assert _speed_score(2) > _speed_score(20)
    assert _cost_score(1.0, amount_usd=1000) > _cost_score(10.0, amount_usd=1000)
    assert _security_score("stable") > _security_score("experimental")
    assert _composite_score(speed=80, cost=90, security=95) > 80


@pytest.mark.asyncio
async def test_rank_usdt_networks():
    with patch(
        "bd_platform.transfer_network_utility._live_fee_usd",
        new=AsyncMock(side_effect=lambda chain, base_fee=1: (base_fee, "test")),
    ):
        out = await rank_transfer_networks("USDT", amount_usd=1000)
    assert out["ok"] is True
    assert out["feature"] == "#108"
    assert len(out["recommendations"]) >= 5
    assert out["best_network"]["rank"] == 1
    assert out["sla_met"] is True
    assert "speed_score" in out["best_network"]
    assert "security_tier" in out["best_network"]


@pytest.mark.asyncio
async def test_widget_includes_reports():
    with patch(
        "bd_platform.transfer_network_utility._live_fee_usd",
        new=AsyncMock(side_effect=lambda chain, base_fee=1: (base_fee, "test")),
    ):
        out = await transfer_network_widget("USDC", amount_usd=500)
    assert out["widget"]["integrated_features"] == ["#108", "#120"]
    assert out["reports"]["cheapest"]
    assert out["reports"]["fastest"]


def test_user_network_preference_120(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.transfer_network_utility._PREFS_PATH", tmp_path / "prefs.json")
    saved = set_user_network_preference("user-1", "USDT", "trc20")
    assert saved["ok"] is True
    assert saved["feature"] == "#120"
    pref = get_user_network_preference("user-1", "USDT")
    assert pref["network_id"] == "trc20"


@pytest.mark.asyncio
async def test_user_network_in_widget(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.transfer_network_utility._PREFS_PATH", tmp_path / "prefs.json")
    set_user_network_preference("user-2", "USDT", "erc20")
    with patch(
        "bd_platform.transfer_network_utility._live_fee_usd",
        new=AsyncMock(side_effect=lambda chain, base_fee=1: (base_fee, "test")),
    ):
        out = await transfer_network_widget("USDT", user_id="user-2")
    assert out["user_network"] is not None
    assert out["user_network"]["network_id"] == "erc20"
    assert out["user_network"]["feature"] == "#120"


@pytest.mark.asyncio
async def test_unsupported_asset():
    out = await rank_transfer_networks("DOGE")
    assert out["ok"] is False


def test_status():
    status = transfer_network_status()
    assert status["feature"] == "#108"
    assert status["companion"] == "#120"
    assert "USDT" in status["supported_assets"]
