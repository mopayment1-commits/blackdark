"""Tests — Session Lifecycle Hardening (#1019)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import session_lifecycle_hardening as slh


@pytest.fixture
def slh_seed() -> dict:
    return json.loads(Path("data/session_account_security_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset():
    slh.reset_session_lifecycle_state()
    audit = Path("data/session_audit.jsonl")
    if audit.is_file():
        audit.unlink()
    device = Path("data/session_device_store.json")
    if device.is_file():
        device.unlink()
    yield
    slh.reset_session_lifecycle_state()


def test_lifecycle_status_no_standalone(slh_seed):
    status = slh.session_lifecycle_status(seed=slh_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["idle_timeout_minutes"] == 30
    assert status["policy"]["absolute_timeout_hours"] == 8
    assert status["policy"]["global_logout_endpoint"] == "/auth/logout-all"


def test_idle_timeout_detection(slh_seed):
    reason = slh.evaluate_session_expiry(
        created_at=datetime.now(UTC).isoformat(),
        expires_at=slh.compute_absolute_expires_at(seed=slh_seed),
        last_activity_at=(datetime.now(UTC) - timedelta(minutes=31)).isoformat(),
        seed=slh_seed,
    )
    assert reason == "idle-timeout"


def test_absolute_timeout_detection(slh_seed):
    reason = slh.evaluate_session_expiry(
        created_at=(datetime.now(UTC) - timedelta(hours=9)).isoformat(),
        expires_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        last_activity_at=datetime.now(UTC).isoformat(),
        seed=slh_seed,
    )
    assert reason == "absolute-timeout"


def test_revocation_list(slh_seed):
    token_hash = "deadbeef" * 4
    slh.revoke_token_hash(token_hash)
    assert slh.is_token_revoked(token_hash) is True


def test_session_audit_append_only(slh_seed):
    slh.log_session_event("create", user_id=7, email="u@example.com", seed=slh_seed)
    slh.log_session_event("global-logout", user_id=7, seed=slh_seed)
    trail = slh.get_session_audit_trail(limit=10)
    assert trail["events_count"] >= 2
    assert trail["append_only"] is True
    assert Path("data/session_audit.jsonl").is_file()


def test_device_fingerprint(slh_seed):
    fp = slh.compute_device_fingerprint(user_agent="Mozilla", ip="10.0.0.1")
    assert len(fp) == 32
    slh.register_session_device(1, fp)
    assert slh.is_known_session_device(1, fp) is True


@pytest.mark.asyncio
async def test_global_logout_all(monkeypatch, slh_seed):
    revoked: list[int] = []

    async def _delete(uid: int) -> int:
        revoked.append(uid)
        return 2

    async def _tokens(uid: int) -> list[str]:
        return ["hash1", "hash2"]

    monkeypatch.setattr("database.delete_user_sessions_for_user", _delete)
    monkeypatch.setattr("database.list_user_session_tokens", _tokens)
    monkeypatch.setattr(
        "identity_service.enqueue_identity_email",
        lambda *a, **k: {"queued": True},
    )

    result = await slh.global_logout_all(42, email="u@example.com", ip="1.2.3.4", seed=slh_seed)
    assert result["ok"] is True
    assert result["sessions_revoked"] == 2
    assert revoked == [42]
    assert slh.is_token_revoked("hash1")
    assert slh.is_token_revoked("hash2")


@pytest.mark.asyncio
async def test_validate_and_touch_session_expired(monkeypatch, slh_seed):
    token_hash = "tok" * 8
    row = {
        "id": 1,
        "email": "u@example.com",
        "session_created_at": (datetime.now(UTC) - timedelta(hours=9)).isoformat(),
        "session_expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        "last_activity_at": datetime.now(UTC).isoformat(),
    }
    deleted: list[str] = []

    async def _delete(token: str) -> None:
        deleted.append(token)

    monkeypatch.setattr("database.delete_user_session", _delete)

    result = await slh.validate_and_touch_session(token_hash, row, seed=slh_seed)
    assert result is None
    assert deleted == [token_hash]


def test_production_gate(slh_seed):
    gate = slh.check_session_lifecycle_gate(seed=slh_seed)
    assert gate["ok"] is True
    assert gate["checks"]["idle_30m"] is True
    assert gate["checks"]["absolute_8h"] is True


def test_e2e(slh_seed):
    result = slh.run_session_lifecycle_e2e(seed=slh_seed)
    assert result["all_passed"] is True
