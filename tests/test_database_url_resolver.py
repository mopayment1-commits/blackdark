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


def test_blackdark_test_database_url_candidate(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "BLACKDARK_TEST_DATABASE_URL",
        "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
    )
    pairs = resolver.candidate_database_urls()
    assert pairs[0][0] == "BLACKDARK_TEST_DATABASE_URL"


def test_railway_internal_host_canonicalized(monkeypatch):
    url = resolver._canonicalize_railway_internal_host(
        "postgresql://user:pass@MYDB.railway.internal:5432/railway"
    )
    assert "@mydb.railway.internal:5432/" in url


def test_resolve_skips_unresolved_railway_internal_for_public(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@postgres.railway.internal:5432/railway")
    monkeypatch.setenv("DATABASE_PUBLIC_URL", "postgresql://u:p@public.proxy.rlwy.net:12345/railway")

    def fake_resolves(host, *, timeout=2.0):
        return host == "public.proxy.rlwy.net"

    monkeypatch.setattr(resolver, "host_resolves", fake_resolves)
    url, meta = resolver.resolve_database_url()
    assert url.startswith("postgresql://u:p@public.proxy.rlwy.net:12345/railway")
    assert "sslmode=require" in url
    assert meta["selected_env"] == "DATABASE_PUBLIC_URL"
    assert meta["selection"] == "railway_public_over_unresolved_internal"


def test_railway_internal_host_does_not_require_ssl():
    internal = "postgresql://u:p@postgres.railway.internal:5432/railway"
    assert resolver.railway_postgres_requires_ssl(internal) is False
    assert resolver.ensure_postgres_ssl_params(internal) == internal


def test_railway_public_proxy_requires_ssl():
    public = "postgresql://u:p@public.proxy.rlwy.net:12345/railway"
    assert resolver.railway_postgres_requires_ssl(public) is True
    dsn, kwargs = resolver.prepare_asyncpg_dsn(public)
    assert "sslmode=require" in dsn
    assert kwargs.get("statement_cache_size") == 0


def test_resolve_prefers_resolvable_host(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://bad-host:5432/db")
    monkeypatch.setenv("DATABASE_PUBLIC_URL", "postgresql://good-host:5432/db")

    def fake_resolves(host, *, timeout=2.0):
        return host == "good-host"

    monkeypatch.setattr(resolver, "host_resolves", fake_resolves)
    url, meta = resolver.resolve_database_url()
    assert url == "postgresql://good-host:5432/db"
    assert meta["selected_env"] == "DATABASE_PUBLIC_URL"
