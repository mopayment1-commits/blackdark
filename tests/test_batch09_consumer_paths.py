"""Batch09 actual consumer path evidence — beyond generic gateway-only proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_09_401_450.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.fixture
def client() -> TestClient:
    from dashboard import app

    return TestClient(app)


CONSUMER_EXPECTATIONS: dict[int, dict] = {
    409: {"mode": "B2B feed status", "surface": "quicktake"},
    425: {"mode": "AI/copilot", "surface": "ai_analyst"},
    426: {"mode": "research workspace", "surface": "thesis_research"},
    428: {"mode": "Excel/Sheets export", "surface": "excel_sheets", "field": "export_rows"},
    429: {"mode": "institutional API", "surface": "api_data", "field": "quota_utilization_pct"},
    431: {"mode": "dashboard UI", "surface": "dashboards", "field": "widget_count"},
    435: {"mode": "cross-market copilot", "surface": "cross_market", "field": "copilot_blend_score"},
    446: {"mode": "alert/event", "surface": "real_time", "field": "alert_count_24h"},
    448: {"mode": "institutional risk API", "surface": "institutional_risk_api", "field": "coverage_pct"},
}


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_consumer_path_via_platform_handler(client: TestClient, capability_id: int):
    """HTTP → cap646 runtime → handle_platform_capability → registry backend."""
    from cap646.runtime import execute_capability

    http = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
    assert http.status_code == 200
    body = http.json()
    assert body.get("success") is True

    direct = __import__("asyncio").run(execute_capability(capability_id, params={"symbol": "BTC"}))
    assert direct.get("ok") is True or direct.get("success") is True
    assert direct.get("capability_id") == capability_id or direct.get("requested_capability_id") == capability_id


@pytest.mark.parametrize("capability_id,meta", list(CONSUMER_EXPECTATIONS.items()))
def test_material_consumer_surface_fields(client: TestClient, capability_id: int, meta: dict):
    response = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
    payload = response.json().get("data") or response.json()
    if isinstance(payload, dict) and "result" in payload:
        payload = payload["result"]
    for key in ("surface", "field"):
        if key not in meta:
            continue
        if key == "surface":
            assert meta["surface"] in json.dumps(payload).lower()
        else:
            assert meta["field"] in payload
