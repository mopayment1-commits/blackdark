"""Tests for PostgreSQL DSN resolution fallbacks."""

from __future__ import annotations

import database_url_resolver as resolver


def test_candidate_database_urls_priority(monkeypatch):
    monkeypatch.setenv("DATABASE_PUBLIC_URL", "postgresql://public:5432/db")
    monkeypatch.setenv("DATABASE_URL", "postgresql://primary:5432/db")
    pairs = resolver.candidate_database_urls()
    assert pairs[0] == ("DATABASE_URL", "postgresql://primary:5432/db")
    assert ("DATABASE_PUBLIC_URL", "postgresql://public:5432/db") in pairs


def test_normalize_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/railway")
    pairs = resolver.candidate_database_urls()
    assert pairs[0][1].startswith("postgresql://")


def test_resolve_prefers_resolvable_host(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://bad-host:5432/db")
    monkeypatch.setenv("DATABASE_PUBLIC_URL", "postgresql://good-host:5432/db")

    def fake_resolves(host, *, timeout=2.0):
        return host == "good-host"

    monkeypatch.setattr(resolver, "host_resolves", fake_resolves)
    url, meta = resolver.resolve_database_url()
    assert url == "postgresql://good-host:5432/db"
    assert meta["selected_env"] == "DATABASE_PUBLIC_URL"
