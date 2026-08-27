"""D-13 — auth abuse and security verification hooks."""

from __future__ import annotations

from pathlib import Path

from security_auth import hash_session_token, verify_admin_key


def test_admin_key_rejects_empty(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "real-admin-key-12345678")
    assert verify_admin_key("") is False
    assert verify_admin_key("wrong-key") is False


def test_session_token_not_reversible():
    token = "user-session-token-abc"
    hashed = hash_session_token(token)
    assert token not in hashed
    assert len(hashed) == 64


def test_d13_verification_matrix_exists():
    path = Path(__file__).resolve().parents[1] / "docs/security/D13_VERIFICATION_MATRIX.md"
    text = path.read_text(encoding="utf-8")
    assert "D-13" in text
    assert "bandit" in text.lower() or "SAST" in text


def test_security_workflow_references_defect_tests():
    wf = Path(__file__).resolve().parents[1] / ".github/workflows/security.yml"
    text = wf.read_text(encoding="utf-8")
    assert "pytest-security" in text
    assert "test_d13" in text or "test_security" in text
