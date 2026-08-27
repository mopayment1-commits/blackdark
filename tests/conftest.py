"""Shared pytest fixtures — institutional CI bootstrap."""

from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_database_schema():
    """Ensure SQLite schema exists before HTTP/API tests in CI (fresh runners)."""
    import database

    asyncio.run(database.init_db())
