"""Triple reference institutional closure tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_institutional_controls_42():
    from cap646.institutional_controls import verify_all_controls

    report = await verify_all_controls()
    assert report["total"] == 42
    assert report["counts"].get("NOT_READY", 0) == 0
    external = report["counts"].get("EXTERNAL_BLOCKED", 0) + report["counts"].get("EXTERNAL_EVIDENCE_REQUIRED", 0)
    assert external >= 4  # SEC-008/009, REL-002, etc.


@pytest.mark.asyncio
async def test_data_platform_chain(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.platform_chain import verify_data_platform_chain

    chain = await verify_data_platform_chain(symbol="BTC")
    assert chain["verdict"] == "VERIFIED_COMPLETE"
    assert chain["internal_closure"] is True
    assert not chain["failed"]


@pytest.mark.asyncio
async def test_functional_wave_a_sample(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.functional_dod import verify_functional
    from cap646.waves import WAVE_A

    for cid in WAVE_A:
        if cid in {644, 645}:
            continue
        report = await verify_functional(cid)
        assert report["verdict"] in {"VERIFIED_COMPLETE", "EXTERNAL_EVIDENCE_REQUIRED"}, f"ID{cid}: {report}"


@pytest.mark.asyncio
async def test_triple_closure_sample(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.triple_closure import triple_institutional_closure
    from cap646.waves import WAVE_A, WAVE_B

    report = await triple_institutional_closure(sample_cap_ids=list(WAVE_A) + list(WAVE_B))
    assert "governing_controls" in report
    assert "data_platform_chain" in report
    assert report["data_platform_chain"]["verdict"] == "VERIFIED_COMPLETE"


@pytest.mark.asyncio
async def test_platform_compounding_e2e(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap646.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from platform_chain_e2e import run_platform_compounding_e2e

    e2e = await run_platform_compounding_e2e(symbol="BTC")
    assert e2e["verdict"] == "VERIFIED_COMPLETE"
    assert e2e["internal_closure"] is True
    evidence = e2e["acceptance_evidence"]
    assert evidence.get("prediction_id")
    assert evidence.get("decision_id")
    assert evidence.get("exposure_id")
    assert evidence.get("certificate_hash")


@pytest.mark.asyncio
async def test_platform_stores(tmp_path, monkeypatch):
    import config

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "stores.db"))

    from decision_ledger import ledger_stats, record_decision
    from market_event_library import event_library_stats, record_market_event
    from user_exposure_log import exposure_stats, record_user_exposure

    event = record_market_event(event_name="test", category="test", symbol="BTC", description="t")
    decision = record_decision(prediction_id="p1", decision_action="WAIT", symbol="BTC", evidence_class="SIMULATED")
    exposure = record_user_exposure(user_id="u1", tier="pro", surface="test", decision_id=decision["decision_id"], prediction_id="p1")
    assert event["event_id"] and decision["decision_id"] and exposure["exposure_id"]
    assert ledger_stats()["status"] == "active"
    assert exposure_stats()["status"] == "active"
    assert event_library_stats()["status"] == "active"


@pytest.mark.asyncio
async def test_user_surface_routes():
    from cap646.ui_pages import user_surface_for

    surf = user_surface_for(47)
    assert surf and surf.get("ui_path") and surf.get("api_path")
