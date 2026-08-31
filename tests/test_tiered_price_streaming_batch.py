"""Tests — Feature #128 Tiered Price Streaming (Enterprise sub-second only)."""

from __future__ import annotations

import json

import pytest

from bd_platform import tiered_price_streaming as tps


@pytest.fixture
def streaming_seed(tmp_path, monkeypatch):
    p = tmp_path / "tiered_price_streaming_seed.json"
    p.write_text(json.dumps({
        "tier_metrics": {
            "free": {"accuracy_pct": 95.5, "uptime_pct": 99.2, "avg_refresh_ms": 2800},
            "pro": {"accuracy_pct": 96.8, "uptime_pct": 99.5, "avg_refresh_ms": 480},
            "enterprise": {"accuracy_pct": 98.5, "uptime_pct": 99.95, "avg_refresh_ms": 68},
        },
        "accuracy": {
            "free": {"accuracy_pct": 95.5, "uptime_pct": 99.2},
            "enterprise": {"accuracy_pct": 98.5, "uptime_pct": 99.95},
        },
    }), encoding="utf-8")
    monkeypatch.setattr(tps, "_SEED_PATH", p)
    return p


def test_status_enterprise_only_decision(streaming_seed):
    status = tps.tiered_price_streaming_status()
    assert status["standalone_rejected"] is True
    assert status["price_feed_feature_id"] == 283
    assert status["institutional_decision"]["not_built_for_everyone"] is True
    assert status["acceptance_criteria"]["no_free_tier_sub_second_resources"] is True


def test_free_tier_sub_second_blocked(streaming_seed):
    access = tps.enforce_tier_access("free", requested_interval_ms=100)
    assert access["allowed"] is False
    assert access["sub_second_blocked"] is True
    assert access["no_free_tier_sub_second"] is True
    assert "enterprise" in access["reason"].lower() or "institution" in access["reason"].lower()


def test_free_tier_sla_1_to_5_seconds(streaming_seed):
    sla = tps.get_tier_sla("free")
    assert sla["sub_second_allowed"] is False
    assert sla["refresh_min_ms"] >= 1000
    assert sla["refresh_max_ms"] <= 5000
    assert sla["mode"] == "rest_poll"


def test_pro_tier_500ms(streaming_seed):
    sla = tps.get_tier_sla("pro")
    assert sla["target_ms"] == 500
    assert sla["sub_second_allowed"] is True
    assert sla["dedicated_websocket"] is False


def test_enterprise_tier_50_100ms_dedicated(streaming_seed):
    sla = tps.get_tier_sla("enterprise")
    assert sla["refresh_min_ms"] == 50
    assert sla["refresh_max_ms"] == 100
    assert sla["dedicated_websocket"] is True
    assert sla["mode"] == "dedicated_websocket"


def test_enterprise_sub_second_allowed(streaming_seed):
    access = tps.enforce_tier_access("enterprise", requested_interval_ms=75)
    assert access["allowed"] is True


def test_free_tier_panel_no_sub_second(streaming_seed):
    panel = tps.build_tiered_streaming_panel(tier="free", asset="BTC")
    assert panel["ok"] is True
    assert panel["streaming"]["sub_second"] is False
    assert panel["sla"]["mode"] == "rest_poll"


def test_free_tier_panel_blocked_on_sub_second_request(streaming_seed):
    panel = tps.build_tiered_streaming_panel(
        tier="free", asset="BTC", requested_interval_ms=50,
    )
    assert panel["ok"] is False
    assert panel["error"] == "tier_access_denied"


def test_enterprise_panel_sub_second(streaming_seed):
    panel = tps.build_tiered_streaming_panel(tier="enterprise", asset="BTC")
    assert panel["ok"] is True
    assert panel["streaming"]["sub_second"] is True
    assert panel["streaming"]["dedicated_websocket"] is True
    assert panel["metrics"]["accuracy_pct"] >= 95.0
    assert panel["metrics"]["uptime_pct"] >= 99.0


def test_tier_sla_tests(streaming_seed):
    tests = tps.run_tier_sla_tests()
    assert tests["all_passed"] is True
    test_names = [t["test"] for t in tests["tier_sla_tests"]]
    assert "free_tier_sub_second_blocked" in test_names
    assert "enterprise_tier_sub_second_allowed" in test_names
    assert "enterprise_only_decision_documented" in test_names


def test_api_routes(streaming_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/price-feed/tiered-streaming/status").status_code == 200
    assert c.get(
        "/api/platform/price-feed/tiered-streaming?tier=enterprise&asset=BTC"
    ).status_code == 200
    assert c.get(
        "/api/platform/price-feed/tiered-streaming?tier=free&requested_interval_ms=50"
    ).status_code == 403
    assert c.get("/api/platform/price-feed/tiered-streaming/sla-tests").status_code == 200
