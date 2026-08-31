"""CI deterministic structural closure tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

# Stable cap used only inside the permanent negative test (never mutates repo bindings).
_NEGATIVE_TEST_CAP_ID = 338


def _install_broken_binding(monkeypatch: pytest.MonkeyPatch, capability_id: int = _NEGATIVE_TEST_CAP_ID) -> None:
    """Return a non-importable entrypoint for one cap inside the test process only."""
    import cap978.ci_deterministic_closure as ci_mod
    from cap646.backend_registry import resolve_binding as real_resolve

    def _resolve(cid: int):
        binding = real_resolve(cid)
        if cid == capability_id:
            return replace(binding, entrypoint=f"{binding.entrypoint}_CI_GATE_NEGATIVE_TEST")
        return binding

    monkeypatch.setattr(ci_mod, "resolve_binding", _resolve)


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


@pytest.mark.asyncio
async def test_ci_deterministic_gate_detects_broken_binding(tmp_path, monkeypatch):
    """Permanent failprobe: gate must fail when a binding entrypoint is not importable."""
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "ci_neg.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.setenv("BLACKDARK_CI_DETERMINISTIC_CLOSURE", "true")
    _install_broken_binding(monkeypatch)
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
        notes="SIGNED: CI gate negative failprobe",
    )

    from cap978.institutional_gate import run_institutional_gate

    report = await run_institutional_gate(sample=True, check_artifacts=False, include_commercial=False)
    assert report["verdict"] == "FAIL"
    assert report["mode"] == "sample_ci_structural"
    assert report["checks_failed"] > 0
    failure_names = {item["name"] for item in report["failures"]}
    assert "sample_incomplete_ids" in failure_names
    assert str(_NEGATIVE_TEST_CAP_ID) in next(
        item["detail"] for item in report["failures"] if item["name"] == "sample_incomplete_ids"
    )
