"""Soft Launch institutional closure tests."""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]


def _load_softlaunch_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mirror scripts/run_soft_launch_closure.py — CI bootstraps before pytest."""
    env_file = _ROOT / ".env.softlaunch.local"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, _, value = raw.partition("=")
        key = key.strip()
        if key:
            monkeypatch.setenv(key, value.strip())


def test_legal_and_honesty_checks():
    from cap978.soft_launch_closure import validate_legal_and_honesty

    checks = validate_legal_and_honesty()
    assert all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]


@pytest.mark.asyncio
async def test_soft_launch_closure_code_complete(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "soft.db"))
    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    _load_softlaunch_env(monkeypatch)
    await database.init_db()

    from cap978.soft_launch_closure import run_soft_launch_closure

    snap = await run_soft_launch_closure(include_institutional_gate=False, check_artifacts=False)
    failed = snap.get("failures") or []
    assert snap["checks_failed"] == 0 or snap["verdict"].startswith(
        ("CODE COMPLETE", "VERIFIED COMPLETE")
    ), f"verdict={snap['verdict']!r} failures={failed}"
    assert snap["tracks"]["COMMERCIAL_INSTITUTIONAL"] is False
    assert "Shadow-forward" in snap["positioning"]


@pytest.mark.asyncio
async def test_soft_launch_with_production_guard(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "guard.db"))
    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.delenv("DATABASE_URL", raising=False)
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
