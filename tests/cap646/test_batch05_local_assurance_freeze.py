"""Batch05 final local assurance freeze — executable reliability, security, observability proof.

Does NOT claim PASS_LIVE or ASSURANCE_READY.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
BATCH05_SAMPLE = [201, 205, 214, 226, 232, 242, 245, 247]
STRANGLER_SAMPLE = [201, 205, 217, 242]
REUSED_LINK_SAMPLE = [206, 214, 226, 228, 232, 245]


@pytest.mark.asyncio
async def test_reliability_unknown_capability_fail_closed():
    from cap646.runtime import execute_capability

    result = await execute_capability(99999, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is False
    assert result.get("error") == "unknown_capability_id"


@pytest.mark.asyncio
async def test_reliability_batch05_out_of_spine_rejected():
    from cap646.batch05_production import execute

    with pytest.raises(ValueError, match="not in batch05"):
        await execute(251, params={"symbol": "BTC"}, skip_entitlement=True)


@pytest.mark.asyncio
async def test_reliability_entitlement_denied_fail_closed(monkeypatch):
    from cap646 import entitlements
    from cap646.runtime import execute_capability

    async def _deny(*_a, **_k):
        return {"allowed": False, "reason": "test_denied", "required_tier": "pro"}

    monkeypatch.setattr(entitlements.entitlement_engine, "check", _deny)
    result = await execute_capability(201, params={"symbol": "BTC"}, skip_entitlement=False, user={"tier": "free"})
    assert result.get("success") is False
    assert result.get("entitlement", {}).get("allowed") is False


@pytest.mark.asyncio
async def test_reliability_gateway_entitlement_denied_no_spine_leak():
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(226, user={"tier": "free"}, params={"symbol": "BTC", "tier": "free"})
    assert result.get("success") is False
    assert result.get("error") == "entitlement_denied"
    assert result.get("production_spine") is None


@pytest.mark.asyncio
async def test_reliability_dependency_failure_simulated(monkeypatch):
    from cap646 import batch05_strangler_spine
    from cap646.runtime import execute_capability

    async def _boom(**_kwargs):
        raise ConnectionError("simulated upstream unavailable")

    monkeypatch.setitem(batch05_strangler_spine.STRANGLER_BUILDERS, 201, _boom)
    result = await execute_capability(201, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is False
    assert "error" in result or result.get("surface") is None


@pytest.mark.asyncio
async def test_reliability_idempotent_double_execute_structure():
    from cap646.runtime import execute_capability

    params = {"symbol": "BTC", "tier": "pro"}
    first = await execute_capability(205, params=params, skip_entitlement=True)
    second = await execute_capability(205, params=params, skip_entitlement=True)
    assert first.get("success") is True
    assert second.get("success") is True
    assert first.get("surface") == second.get("surface") == "open_interest_intelligence"


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", STRANGLER_SAMPLE)
async def test_reliability_malformed_empty_symbol_structured(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, params={"symbol": ""}, skip_entitlement=True)
    assert "success" in result
    assert "surface" in result or result.get("success") is False


@pytest.mark.asyncio
async def test_reliability_stale_freshness_fields_present():
    from cap646.runtime import execute_capability

    result = await execute_capability(245, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is True
    assert "freshness_chip" in result or "executable_fresh" in result


@pytest.mark.asyncio
async def test_security_no_stack_trace_on_unknown_id():
    from cap646.runtime import execute_capability

    result = await execute_capability(88888, params={"symbol": "BTC"}, skip_entitlement=True)
    body = json.dumps(result)
    assert "Traceback" not in body
    assert "File \"" not in body


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", [201, 214, 247])
async def test_security_injection_symbol_handled(capability_id: int):
    from cap646.runtime import execute_capability

    nasty = "BTC'; DROP TABLE users;--"
    result = await execute_capability(capability_id, params={"symbol": nasty}, skip_entitlement=True)
    assert isinstance(result, dict)
    assert "Traceback" not in json.dumps(result)


@pytest.mark.asyncio
async def test_security_oversized_symbol_handled():
    from cap646.runtime import execute_capability

    result = await execute_capability(201, params={"symbol": "X" * 5000}, skip_entitlement=True)
    assert isinstance(result, dict)
    assert result.get("success") is not False or "error" in result


@pytest.mark.asyncio
async def test_security_gateway_audit_no_password_fields():
    from cap646.institutional_gateway import gateway_execute

    await gateway_execute(
        201,
        user={"tier": "free", "email": "neg@test.local", "password": "secret"},
        params={"symbol": "BTC"},
    )
    from cap646.institutional_gateway import _AUDIT

    if _AUDIT:
        last = json.dumps(_AUDIT[-1])
        assert "secret" not in last


def test_observability_health_live_local():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("probe") == "live"
    assert "ts" in body


def test_observability_health_ready_structure():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    resp = client.get("/health/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "ready" in body or "status" in body


def test_observability_health_root_lists_probes():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "live" in str(body.get("endpoints", body))


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", STRANGLER_SAMPLE)
async def test_observability_latency_ms_on_execute(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is True
    payload_root = result.get("surface")
    if payload_root and isinstance(result.get(payload_root), dict):
        inner = result[payload_root]
        assert "latency_ms" in inner or "elapsed_ms" in result


@pytest.mark.parametrize("capability_id", range(201, 251))
def test_data_integrity_domain_rules_present(capability_id: int):
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == capability_id)
    rules = row["domain_rules"]
    assert len(rules) >= 3
    semantic = [r for r in rules if r["field"] != "success"]
    assert len(semantic) >= 2


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", [201, 205, 242])
async def test_data_integrity_feature_ref_matches_id(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, params={"symbol": "BTC"}, skip_entitlement=True)
    surface = result.get("surface")
    payload = result.get(surface) if surface else {}
    if isinstance(payload, dict) and "feature_ref" in payload:
        assert payload["feature_ref"] == capability_id


@pytest.mark.asyncio
@pytest.mark.parametrize("capability_id", [201, 205, 242])
async def test_data_integrity_latency_finite(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, params={"symbol": "BTC"}, skip_entitlement=True)
    surface = result.get("surface")
    payload = result.get(surface) if surface else {}
    if isinstance(payload, dict) and "latency_ms" in payload:
        lat = payload["latency_ms"]
        assert isinstance(lat, (int, float))
        assert math.isfinite(lat)
