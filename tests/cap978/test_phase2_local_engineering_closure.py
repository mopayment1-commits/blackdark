"""Phase 2 — local engineering closure tests for post-baseline capabilities (827–978)."""

from __future__ import annotations

import pytest

POST_BASELINE_IDS = list(range(827, 979))
WORKSET_HISTORICAL = [644, 645]


@pytest.mark.asyncio
async def test_runtime_wires_post_baseline_extension_ids(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "phase2-runtime.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")

    await database.init_db()

    from cap646.runtime import execute_capability

    user = {"email": "phase2@blackdark.local", "tier": "elite"}
    for cid in (827, 850, 900, 950, 978):
        result = await execute_capability(cid, user=user, params={"symbol": "BTC"})
        assert result.get("error") != "unknown_capability_id", result
        assert result.get("success") is True or result.get("classification"), result


@pytest.mark.parametrize("capability_id", POST_BASELINE_IDS)
@pytest.mark.asyncio
async def test_post_baseline_functional_verification(capability_id, tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / f"phase2-{capability_id}.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")

    await database.init_db()

    from cap978.verify import verify_functional_978

    report = await verify_functional_978(
        capability_id,
        user={"email": "phase2@blackdark.local", "tier": "elite"},
    )
    assert report["verdict"] == "VERIFIED_COMPLETE", report


@pytest.mark.asyncio
async def test_cap_0644_capacity_load_evidence_semantics():
    from cap646.institutional_official_production import execute

    result = await execute(644, params={"symbol": "BTC", "tier": "elite"})
    assert result.get("success") is True
    assert result.get("surface") == "capacity_load_evidence"
    assert result.get("handler_module") == "cap646.batch26_dedicated"
    payload = result.get("capacity_load_evidence") or {}
    assert payload.get("signed_load_evidence", {}).get("present") is True
    envelope = payload.get("safe_operating_envelope") or {}
    assert envelope.get("p50_ms") is not None
    assert envelope.get("p95_ms") is not None
    assert envelope.get("error_rate") is not None


@pytest.mark.asyncio
async def test_cap_0645_local_engineering_external_pending():
    from cap646.institutional_official_production import execute
    from pentest_attestation import verify_pentest_attestation

    result = await execute(645, params={"symbol": "BTC", "tier": "elite"})
    assert result.get("success") is True
    assert result.get("surface") == "security_verification_evidence"
    payload = result.get("security_verification_evidence") or {}
    assert payload.get("engineering_ready") is True
    assert payload.get("external_dependency_status") == "PENDING"
    assert verify_pentest_attestation() is False
