"""Retention & Deletion Policy — merged #949 + #1023."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


async def _ensure_user(email: str) -> None:
    from database import create_user, fetch_user_by_email

    if await fetch_user_by_email(email) is None:
        await create_user(email, "pbkdf2_sha256$test$" + "x" * 64, "Retention Test")


@pytest.fixture
def retention_env(monkeypatch, tmp_path):
    state = tmp_path / "state.json"
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr("data_retention_governance._STATE_PATH", state)
    monkeypatch.setattr("data_retention_governance._AUDIT_PATH", audit)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    return {"state": state, "audit": audit}


def test_seed_loads():
    from data_retention_governance import _load_seed

    seed = _load_seed()
    assert seed["standalone_rejected"] is True
    tiers = seed["retention_deletion_policy"]["retention_tiers"]
    assert tiers["raw_data_days"] == 90
    assert tiers["aggregated_days"] == 730
    assert tiers["audit_logs_days"] == 730
    assert tiers["immutable_records_days"] == 1825


def test_policy_status(retention_env):
    from data_retention_governance import retention_deletion_policy_status

    status = retention_deletion_policy_status()
    assert status["ok"] is True
    assert status["non_custodial"] is True
    assert status["retention_tiers"]["raw_data_days"] == 90


def test_legal_hold_blocks_erasure(retention_env):
    from data_retention_governance import is_legal_hold_active, set_legal_hold

    set_legal_hold("hold@example.com", active=True, reason="litigation", admin_actor="admin")
    assert is_legal_hold_active("hold@example.com") is True


@pytest.mark.asyncio
async def test_schedule_erasure_soft_delete(retention_env):
    from data_retention_governance import get_deletion_request_status, schedule_erasure
    from database import create_user, fetch_user_by_email

    email = _unique_email("erase-me")
    await _ensure_user(email)
    assert await fetch_user_by_email(email) is not None

    result = await schedule_erasure(email, actor="user")
    assert result["status"] == "soft_deleted"
    assert result["grace_days"] == 30
    assert "scheduled_hard_delete_at" in result

    req = get_deletion_request_status(email)
    assert req is not None
    assert req["status"] == "soft_deleted"


@pytest.mark.asyncio
async def test_erasure_blocked_by_legal_hold(retention_env):
    from data_retention_governance import schedule_erasure, set_legal_hold
    from database import create_user

    email = _unique_email("blocked")
    await _ensure_user(email)
    set_legal_hold(email, active=True, reason="litigation")

    result = await schedule_erasure(email)
    assert result["status"] == "blocked_legal_hold"


@pytest.mark.asyncio
async def test_hard_delete_after_grace(retention_env):
    from data_retention_governance import execute_hard_delete, schedule_erasure
    from database import create_user, fetch_user_by_email

    email = _unique_email("hard-delete")
    await _ensure_user(email)
    await schedule_erasure(email)

    result = await execute_hard_delete(email)
    assert result["status"] == "completed"
    assert await fetch_user_by_email(email) is None


@pytest.mark.asyncio
async def test_gdpr_erase_schedules_workflow(retention_env):
    from gdpr_service import erase_user_data
    from database import create_user

    email = _unique_email("gdpr")
    await _ensure_user(email)

    pending = await erase_user_data(email, confirmed=False)
    assert pending["status"] == "confirmation_required"

    scheduled = await erase_user_data(email, confirmed=True)
    assert scheduled["status"] == "soft_deleted"
    assert scheduled["gdpr_article"] == 17


@pytest.mark.asyncio
async def test_immutable_audit_anonymize(retention_env, tmp_path, monkeypatch):
    from pathlib import Path as RealPath

    import data_retention_governance as drg

    audit_dir = tmp_path / "immutable_recommendation_audit"
    audit_dir.mkdir()
    audit_file = audit_dir / "rec.jsonl"
    audit_file.write_text(
        json.dumps({"user_email": "anon@example.com", "user_id": 5, "action": "recommend"}) + "\n",
        encoding="utf-8",
    )

    def fake_path(value: str = ".") -> RealPath:
        if "immutable_recommendation_audit" in str(value):
            return audit_dir
        return RealPath(value)

    monkeypatch.setattr(drg, "Path", fake_path)

    result = await drg.anonymize_immutable_audit_records("anon@example.com")
    assert result["anonymized"] >= 1
    row = json.loads(audit_file.read_text(encoding="utf-8").strip())
    assert row["user_email"] == "anonymized"


def test_production_gate(retention_env):
    from data_retention_governance import check_retention_deletion_production_gate

    gate = check_retention_deletion_production_gate()
    assert gate["checks"]["tiers_documented"] is True
    assert gate["ok"] is True


def test_e2e(retention_env):
    from data_retention_governance import run_retention_deletion_e2e

    result = run_retention_deletion_e2e()
    assert result["ok"] is True
    assert result["all_passed"] is True


@pytest.mark.asyncio
async def test_daily_job_runs(retention_env):
    from data_retention_governance import run_retention_deletion_job

    with patch("db_upgrade.prune_old_market_rows", new_callable=AsyncMock) as mock_prune:
        mock_prune.return_value = {"pricing_logs": 1}
        result = await run_retention_deletion_job()
    assert result["ok"] is True
    assert "tier_enforcement" in result


@pytest.mark.asyncio
async def test_platform_routes(retention_env):
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in (
            "/api/platform/retention-deletion/status",
            "/api/platform/retention-deletion/gate",
            "/api/platform/retention-deletion/e2e",
        ):
            r = await client.get(path)
            assert r.status_code == 200, path
            body = r.json()
            assert body.get("ok") is True or body.get("all_passed") is True


def test_stripe_and_backup_notes():
    from data_retention_governance import backup_deletion_note, stripe_billing_retention_note

    stripe = stripe_billing_retention_note()
    backup = backup_deletion_note()
    assert stripe["stripe_handles_payment_data"] is True
    assert backup["no_resurrection"] is True


@pytest.mark.asyncio
async def test_audit_written_on_schedule(retention_env):
    from data_retention_governance import schedule_erasure
    from database import create_user

    email = _unique_email("audit-test")
    await _ensure_user(email)
    await schedule_erasure(email)

    lines = retention_env["audit"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    row = json.loads(lines[-1])
    assert row["action"] == "erasure_scheduled"
