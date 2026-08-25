"""Tests — Feature #231 B2B Query Latency SLA merged into #219 Freshness Assurance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import b2b_sla_monitoring as b2b
from bd_platform import freshness_assurance as fa


@pytest.fixture
def isolated_b2b_seed(tmp_path, monkeypatch):
    seed = tmp_path / "b2b_sla_monitoring_seed.json"
    seed.write_text(
        json.dumps({
            "default_percentiles": {"p50": 200, "p95": 1800, "p99": 2500},
            "default_uptime": {"uptime_pct": 99.2, "downtime_hours_month": 5.8},
            "fallback": {
                "primary": "Oracle API v2.1",
                "backup": "Backup Feed v1.9",
                "status": "Active",
            },
            "monitored_endpoints": ["/api/v1/platform/oracle", "/api/v1/platform/price"],
            "endpoints": {
                "/api/v1/platform/oracle": {
                    "uptime_pct": 99.4,
                    "downtime_hours_month": 4.3,
                    "sla_credit_applied": False,
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(b2b, "_SEED_PATH", seed)
    b2b._latency_samples.clear()
    b2b._rate_counters.clear()
    b2b._endpoint_uptime.clear()
    return seed


def test_latency_percentile_slo(isolated_b2b_seed):
    for ms in [150, 180, 200, 220, 250, 300, 500, 800, 1200, 1700]:
        b2b.record_api_latency("/api/v1/platform/oracle", float(ms))
    result = b2b.get_endpoint_latency("/api/v1/platform/oracle")
    assert "p50=" in result["latency_display"]
    assert "p95=" in result["latency_display"]
    assert "SLO: 3s" in result["latency_display"]
    assert result["slo_p95_ms"] == 3000


def test_uptime_display(isolated_b2b_seed):
    uptime = b2b.get_endpoint_uptime("/api/v1/platform/oracle")
    assert "Uptime:" in uptime["uptime_display"]
    assert "Downtime:" in uptime["uptime_display"]
    assert "SLA Credit:" in uptime["uptime_display"]
    assert uptime["sla_target_pct"] == 99.0


def test_rate_limit_graceful_degradation(isolated_b2b_seed):
    for _ in range(8500):
        b2b.increment_rate_counter("client1", "institutional")
    status = b2b.get_rate_limit_status("client1", "institutional")
    assert "Rate Limit:" in status["rate_limit_display"]
    assert status["status"] in ("Normal", "Throttled", "Blocked")
    assert status["rejection_without_explanation"] is False
    if status["status"] == "Blocked":
        assert status["graceful_degradation"] is not None


def test_cache_tier_policy(isolated_b2b_seed):
    free = b2b.get_cache_policy("free")
    pro = b2b.get_cache_policy("pro")
    ent = b2b.get_cache_policy("institutional")
    assert free["max_age_hours"] == 1
    assert pro["max_age_hours"] == 4
    assert ent["max_age_hours"] == 24
    assert ent["bypass_available"] is True
    assert "Max Age" in free["update_frequency_display"] or "Cached" in free["update_frequency_display"]


def test_cache_response_headers(isolated_b2b_seed):
    headers = b2b.build_response_headers("pro", cached=True, cache_age_seconds=3600)
    assert "X-BD-Cache-Policy" in headers
    assert "X-BD-Cache-Hit" in headers
    assert headers["X-BD-Cache-Hit"] == "true"
    assert "X-BD-SLA-Disclaimer" in headers


def test_fallback_status(isolated_b2b_seed):
    fb = b2b.get_fallback_status()
    assert "Primary:" in fb["fallback_display"]
    assert "Fallback:" in fb["fallback_display"]
    assert fb["status"] in ("Active", "Degraded", "Fallback")


def test_enterprise_only_dashboard(isolated_b2b_seed):
    denied = b2b.get_b2b_sla_dashboard(tier="free")
    assert denied["ok"] is False
    assert denied["enterprise_only"] is True

    allowed = b2b.get_b2b_sla_dashboard(tier="institutional")
    assert allowed["ok"] is True
    assert allowed["tab"] == "B2B SLA Monitoring"
    assert allowed["standalone"] is False
    assert allowed["merged_into"] == "Freshness Assurance Layer (#219)"


def test_internal_admin_access(isolated_b2b_seed):
    dash = b2b.get_b2b_sla_dashboard(tier="free", internal=True)
    assert dash["ok"] is True
    assert dash["internal_admin"] is True


def test_sla_disclaimer(isolated_b2b_seed):
    status = b2b.b2b_sla_status()
    assert "operational transparency" in status["sla_disclaimer"]
    assert "Not a guarantee" in status["sla_disclaimer"]


def test_middleware_context_manager(isolated_b2b_seed):
    with b2b.B2BSLAMiddleware("/api/v1/platform/price", tier="pro"):
        pass
    result = b2b.get_endpoint_latency("/api/v1/platform/price")
    assert result["sample_count"] >= 1
    assert result["oracle_api_middleware"] is True


def test_no_instant_claims(isolated_b2b_seed):
    dash = b2b.get_b2b_sla_dashboard(tier="institutional")
    assert dash["no_instant_claims"] is True
    cache = dash["cache_policy"]
    assert "Real-time" in cache["update_frequency_display"] or "Cached" in cache["update_frequency_display"]


def test_freshness_dashboard_includes_b2b_tab(isolated_b2b_seed, tmp_path, monkeypatch):
    seed = tmp_path / "freshness_assurance_seed.json"
    store = tmp_path / "freshness_assurance.json"
    seed.write_text(json.dumps({
        "clock_sync": {"synced": True},
        "stale_thresholds_ms": {"default": 1000},
        "sample_feeds": [],
    }), encoding="utf-8")
    monkeypatch.setattr(fa, "_SEED_PATH", seed)
    monkeypatch.setattr(fa, "_STORE_PATH", store)
    fa._feed_state.clear()
    fa._latency_history.clear()

    dash = fa.get_freshness_dashboard()
    assert "b2b_sla_tab" in dash
    assert dash["merged_features"]["b2b_query_latency"] == 231


def test_freshness_status_includes_b2b(isolated_b2b_seed, tmp_path, monkeypatch):
    seed = tmp_path / "freshness_assurance_seed.json"
    monkeypatch.setattr(fa, "_SEED_PATH", seed)
    seed.write_text(json.dumps({"health_check_interval_minutes": 5}), encoding="utf-8")
    status = fa.freshness_assurance_status()
    assert status["merged_features"]["b2b_query_latency"]["feature_id"] == 231
    assert status["b2b_sla"]["feature_id"] == 231


def test_api_routes(isolated_b2b_seed, tmp_path, monkeypatch):
    seed = tmp_path / "freshness_assurance_seed.json"
    monkeypatch.setattr(fa, "_SEED_PATH", seed)
    monkeypatch.setattr(fa, "_STORE_PATH", tmp_path / "freshness_assurance.json")
    seed.write_text(json.dumps({"sample_feeds": []}), encoding="utf-8")

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/freshness/b2b-sla/status").status_code == 200
    assert c.get("/api/platform/freshness/b2b-sla/fallback").status_code == 200
    assert c.get("/api/platform/freshness/b2b-sla/cache-policy?tier=pro").status_code == 200
    dash = c.get("/api/platform/freshness/b2b-sla/dashboard?tier=institutional")
    assert dash.status_code == 200
    assert dash.json()["tab"] == "B2B SLA Monitoring"


def test_full_seed_exists():
    seed = json.loads(Path("data/b2b_sla_monitoring_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 231
    assert seed["merged_into"] == 219
    assert seed["standalone"] is False
