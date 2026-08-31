"""Tests — #289 Alert Engine (renamed from Smart Alerts)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import alert_engine as ae


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "alert_engine_seed.json"
    seed.write_text(
        json.dumps({
            "current_phase": 1,
            "rules": [
                {
                    "rule_id": "r1",
                    "name": "BTC above 100k",
                    "type": "price",
                    "condition": {"field": "price", "operator": ">=", "threshold": 100000},
                    "current_value": 95020,
                },
                {
                    "rule_id": "r2",
                    "name": "Recent fire",
                    "type": "price",
                    "condition": {"field": "price", "operator": ">=", "threshold": 90000},
                    "current_value": 95020,
                    "last_fired_at": "2026-08-25T23:58:00+00:00",
                },
            ],
            "delivery_log": [
                {
                    "alert_id": "d1",
                    "rule_id": "r1",
                    "channel": "push",
                    "attempts": 1,
                    "success": True,
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ae, "_SEED_PATH", seed)
    return seed


def test_renamed_not_smart_alerts(isolated_seed):
    status = ae.alert_engine_status()
    assert status["feature_id"] == 289
    assert status["renamed_from"] == "Smart Alerts"
    assert status["title"] == "Alert Engine"


def test_backend_enforcement(isolated_seed):
    enforcement = ae.build_backend_enforcement()
    assert enforcement["server_side_evaluation"] is True
    assert enforcement["no_client_side_only"] is True
    assert "push" in enforcement["delivery_channels"]
    assert enforcement["deduplication_window_sec"] == 300
    assert enforcement["max_retries"] == 3
    assert enforcement["log_retention_days"] == 90


def test_rule_evaluation_server_side(isolated_seed):
    result = ae.evaluate_rule({
        "rule_id": "t1",
        "name": "test",
        "type": "price",
        "condition": {"field": "price", "operator": ">=", "threshold": 90000},
        "current_value": 95000,
    })
    assert result["triggered"] is True
    assert result["server_side"] is True


def test_dedupe_suppression(isolated_seed):
    from datetime import UTC, datetime
    now = datetime.now(UTC).isoformat()
    result = ae.evaluate_rule({
        "rule_id": "r2",
        "name": "recent",
        "type": "price",
        "condition": {"field": "price", "operator": ">=", "threshold": 90000},
        "current_value": 95020,
        "last_fired_at": now,
    })
    assert result["dedupe_suppressed"] is True
    assert result["status"] == "suppressed"


def test_scope_lock_phases(isolated_seed):
    scope = ae.build_scope_lock()
    assert scope["rule_based_first"] is True
    assert scope["no_smart_ai_implied"] is True
    assert "Price alerts" in scope["phases"][1]


def test_delivery_logs(isolated_seed):
    logs = ae.list_delivery_logs()
    assert logs["log_retention_days"] == 90
    assert logs["logs"][0]["channel"] == "push"


def test_panel(isolated_seed):
    panel = ae.build_alert_engine_panel()
    assert panel["ok"] is True
    assert panel["no_smart_ai_implied"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/alert-engine/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/alert-engine").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/alert-engine/rules").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/alert_engine_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 289
    assert seed["renamed_from"] == "Smart Alerts"
