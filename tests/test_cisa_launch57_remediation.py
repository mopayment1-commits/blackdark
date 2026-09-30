"""Launch-57 CISA remediation regression gates."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def strict_client(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "false")
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("USER_MFA_ENROLL_REQUIRED", "false")
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "test-audit-signing-key-32chars-minimum-xx")
    from dashboard import app

    return TestClient(app, base_url="https://example.test")


def test_security_txt_route(strict_client: TestClient):
    r = strict_client.get("/.well-known/security.txt")
    assert r.status_code == 200
    assert "Contact:" in r.text
    assert "Policy:" in r.text


def test_sso_status_allowed_without_session(strict_client: TestClient, monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    r = strict_client.get("/api/institutional/sso/status")
    assert r.status_code == 200
    assert r.json().get("surface") == "enterprise_sso"


def test_anonymous_denial_includes_security_headers(strict_client: TestClient):
    r = strict_client.get("/api/user/profile")
    assert r.status_code == 401
    assert r.headers.get("X-Blackdark-Auth-Boundary") == "anonymous-denied"
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Security-Hardening") == "1"


def test_public_security_status_is_minimal(strict_client: TestClient):
    r = strict_client.get("/api/security/status")
    assert r.status_code == 200
    body = r.json()
    assert body.get("surface") == "security_posture_public"
    assert "checks" not in body
    assert "pentest_attestation" not in body
    assert body.get("honesty", {}).get("cisa_certification_claimed") is False


def test_security_log_retention_minimum():
    from security_events import security_log_retention_days

    assert security_log_retention_days() >= 180


def test_webauthn_status_reports_library(monkeypatch):
    monkeypatch.setenv("WEBAUTHN_RP_ID", "example.test")
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    from webauthn_service import webauthn_status

    st = webauthn_status()
    assert st["library_available"] is True
    assert st["enabled"] is True


def test_launch57_closure_status_honest():
    from launch57_assurance_closure import launch57_closure_status

    report = launch57_closure_status()
    assert report["cisa_certification_claimed"] is False
    assert report["findings"]["pentest_attestation"]["status"] in {"OPEN", "CLOSED"}


def test_sbom_includes_git_commit_metadata():
    from pathlib import Path

    from scripts.generate_sbom import _parse_lock, build_sbom

    lock = Path("requirements.lock.txt")
    if not lock.is_file():
        pytest.skip("no lockfile")
    sha = __import__("hashlib").sha256(lock.read_bytes()).hexdigest()
    comps = _parse_lock(lock)
    bom = build_sbom(comps, lock_sha=sha)
    names = {p["name"] for p in bom["metadata"]["properties"]}
    assert "blackdark:git_commit" in names or "blackdark:release" in names
