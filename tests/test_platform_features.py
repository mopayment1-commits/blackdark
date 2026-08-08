"""Tests for 40-point platform modules."""

from __future__ import annotations

import pytest


def test_feature_matrix_has_40_points():
    from bd_platform.registry import FEATURE_MATRIX

    assert len(FEATURE_MATRIX) == 40
    ids = [f["id"] for f in FEATURE_MATRIX]
    assert ids == list(range(1, 41))


def test_script_sandbox_blocks_import():
    from bd_platform.script_sandbox import run_script

    assert run_script("price + rsi")["result"] == 50.0
    with pytest.raises(ValueError):
        run_script("__import__('os').system('echo')")


def test_grid_bot_create():
    from bd_platform.grid_bot import create_grid, list_grids

    bot = create_grid(asset="BTC", lower_price=90000, upper_price=100000, grids=5)
    assert bot["asset"] == "BTC"
    assert len(bot["levels"]) == 6
    assert list_grids()["count"] >= 1


def test_ifttt_rules_crud():
    from bd_platform.ifttt_rules import create_rule, list_rules

    create_rule(if_condition="profit > 0.25", then_action="alert")
    assert list_rules()["count"] >= 1


def test_public_proof():
    from bd_platform.public_proof import build_public_proof, commit_record, verify_commitment

    proof = build_public_proof()
    assert "merkle_root" in proof
    assert proof["proof_type"] == "merkle_hash_chain_with_zk_commitments"
    c = commit_record({"asset": "BTC", "direction": "long"})
    v = verify_commitment({"asset": "BTC", "direction": "long"}, c["salt"], c["commitment"])
    assert v["valid"] is True


@pytest.mark.asyncio
async def test_portfolio_rebalance():
    from bd_platform.portfolio_rebalancer import suggest_rebalance

    r = await suggest_rebalance({"BTC": 5000, "ETH": 5000}, target_weights={"BTC": 0.5, "ETH": 0.5})
    assert r["portfolio_total_usd"] == 10000
    assert r["trades"] == []


def test_drawdown_guard():
    from bd_platform.drawdown_guard import drawdown_status, update_equity
    from risk_manager import unfreeze_trading

    unfreeze_trading()
    update_equity(10000)
    update_equity(9000)
    st = drawdown_status()
    assert st["drawdown_pct"] >= 9.0


def test_completion_summary():
    from bd_platform.completion import FREE_REPLACEMENTS, completion_summary

    data = completion_summary()
    assert data["total_features"] == 40
    assert data["complete_100_count"] == 40
    assert data["paid_api_blocked_count"] == 0
    assert data["actionable_complete_percent"] == 100.0
    assert len(FREE_REPLACEMENTS) == 7


@pytest.mark.asyncio
async def test_lunarcrush_free_fallback():
    from bd_platform.free_integrations import lunarcrush_social

    r = await lunarcrush_social("BTC")
    assert r["available"] is True
    assert r["free_tier"] is not None


@pytest.mark.asyncio
async def test_coinmarketcal_free_fallback():
    from bd_platform.free_integrations import coinmarketcal_events

    r = await coinmarketcal_events(limit=5)
    assert r["available"] is True
    assert r.get("events") is not None


@pytest.mark.asyncio
async def test_holder_analytics_replaces_itb():
    from bd_platform.free_integrations import holder_analytics

    r = await holder_analytics("BTC")
    assert r["available"] is True
    assert "replacement_for" in r
    assert r["metrics"].get("long_short_ratio") is not None or r["metrics"].get("price_usd") is not None


@pytest.mark.asyncio
async def test_cross_chain_flows_free():
    from bd_platform.free_integrations import cross_chain_flows

    r = await cross_chain_flows()
    assert r["available"] is True
    assert len(r.get("flows") or []) > 0


@pytest.mark.asyncio
async def test_token_unlocks_free():
    from bd_platform.token_unlocks import unlock_calendar

    r = await unlock_calendar(limit=5)
    assert r["source"] == "free_tier_composite"
    assert "scheduled_unlocks" in r


@pytest.mark.asyncio
async def test_footprint_async():
    from bd_platform.footprint_analytics import footprint_snapshot
    from database import init_db

    await init_db()
    r = await footprint_snapshot("BTC")
    assert r["asset"] == "BTC"
    assert "depth_levels" in r


def test_script_sandbox_functions():
    from bd_platform.script_sandbox import run_script

    r = run_script("max(price, ma_slow) > rsi", variables={"price": 100, "ma_slow": 90, "rsi": 50})
    assert r["result"] is True
    assert r["signal"] == "buy"
