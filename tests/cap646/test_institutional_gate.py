"""Institutional gate tests — fast invariant checks + sample gate run."""

from __future__ import annotations

import pytest


def test_catalog_integrity():
    from cap978.institutional_gate import validate_catalog_integrity

    checks = validate_catalog_integrity()
    assert all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]


def test_external_registry_integrity():
    from cap978.institutional_gate import validate_external_registry_integrity

    checks = validate_external_registry_integrity()
    assert all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]


def test_committed_artifacts_match_baseline():
    from cap978.institutional_gate import validate_committed_artifacts

    checks = validate_committed_artifacts()
    assert all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]


def test_commercial_launch_checklist():
    from cap978.institutional_gate import CLOSURE_BASELINE, commercial_launch_checklist

    report = commercial_launch_checklist()
    expected_total = CLOSURE_BASELINE["external_registry"]["total"]
    assert report["internal_closure_complete"] is True
    assert report["commercial_launch_ready"] is False
    assert report["total_external_items"] == expected_total
    assert report["p0_blockers"] >= 3
    assert all(i["owner"] == "external" for i in report["items"])


@pytest.mark.slow
@pytest.mark.asyncio
async def test_institutional_gate_sample(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "gate.db"))
    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap978.institutional_gate import run_institutional_gate

    report = await run_institutional_gate(sample=True, check_artifacts=True, include_commercial=True)
    assert report["verdict"] == "PASS"
    assert report["checks_failed"] == 0


@pytest.mark.asyncio
async def test_institutional_gate_full(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "gate_full.db"))
    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap978.closure import institutional_closure_978
    from cap978.institutional_gate import run_institutional_gate, validate_closure_invariants

    closure = await institutional_closure_978()
    invariant_checks = validate_closure_invariants(closure)
    assert all(c["ok"] for c in invariant_checks), [c for c in invariant_checks if not c["ok"]]

    report = await run_institutional_gate(sample=False, check_artifacts=True, include_commercial=False)
    assert report["verdict"] == "PASS"
    assert report["closure_verdict"] == "INSTITUTIONAL_GATE_PASS"
