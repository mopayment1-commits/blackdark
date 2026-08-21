"""Wave A/B DoD and UI E2E tests."""

from __future__ import annotations

import pytest

from cap646.waves import WAVE_A, WAVE_B, WAVE_D


@pytest.mark.asyncio
async def test_wave_a_dod(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.dod import verify_wave

    report = await verify_wave(WAVE_A)
    assert report["total"] == len(WAVE_A)
    not_ready = report["counts"].get("NOT_READY", 0)
    assert not_ready <= 2, report["counts"]


@pytest.mark.asyncio
async def test_wave_b_dod(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.dod import verify_wave

    report = await verify_wave(WAVE_B)
    assert report["total"] == len(WAVE_B)
    assert report["counts"].get("NOT_READY", 0) == 0, report["counts"]


@pytest.mark.asyncio
async def test_wave_c_dod(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.dod import verify_wave
    from cap646.waves import WAVE_C

    report = await verify_wave(WAVE_C)
    assert report["total"] == len(WAVE_C)
    assert report["counts"].get("NOT_READY", 0) == 0, report["counts"]


@pytest.mark.asyncio
async def test_cap646_hub_page():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.get("/cap646")
    assert r.status_code == 200
    assert "CAP646 Capability Hub" in r.text
    assert "cap646_hub.js" in r.text


@pytest.mark.asyncio
async def test_wave_api_ids():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.get("/api/cap646/wave/A/ids")
    assert r.status_code == 200
    assert len(r.json()["ids"]) == len(WAVE_A)


@pytest.mark.asyncio
async def test_wave_d_sample_execute(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.runtime import execute_capability

    sample = WAVE_D[:5]
    for cid in sample:
        result = await execute_capability(cid, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
        assert result.get("compliance_footer"), f"ID{cid} missing footer"
        assert result.get("success") is True, f"ID{cid} failed: {result.get('error')}"
