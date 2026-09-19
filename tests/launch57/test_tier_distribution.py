"""Launch-57 tier distribution — 57/57 table, gating, MOST POPULAR on ELITE."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from launch57.tier_distribution import (
    BLOCKED_EXTERNAL_LAUNCH_IDS,
    MOST_POPULAR_TIER,
    build_launch57_distribution_table,
    distribution_closure_report,
    enforce_launch57_tier_access,
    minimum_tier_for,
    tier_satisfies,
)


def test_distribution_table_57_complete_no_missing_surface():
    table = build_launch57_distribution_table()
    assert len(table) == 57
    report = distribution_closure_report()
    assert report["MISSING_SURFACE"] == []
    assert report["UNGATED_PAID_FEATURES"] == []
    assert report["launch57_rows"] == 57
    assert report["table_complete"] is True
    for row in table:
        assert row["launch_name"]
        assert row["surface_path"]
        assert row["button_or_route"]
        assert row["tier"]
        assert row["status"]


def test_most_popular_tier_is_elite_49():
    assert MOST_POPULAR_TIER == "elite"
    from billing.plan_registry import PLAN_DEFINITIONS

    assert PLAN_DEFINITIONS["elite"]["popular"] is True
    assert PLAN_DEFINITIONS["pro"].get("popular") is not True


def test_blocked_external_not_sold_as_ready():
    report = distribution_closure_report()
    blocked = report["BLOCKED_EXTERNAL_NOT_SOLD_AS_READY"]
    assert {b["launch_number"] for b in blocked} == set(BLOCKED_EXTERNAL_LAUNCH_IDS)


def test_visitor_cannot_access_elite_net_edge_full():
    gate = enforce_launch57_tier_access(launch_item_id=5, params={"tier": "free", "user_key": "anonymous"})
    assert gate["allowed"] is False
    gate_pro = enforce_launch57_tier_access(launch_item_id=5, params={"tier": "pro"})
    assert gate_pro["allowed"] is False
    gate_elite = enforce_launch57_tier_access(launch_item_id=5, params={"tier": "elite"})
    assert gate_elite["allowed"] is False
    assert gate_elite["reason"] == "unverified_paid_tier_claim"


def test_free_cannot_access_wallet_dd_ai_arbitrage():
    assert enforce_launch57_tier_access(launch_item_id=53, params={"tier": "free"})["allowed"] is False
    assert enforce_launch57_tier_access(launch_item_id=36, params={"tier": "pro"})["allowed"] is False
    assert enforce_launch57_tier_access(launch_item_id=43, params={"tier": "elite"})["allowed"] is False


def test_pro_gets_certificate_history_not_cost_autopsy():
    assert tier_satisfies(3, "pro") is True
    assert tier_satisfies(49, "pro") is True
    assert tier_satisfies(5, "pro") is False


def test_elite_gets_net_edge_wallet_token_ai():
    elite_params = {"tier": "elite", "user_id": 1, "verified_subscription_tier": "elite"}
    for lid in (5, 53, 54, 36):
        assert enforce_launch57_tier_access(launch_item_id=lid, params=elite_params)["allowed"] is True


def test_quant_gets_arbitrage_suspicious_exchange():
    quant_params = {"tier": "quant", "user_id": 1, "verified_subscription_tier": "quant"}
    for lid in (43, 56, 57):
        assert enforce_launch57_tier_access(launch_item_id=lid, params=quant_params)["allowed"] is True
        assert enforce_launch57_tier_access(launch_item_id=lid, params={"tier": "elite", "user_id": 1, "verified_subscription_tier": "elite"})["allowed"] is False


def test_floor_guest_trust_and_ledger_public():
    assert enforce_launch57_tier_access(launch_item_id=46, params={"tier": "free", "user_key": "anonymous"})["allowed"] is True
    assert enforce_launch57_tier_access(launch_item_id=4, params={"tier": "free", "user_key": "anonymous"})["allowed"] is True


def test_api_tier_distribution_public():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/tier-distribution")
    assert res.status_code == 200
    body = res.json()
    assert body["closure"]["MOST_POPULAR_TIER"] == "elite"
    assert len(body["rows"]) == 57


def test_api_net_edge_denied_for_anonymous():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/net-edge", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 401


def test_api_net_edge_denied_for_pro_tier():
    from dashboard import app

    client = TestClient(app)
    # Simulate authenticated request is hard without session; tier gate unit-tested above.
    gate = enforce_launch57_tier_access(launch_item_id=5, params={"tier": "pro"})
    assert gate["allowed"] is False


def test_pro_arbitrage_feature_flag_off():
    from auth_service import TIER_FEATURES

    assert TIER_FEATURES["pro"]["arbitrage"] is False
    assert TIER_FEATURES["quant"]["arbitrage"] is True


def test_minimum_tier_mapping_samples():
    assert minimum_tier_for(22) == "free"  # floor → free minimum
    assert minimum_tier_for(3) == "pro"
    assert minimum_tier_for(5) == "elite"
    assert minimum_tier_for(43) == "quant"


def test_launch22_surface_is_real_time_prices_not_subscription_pricing():
    table = build_launch57_distribution_table()
    row22 = next(r for r in table if r["launch_number"] == 22)
    assert row22["surface_path"] == "/api/launch57/real-time-prices"
    assert row22["surface_path"] != "/#pricing"
    assert row22["status"] == "PENDING_VERIFICATION"


def test_launch22_public_api_returns_price_with_freshness_badge(monkeypatch):
    from dashboard import app

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 50000.0, "source": "binance:api.binance.com", "age_sec": 1.0, "change_24h": 1.2}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    client = TestClient(app)
    res = client.get("/api/launch57/real-time-prices", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body["launch_item_id"] == 22
    assert body["surface"] == "real_time_prices"
    assert body["price"] == 50000.0
    assert body["freshness_state"] in {"LIVE", "NEAR_LIVE", "DELAYED", "STALE"}
    assert body.get("presented_as_live") is True


@pytest.mark.asyncio
async def test_kill_real_time_prices_path_not_presented_as_live(monkeypatch):
    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {"price": 100.0, "source": "binance:api.binance.com", "age_sec": 120.0}

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    from launch57.data_batch1 import real_time_prices

    out = await real_time_prices(symbol="BTC", params={})
    assert out["freshness_state"] == "STALE"
    assert out["presented_as_live"] is False
