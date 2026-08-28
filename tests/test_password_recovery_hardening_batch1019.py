"""Tests — Secure Password Recovery Hardening (#1019)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

import password_recovery_hardening as prh


@pytest.fixture
def pr_seed() -> dict:
    return json.loads(Path("data/session_account_security_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset(tmp_path, monkeypatch):
    prh.reset_password_recovery_state()
    audit = Path("data/password_recovery_audit.jsonl")
    if audit.is_file():
        audit.unlink()
    devices = Path("data/password_recovery_devices.json")
    if devices.is_file():
        devices.unlink()
    yield
    prh.reset_password_recovery_state()


def test_recovery_status(pr_seed):
    status = prh.password_recovery_status(seed=pr_seed)
    assert status["policy"]["security_questions_forbidden"] is True
    assert status["policy"]["token_expiry_minutes"] == 15
    assert status["standalone_rejected"] is True


def test_security_questions_rejected():
    with pytest.raises(ValueError, match="Security questions"):
        prh.assert_no_security_questions({"security_question": "pet name?"})


def test_email_rate_limit(pr_seed):
    for _ in range(3):
        prh.check_password_recovery_rate_limits(email="u@example.com", ip="1.1.1.1", seed=pr_seed)
    with pytest.raises(ValueError, match="email"):
        prh.check_password_recovery_rate_limits(email="u@example.com", ip="1.1.1.1", seed=pr_seed)


def test_ip_rate_limit(pr_seed):
    for i in range(5):
        prh.check_password_recovery_rate_limits(email=f"u{i}@example.com", ip="9.9.9.9", seed=pr_seed)
    with pytest.raises(ValueError, match="network"):
        prh.check_password_recovery_rate_limits(email="x@example.com", ip="9.9.9.9", seed=pr_seed)


def test_device_fingerprint_and_known_device():
    fp = prh.compute_device_fingerprint(user_agent="Mozilla", ip="10.0.0.1")
    assert len(fp) == 32
    assert prh.is_known_device(1, fp) is False
    prh.register_known_device(1, fp)
    assert prh.is_known_device(1, fp) is True


def test_audit_trail(pr_seed):
    prh.log_recovery_event("reset_requested", email="a@b.com", result="ok", seed=pr_seed)
    trail = prh.get_password_recovery_audit_trail()
    assert trail["events_count"] >= 1
    assert trail["append_only"] is True


def test_notification_template(pr_seed):
    body = prh.password_changed_notification_body(seed=pr_seed)
    assert "wasn't you" in body.lower() or "wasn't you" in body


def test_hardened_reset_flow(tmp_path, monkeypatch, pr_seed):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "pr.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "unit-test-mfa-key-not-for-prod-32b!")

    async def _fake_email(*_a, **_k):
        return {"queued": True, "flush": {"status": "skipped"}}

    monkeypatch.setattr("identity_service.enqueue_identity_email", _fake_email)

    async def _run():
        await database.init_db()
        uid = await database.create_user(
            "hardened@example.com", hash_password("old-password-99"), "Hardened"
        )
        await prh.send_hardened_password_reset(
            uid, "hardened@example.com", ip="127.0.0.1", seed=pr_seed
        )
        from identity_service import issue_auth_token

        token = await issue_auth_token(uid, "password_reset")
        result = await prh.complete_hardened_password_reset(
            token=token,
            new_password="new-secure-pass-42",
            ip="127.0.0.1",
            seed=pr_seed,
        )
        assert result["sessions_invalidated"] is True
        row = await database.fetch_user_by_id(uid)
        from auth_service import verify_password

        assert verify_password("new-secure-pass-42", row["password_hash"])

    asyncio.run(_run())


def test_token_ttl_15_minutes():
    from identity_service import TOKEN_TTL_MINUTES

    assert TOKEN_TTL_MINUTES["password_reset"] == 15


def test_production_gate(pr_seed):
    gate = prh.check_password_recovery_gate(seed=pr_seed)
    assert gate["ok"] is True


def test_e2e_password_recovery(pr_seed):
    result = prh.run_password_recovery_e2e(seed=pr_seed)
    assert result["all_passed"] is True
