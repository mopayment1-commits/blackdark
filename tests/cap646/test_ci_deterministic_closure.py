"""CI deterministic structural closure tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_ci_deterministic_sample_closure_stable(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "ci_det.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.setenv("BLACKDARK_CI_DETERMINISTIC_CLOSURE", "true")
    await database.init_db()

    from institutional_assurance import publish_signed_capacity

    publish_signed_capacity(
        environment="staging",
        workers=2,
        postgres=True,
        redis=True,
        requests=80,
        p50_ms=131.3,
        p95_ms=143.4,
        p99_ms=167.5,
        error_rate=0.0,
        operator="ci-test",
        notes="SIGNED: CI deterministic closure test",
    )

    from cap978.closure import institutional_closure_978

    snapshots: list[list[int]] = []
    for _ in range(3):
        report = await institutional_closure_978(sample=True, ci_deterministic=True)
        assert report["verification_mode"] == "ci_structural_no_network"
        assert report["cap978"]["FUNCTIONALLY_INCOMPLETE"] == 0
        assert report["cap978"]["incomplete_sample"] == []
        snapshots.append(list(report["cap978"]["incomplete_sample"]))

    assert snapshots[0] == snapshots[1] == snapshots[2] == []


@pytest.mark.asyncio
async def test_ci_deterministic_institutional_gate_passes(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "ci_gate.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.setenv("BLACKDARK_CI_DETERMINISTIC_CLOSURE", "true")
    await database.init_db()

    from institutional_assurance import publish_signed_capacity

    publish_signed_capacity(
        environment="staging",
        workers=2,
        postgres=True,
        redis=True,
        requests=80,
        p50_ms=131.3,
        p95_ms=143.4,
        p99_ms=167.5,
        error_rate=0.0,
        operator="ci-test",
        notes="SIGNED: CI gate deterministic test",
    )

    from cap978.institutional_gate import run_institutional_gate

    for _ in range(3):
        report = await run_institutional_gate(sample=True, check_artifacts=True, include_commercial=False)
        assert report["verdict"] == "PASS", report.get("failures")
        assert report["mode"] == "sample_ci_structural"
        assert report["checks_failed"] == 0
