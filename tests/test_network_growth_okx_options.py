"""Tests — #78 Network Growth, #80 OKX, #82+#83 Options Intelligence."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.network_growth_intelligence import (
    _spam_dust_policy,
    compute_growth_and_acceleration,
    analyze_network_growth,
    network_growth_for_decision_engine,
)
from bd_platform.options_intelligence import (
    _parse_instrument,
    build_iv_surface,
    build_term_structure,
    analyze_options_intelligence,
    options_intelligence_for_decision_engine,
)
from blackdark.ingestion.okx_connector import (
    fetch_okx_spot_ticker,
    fetch_okx_market_context,
    okx_connector_status,
)


def test_spam_dust_policy_documented():
    policy = _spam_dust_policy()
    assert policy["min_transfer_usd"] == 10.0
    assert policy["stable_first_seen"] is True


def test_growth_acceleration_derivative():
    now = int(time.time())
    registry = {
        "addresses": {
            f"ethereum:0x{i}": {
                "chain": "ethereum",
                "first_seen_ts": now - 3600 * 24 * (i % 5),
                "interaction_count": 5,
                "total_usd": 100.0,
            }
            for i in range(20)
        }
    }
    metrics = compute_growth_and_acceleration(registry, chains=("ethereum",))
    assert "acceleration_pct" in metrics
    assert "new_addresses_7d" in metrics
    assert metrics["growth_index"] >= 1.0


def test_parse_deribit_instrument():
    meta = _parse_instrument("BTC-29MAR24-70000-C")
    assert meta is not None
    assert meta["asset"] == "BTC"
    assert meta["strike"] == 70000.0
    assert meta["kind"] == "C"


def test_iv_surface_benchmark_validation():
    summaries = [
        {
            "instrument_name": "BTC-27MAR27-70000-C",
            "mark_iv": 45.0,
            "open_interest": 100,
        },
        {
            "instrument_name": "BTC-27MAR27-70000-P",
            "mark_iv": 55.0,
            "open_interest": 80,
        },
    ]
    surface = build_iv_surface(summaries, spot=70000.0, asset="BTC")
    assert surface["atm_iv_pct"] == 45.0
    assert surface["benchmark_validation_passed"] is True


def test_term_structure_backwardation():
    summaries = [
        {"instrument_name": "BTC-27MAR27-70000-C", "mark_iv": 52.0},
        {"instrument_name": "BTC-25JUN27-70000-C", "mark_iv": 38.0},
    ]
    term = build_term_structure(summaries, spot=70000.0, asset="BTC")
    assert term["structure"] == "backwardation"
    assert term["expiry_exactness_passed"] is True


@pytest.mark.asyncio
async def test_network_growth_analyze():
    with patch(
        "bd_platform.network_growth_intelligence._ingest_from_transaction_index",
        return_value=0,
    ), patch(
        "bd_platform.network_growth_intelligence._ingest_transfers",
        return_value=50,
    ):
        out = await analyze_network_growth("SOL")
    assert out["ok"] is True
    assert out["feature"] == "#78"
    assert out["network_growth"]["acceleration_pct"] is not None
    assert out["spam_dust_policy"]["min_transfer_usd"] == 10.0


@pytest.mark.asyncio
async def test_network_growth_decision_engine():
    with patch(
        "bd_platform.network_growth_intelligence.analyze_network_growth",
        new=AsyncMock(
            return_value={
                "ok": True,
                "asset": "SOL",
                "network_growth": {"acceleration_pct": 45.0},
                "headline": "SOL network growth accelerated 45% this week",
                "latency_ms": 50,
            }
        ),
    ):
        out = await network_growth_for_decision_engine("SOL")
    assert out["ok"] is True
    assert out["risk_score_delta"] > 0


@pytest.mark.asyncio
async def test_okx_spot_mocked():
    fake = {
        "ok": True,
        "data": {"data": [{"last": "50000", "open24h": "49000", "vol24h": "1000", "volCcy24h": "50000000"}]},
        "cache_hit": False,
    }
    with patch("blackdark.ingestion.okx_connector._okx_get", new=AsyncMock(return_value=fake)):
        out = await fetch_okx_spot_ticker("BTC")
    assert out["ok"] is True
    assert out["feature"] == "#80"
    assert out["price_usd"] == 50000.0


@pytest.mark.asyncio
async def test_okx_fallback_to_binance():
    with patch(
        "blackdark.ingestion.okx_connector._okx_get",
        new=AsyncMock(return_value={"ok": False, "error": "http_500"}),
    ), patch(
        "blackdark.ingestion.binance_connector.fetch_binance_spot_ticker",
        new=AsyncMock(return_value={"ok": True, "price_usd": 100.0, "symbol": "BTC"}),
    ):
        out = await fetch_okx_spot_ticker("BTC")
    assert out["ok"] is True
    assert out.get("fallback") is True


def test_okx_connector_status():
    status = okx_connector_status()
    assert status["feature"] == "#80"
    assert "fallback_chain" in status


@pytest.mark.asyncio
async def test_options_intelligence_mocked():
    summaries = [
        {"instrument_name": "BTC-27MAR27-70000-C", "mark_iv": 45.0, "open_interest": 200},
        {"instrument_name": "BTC-27MAR27-65000-P", "mark_iv": 52.0, "open_interest": 150},
        {"instrument_name": "BTC-25JUN27-70000-C", "mark_iv": 38.0, "open_interest": 100},
    ]
    with patch(
        "bd_platform.options_intelligence._fetch_book_summaries",
        new=AsyncMock(return_value=summaries),
    ), patch(
        "bd_platform.options_intelligence._fetch_index_price",
        new=AsyncMock(return_value=70000.0),
    ):
        out = await analyze_options_intelligence("BTC")
    assert out["ok"] is True
    assert out["iv_surface"]["atm_iv_pct"] == 45.0
    assert out["term_structure"]["structure"] in {"backwardation", "contango", "flat"}
    assert out.get("headline")


@pytest.mark.asyncio
async def test_options_decision_engine_payload():
    with patch(
        "bd_platform.options_intelligence.analyze_options_intelligence",
        new=AsyncMock(
            return_value={
                "ok": True,
                "asset": "BTC",
                "iv_surface": {"atm_iv_pct": 45, "put_skew_vs_atm": 10},
                "term_structure": {"structure": "backwardation"},
                "headline": "test",
                "latency_ms": 80,
            }
        ),
    ):
        out = await options_intelligence_for_decision_engine("BTC")
    assert out["ok"] is True
    assert out["risk_score_delta"] > 0
