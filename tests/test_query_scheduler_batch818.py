"""Tests — #818 Data Engine Query Scheduler."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_query_scheduler as qs


@pytest.fixture
def qs_seed() -> dict:
    return json.loads(Path("data/data_engine_query_scheduler_seed.json").read_text(encoding="utf-8"))


def test_818_status(qs_seed):
    status = qs.query_scheduler_status_818()
    assert status["standalone_rejected"] is True
    assert status["component"] == "query_scheduler"
    assert status["schedule_types"] == ["hourly", "daily", "weekly"]
    assert status["no_real_time_continuous"] is True
    assert status["failure_logs_required"] is True


def test_818_list_queries(qs_seed):
    listed = qs.list_scheduled_queries_818(seed=qs_seed)
    assert listed["count"] >= 4
    schedules = {q["schedule"] for q in listed["queries"]}
    assert "hourly" in schedules
    assert "daily" in schedules
    assert "weekly" in schedules


def test_818_execute_success(qs_seed):
    result = qs.run_scheduled_query_with_retries_818("sq-market-radar-btc", seed=qs_seed)
    assert result["ok"] is True
    assert len(result["retry_logs"]) >= 1


def test_818_retry_logs(qs_seed):
    result = qs.run_scheduled_query_with_retries_818(
        "sq-market-radar-btc", simulate_failure=True, seed=qs_seed,
    )
    assert result["ok"] is True
    assert len(result["retry_logs"]) == 3
    assert result["retry_logs"][0]["status"] == "failed"
    assert result["retry_logs"][-1]["status"] == "success"


def test_818_failure_logs_audit(qs_seed):
    retry = qs.list_query_retry_logs_818(seed=qs_seed)
    assert retry["audit_trail"] is True
    assert retry["count"] >= 1
    failures = qs.list_query_failure_logs_818(seed=qs_seed)
    assert failures["count"] >= 1
    assert failures["devops_alert_on_final_failure"] is True


def test_818_market_radar_refresh(qs_seed):
    refresh = qs.build_market_radar_scheduled_refresh_818("BTC", seed=qs_seed)
    assert refresh["fresh_dashboard"] is True
    assert refresh["schedule"] == "hourly"


def test_818_e2e(qs_seed):
    e2e = qs.run_query_scheduler_e2e_818(seed=qs_seed)
    assert e2e["all_passed"] is True


def test_818_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/data-engine/query-scheduler/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-engine/query-scheduler/queries").status_code == 200
    resp = c.post("/api/platform/intelligence-ledger/data-engine/query-scheduler/execute?query_id=sq-market-radar-btc")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    e2e = c.get("/api/platform/intelligence-ledger/data-engine/query-scheduler/e2e")
    assert e2e.status_code == 200
    assert e2e.json()["all_passed"] is True
