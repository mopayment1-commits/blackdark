"""Tests — #876 API Gateway + #663 Exchange Stablecoin Buying Power Index."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bd_platform import api_gateway as ag
from bd_platform import onchain_metrics_library as oml
from bd_platform import stablecoin_health_monitor as shm


@pytest.fixture
def gateway_seed(tmp_path, monkeypatch):
    p = tmp_path / "api_gateway_seed.json"
    p.write_text(Path("data/api_gateway_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ag, "_SEED_PATH", p)
    ag.reset_quota_for_tests()
    return p


@pytest.fixture
def stablecoin_seed(tmp_path, monkeypatch):
    p = tmp_path / "stablecoin_health_monitor_seed.json"
    p.write_text(Path("data/stablecoin_health_monitor_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(shm, "_SEED_PATH", p)
    return p


@pytest.fixture
def onchain_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


# --- #876 API Gateway ---


def test_876_gateway_status(gateway_seed):
    status = ag.api_gateway_status()
    assert status["ok"] is True
    assert status["legal_name"] == "API Gateway"
    assert status["rest_first"] is True


def test_876_rbac_free_denied_risk(gateway_seed):
    result = ag.gateway_handle_request(endpoint_id="risk_protocol", api_key="bd_free_demo_key_0001")
    assert result["status_code"] == 403


def test_876_rbac_pro_risk_access(gateway_seed):
    result = ag.gateway_handle_request(
        endpoint_id="risk_protocol", api_key="bd_pro_demo_key_0002",
        path_params={"protocol_id": "aave_v3"},
    )
    assert result["status_code"] == 200


def test_876_quota_enforcement(gateway_seed):
    ag.reset_quota_for_tests()
    for _ in range(100):
        r = ag.gateway_handle_request(endpoint_id="usage", api_key="bd_free_demo_key_0001")
        assert r["status_code"] == 200
    denied = ag.gateway_handle_request(endpoint_id="usage", api_key="bd_free_demo_key_0001")
    assert denied["status_code"] == 429


def test_876_cursor_pagination(gateway_seed):
    items = [{"id": i} for i in range(25)]
    page1 = ag.paginate_cursor(items, limit=10)
    assert len(page1["items"]) == 10
    assert page1["pagination"]["has_next"] is True
    page2 = ag.paginate_cursor(items, cursor=page1["pagination"]["next_cursor"], limit=10)
    assert page2["items"][0]["id"] == 10


def test_876_idempotency_post(gateway_seed):
    from api import idempotency as idem

    idem._STORE.clear()
    r1 = ag.gateway_handle_request(
        endpoint_id="alerts_subscribe",
        api_key="bd_pro_demo_key_0002",
        method="POST",
        body={"channel": "defi_risk_spike"},
        idempotency_key="idem-test-001",
    )
    assert r1["status_code"] == 201 or r1["status_code"] == 200
    r2 = ag.gateway_handle_request(
        endpoint_id="alerts_subscribe",
        api_key="bd_pro_demo_key_0002",
        method="POST",
        body={"channel": "other"},
        idempotency_key="idem-test-001",
    )
    assert r2.get("idempotent_replay") is True


def test_876_audit_log(gateway_seed):
    ag.gateway_handle_request(endpoint_id="market_overview", api_key="bd_free_demo_key_0001")
    logs = ag.export_audit_logs(user_id="user_free_001")
    assert len(logs.get("items", [])) >= 1
    entry = logs["items"][-1]
    assert entry["user_id"] == "user_free_001"
    assert "endpoint" in entry
    assert "response_size_bytes" in entry


def test_876_openapi_auto_generated(gateway_seed):
    spec = ag.build_openapi_spec()
    assert spec["x_auto_generated"] is True
    assert "/api/v1/market/overview" in spec["paths"]


def test_876_authz_matrix(gateway_seed):
    ag.reset_quota_for_tests()
    result = ag.run_authz_matrix_tests()
    assert result["ok"] is True


def test_876_prometheus_metrics(gateway_seed):
    ag.gateway_handle_request(endpoint_id="market_overview", api_key="bd_free_demo_key_0001")
    text = ag.prometheus_metrics_text()
    assert "api_gateway_requests_total" in text


def test_876_reconciliation(gateway_seed):
    ag.reset_quota_for_tests()
    result = ag.run_reconciliation_tests()
    assert result["ok"] is True


def test_876_http_routes():
    from dashboard import app

    client = TestClient(app)
    resp = client.get("/api/v1/gateway/status")
    assert resp.status_code == 200
    assert resp.json()["legal_name"] == "API Gateway"


def test_876_http_market_with_key():
    from dashboard import app

    client = TestClient(app)
    resp = client.get(
        "/api/v1/market/overview",
        headers={"X-API-Key": "bd_free_demo_key_0001"},
    )
    assert resp.status_code == 200


# --- #663 Buying Power Index ---


def test_663_buying_power_formula(stablecoin_seed):
    index = shm.build_exchange_stablecoin_buying_power_index()
    assert index["ok"] is True
    assert index["metric_id"] == "exchange_stablecoin_buying_power"
    assert index["merged_into"] == 577
    assert isinstance(index["index_pct"], (int, float))
    assert index["stablecoin_usd"] > 0
    assert index["crypto_usd"] > 0


def test_663_triple_source(stablecoin_seed):
    index = shm.build_exchange_stablecoin_buying_power_index()
    sources = index["triple_source"]
    assert "defillama" in sources
    assert "glassnode" in sources
    assert "onchain_direct" in sources
    assert len(sources["values"]) == 3


def test_663_market_radar_widget(stablecoin_seed):
    widget = shm.build_market_radar_buying_power_widget_663()
    assert widget["surface"] == "market_radar"
    assert widget["widget"] == "exchange_stablecoin_buying_power"
    assert widget["widget_label_ar"] == "قوة الشراء"


def test_663_daily_brief_hook(stablecoin_seed):
    hook = shm.build_buying_power_daily_brief_hook_474()
    assert hook is not None
    assert hook["integration_474"] is True
    assert "12" in hook.get("mention", "")


def test_663_arbitrage_adjustment(stablecoin_seed):
    adj = shm.apply_buying_power_arbitrage_adjustment_429({"net_edge_bps": 50})
    assert adj["buying_power_context_663"]["integration_429"] is True
    assert adj["risk_adjusted_edge_bps"] > 50


def test_663_metric_577(onchain_seed, stablecoin_seed):
    metric = oml.build_exchange_stablecoin_buying_power_metric_577()
    assert metric["metric_id"] == "exchange_stablecoin_buying_power"
    assert metric["task_ref"] == 663
    assert metric["value"] is not None


def test_663_reconciliation(stablecoin_seed):
    result = shm.run_reconciliation_tests()
    bp_checks = [c for c in result["checks"] if c["id"].startswith("663_")]
    assert all(c["passed"] for c in bp_checks)
