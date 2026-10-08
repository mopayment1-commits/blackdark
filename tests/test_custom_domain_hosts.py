"""Custom domain must be accepted when traffic reaches the app (TrustedHost + CORS)."""

from __future__ import annotations

import security_middleware as sm


def test_public_canonical_hosts_in_allowed_hosts(monkeypatch):
    monkeypatch.setenv("PUBLIC_CANONICAL_HOSTS", "blackdark.io,www.blackdark.io")
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    hosts = sm._allowed_hosts()
    assert "blackdark.io" in hosts
    assert "www.blackdark.io" in hosts


def test_cors_includes_canonical_https_origins(monkeypatch):
    monkeypatch.setenv("PUBLIC_CANONICAL_HOSTS", "blackdark.io,www.blackdark.io")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    origins = sm._cors_origins()
    assert "https://blackdark.io" in origins
    assert "https://www.blackdark.io" in origins
