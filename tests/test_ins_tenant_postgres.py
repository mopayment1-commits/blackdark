"""INS-TENANT Postgres production closure tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def pg_url():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url.startswith(("postgres://", "postgresql://")):
        url = os.getenv(
            "INS_TENANT_TEST_DATABASE_URL",
            "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark",
        )
    return url


@pytest.mark.asyncio
async def test_ins_tenant_postgres_provision_and_smoke(monkeypatch, pg_url):
    monkeypatch.setenv("DATABASE_URL", pg_url)
    import config

    monkeypatch.setattr(config, "DATABASE_URL", pg_url, raising=False)

    from postgres_backend import close_pool

    await close_pool()

    from scripts.provision_ins_tenant_postgres import provision

    result = await provision(migrate_json=True)
    assert result["ins_tenant_ready"] is True
    assert result["smoke"]["smoke_pass"] is True
    assert result["status"]["storage_engine"] == "postgresql"

    from rvm.verify import verify_institutional_gate

    gate = await verify_institutional_gate("INS-TENANT")
    assert gate["status"] == "PASS"
    assert "postgresql_production_path" in gate["evidence"]

    await close_pool()
