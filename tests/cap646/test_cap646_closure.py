"""CAP646 closure tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_evidence_class_footer():
    from cap646.evidence_class import ai_compliance_footer

    out = ai_compliance_footer({"success": True, "source": "oracle"})
    assert out["evidence_class"] in {"SHADOW_LIVE_FORWARD", "PRODUCTION_VERIFIED", "BACKTESTED", "SIMULATED"}
    assert "compliance_footer" in out


@pytest.mark.asyncio
async def test_wave_a_f0_631():
    from cap646.data_spine import ingestion_architecture_report

    report = await ingestion_architecture_report()
    assert report["capability_id"] == 631
    assert report["success"] is True
    assert report["compliance_footer"]


@pytest.mark.asyncio
async def test_verified_capability_63():
    from cap646.runtime import execute_capability

    result = await execute_capability(63, skip_entitlement=True)
    assert result["success"] is True
    assert result.get("compliance_footer")


@pytest.mark.asyncio
async def test_external_blocked():
    from cap646.functional_dod import verify_functional

    report = await verify_functional(645)
    assert report["verdict"] == "EXTERNAL_EVIDENCE_REQUIRED"


@pytest.mark.asyncio
async def test_duplicate_routes_to_canonical():
    from cap646.runtime import execute_capability

    dup = await execute_capability(106, skip_entitlement=True)
    assert dup.get("duplicate_of") == 63


@pytest.mark.asyncio
async def test_cap646_api_catalog():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.get("/api/cap646/catalog?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 5


@pytest.mark.asyncio
async def test_closure_sample(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "cap646.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.closure import final_institutional_verification

    report = await final_institutional_verification(sample_only=True)
    assert report["total_checked"] >= 10
    assert "counts" in report
