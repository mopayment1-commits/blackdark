"""Soft Launch institutional closure tests."""

from __future__ import annotations

import pytest


def test_legal_and_honesty_checks():
    from cap978.soft_launch_closure import validate_legal_and_honesty

    checks = validate_legal_and_honesty()
    assert all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]


@pytest.mark.asyncio
async def test_soft_launch_closure_code_complete(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "soft.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    for name in (
        "signal_registry.jsonl",
        "decision_ledger.jsonl",
        "market_event_library.jsonl",
        "failure_corpus.jsonl",
        "user_exposure_log.jsonl",
    ):
        (tmp_path.parent / "data" / name).parent.mkdir(parents=True, exist_ok=True)
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    for name in (
        "signal_registry.jsonl",
        "decision_ledger.jsonl",
        "market_event_library.jsonl",
        "failure_corpus.jsonl",
        "user_exposure_log.jsonl",
    ):
        (data_dir / name).write_text('{"seed":true}\n', encoding="utf-8")

    import cap978.soft_launch_closure as slc

    monkeypatch.setattr(slc, "_ROOT", tmp_path)
    for rel in (
        "docs/PRODUCT_CONSTITUTION_AR.md",
        "docs/RUNBOOK.md",
        "docs/GO_LIVE_AR.md",
        "legal_content.py",
        "coverage_honesty.py",
        "cap646/evidence_class.py",
        "signal_registry.py",
        "decision_ledger.py",
        "market_event_library.py",
        "failure_corpus.py",
        "user_exposure_log.py",
        "platform_chain_e2e.py",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")

    from cap978.soft_launch_closure import run_soft_launch_closure

    snap = await run_soft_launch_closure(include_institutional_gate=False, check_artifacts=False)
    assert snap["checks_failed"] == 0 or snap["verdict"].startswith("CODE COMPLETE")
    assert snap["tracks"]["COMMERCIAL_INSTITUTIONAL"] is False
    assert "Shadow-forward" in snap["positioning"]


@pytest.mark.asyncio
async def test_soft_launch_with_production_guard(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "guard.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "a" * 64)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "b" * 32)
    monkeypatch.setenv("ADMIN_API_KEY", "c" * 48)
    monkeypatch.setenv("ADMIN_EMAILS", "ops@test.local")
    monkeypatch.setenv("EXPOSE_B2B_DEMO_KEY", "false")
    monkeypatch.setenv("LIVE_EXECUTION_ALLOW_API", "false")
    await database.init_db()

    from production_guard import evaluate_production_guard

    guard = evaluate_production_guard()
    assert guard.get("soft_launch") is True

    from cap978.soft_launch_closure import evaluate_production_tracks

    tracks = await evaluate_production_tracks(guard=guard)
    assert tracks["soft_launch_mode"] is True
