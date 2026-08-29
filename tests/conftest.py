"""Shared pytest fixtures — institutional CI bootstrap."""

from __future__ import annotations

import asyncio
import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_test_secrets():
    """Ensure vault key is always set in tests (no silent dev fallback)."""
    os.environ.setdefault("SECRETS_MASTER_KEY", "pytest-session-vault-key-not-for-production-use")
    os.environ.setdefault("SESSION_TOKEN_PEPPER", "pytest-session-pepper-not-for-production")
    yield


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_database_schema():
    """Ensure SQLite schema exists before HTTP/API tests in CI (fresh runners)."""
    import database

    asyncio.run(database.init_db())
