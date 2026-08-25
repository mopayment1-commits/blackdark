"""Tests — #203 Incentive Tracker, #205 Community Freemium Layer."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bd_platform import community_freemium_layer as cfl
from bd_platform import incentive_tracker as it


# ── #203 Incentive Tracker ─────────────────────────────────────────────────────


@pytest.fixture
def isolated_incentive_store(tmp_path, monkeypatch):
    store = tmp_path / "incentive_tracker.json"
    seed = tmp_path / "incentive_programs_seed.json"
    seed.write_text(
        '[{"id":"p1","protocol":"Uniswap","program_name":"UNI LP Incentives","chain":"ethereum",'
        '"incentive_type":"liquidity_mining","status":"active","source":"Protocol Docs",'
        '"source_url":"https://docs.uniswap.org","apy_pct":12.5,"risk_score":4,'
        '"timeline":{"start":"2026-01-01","end":"2026-12-31","cliff_days":30},"assets":["ETH"]}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(it, "_STORE_PATH", store)
    monkeypatch.setattr(it, "_SEED_PATH", seed)
    return store


def test_incentive_tracker_50_protocol_seed():
    """Full seed file must cover ≥50 protocols."""
    import json
    from pathlib import Path

    rows = json.loads(Path("data/incentive_programs_seed.json").read_text(encoding="utf-8"))
    protocols = {r["protocol"] for r in rows}
    assert len(rows) >= 50
    assert len(protocols) >= 50


def test_source_status_visible(isolated_incentive_store):
    result = it.list_incentive_programs()
    prog = result["programs"][0]
    assert "Source:" in prog["source_line"]
    assert "Status:" in prog["source_line"]
    assert prog["disclaimer_hideable"] is False


def test_not_opportunity_format(isolated_incentive_store):
    prog = it.get_incentive_program("p1")["program"]
    assert prog["not_an_opportunity"] is True
    assert "Incentive Program:" in prog["display"]
    assert "APY:" in prog["display"]
    assert "Risk:" in prog["display"]


def test_timeline_visible(isolated_incentive_store):
    prog = it.get_incentive_program("p1")["program"]
    assert "Start:" in prog["timeline_display"]
    assert "Cliff:" in prog["timeline_display"]


def test_fee_db_context(isolated_incentive_store):
    prog = it.get_incentive_program("p1")["program"]
    assert prog["fee_context"]["fee_db_feature_id"] == 130


def test_disclaimer_always_present(isolated_incentive_store):
    listed = it.list_incentive_programs()
    detail = it.get_incentive_program("p1")
    assert "Impermanent loss" in listed["disclaimer"]
    assert detail["disclaimer_hideable"] is False


def test_filter_by_status(isolated_incentive_store):
    active = it.list_incentive_programs(status="active")
    assert active["count"] >= 1


# ── #205 Community Freemium ──────────────────────────────────────────────────


def test_community_limits_display():
    limits = cfl.community_tier_limits()
    assert limits["daily_calls"] == 100
    assert limits["max_assets"] == 5
    assert limits["resolution"] == "1D"
    assert "Powered by BLACKDARK" in limits["watermark"]


def test_community_asset_restriction():
    err = cfl.validate_community_request("DOGE")
    assert err is not None
    assert err["error"] == "asset_not_in_community_tier"
    assert "Upgrade" in err["upsell"]


def test_community_resolution_restriction():
    err = cfl.validate_community_request("BTC", resolution="1H")
    assert err is not None
    assert err["error"] == "resolution_not_allowed"


@pytest.mark.asyncio
async def test_community_chart_watermark(monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value={"ok": True, "data": {"price_usd": 100000, "change_24h_pct": 1.0}}),
    )
    result = await cfl.fetch_community_chart("BTC")
    assert result["ok"] is True
    assert result["watermark"] == "Powered by BLACKDARK"
    assert result["watermark_required"] is True
    assert result["limits"]["separate_charts_engine"] is False


@pytest.mark.asyncio
async def test_community_oracle_uses_same_engine(monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_oracle",
        AsyncMock(return_value={"ok": True, "data": {"verdict": "WAIT", "confidence_score": 60}}),
    )
    result = await cfl.fetch_community_oracle("ETH")
    assert result["ok"] is True
    assert result["merged_into"] == 162
    assert "Upgrade" in result["upsell"]


def test_community_status():
    status = cfl.community_freemium_status()
    assert status["parity_with_unified_api"] is True
    assert status["merged_into"] == 162
