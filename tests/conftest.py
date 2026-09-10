"""Shared pytest fixtures — institutional CI bootstrap."""

from __future__ import annotations

import asyncio
import hashlib
import os
from collections.abc import AsyncIterator
from pathlib import Path

# Full-suite HTTP matrices (cap646/batch11/FDS) exceed default viral API RL (120/min).
os.environ.setdefault("VIRAL_API_RL_PER_MIN", "100000")
os.environ.setdefault("VIRAL_ORACLE_RL_PER_MIN", "100000")
os.environ.setdefault("VIRAL_WEB_RL_PER_MIN", "100000")
os.environ.setdefault("ANONYMOUS_PUBLIC_RL_EXEMPT", "true")

import aiohttp
import pytest


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_httpx2_for_testclient():
    """Starlette TestClient requires httpx2; keep production on httpx."""
    try:
        import httpx2  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "httpx2 is required for institutional pytest/TestClient paths"
        ) from exc
    yield


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_test_secrets():
    """Ensure vault key is always set in tests (no silent dev fallback)."""
    os.environ.setdefault("SECRETS_MASTER_KEY", "pytest-session-vault-key-not-for-production-use")
    os.environ.setdefault("SESSION_TOKEN_PEPPER", "pytest-session-pepper-not-for-production")
    yield


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_signed_capacity():
    """Publish staging signed capacity so CAP-644 stays in external registry during tests."""
    from institutional_assurance import get_signed_capacity, publish_signed_capacity, verify_signed_capacity

    cap = get_signed_capacity()
    if not cap or str(cap.get("environment") or "").lower() == "production" or not verify_signed_capacity(cap):
        publish_signed_capacity(
            environment="staging",
            workers=2,
            postgres=True,
            redis=True,
            requests=80,
            p50_ms=131.3,
            p95_ms=143.4,
            p99_ms=167.5,
            error_rate=0.0,
            operator="pytest-institutional-gate",
            notes="SIGNED: pytest bootstrap — staging keeps CAP-644 registry slot deterministic",
        )
    yield


_CANONICAL_GUARD_PATHS: tuple[Path, ...] = (Path("data/oracle_audit_chain.jsonl"),)


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def _isolate_canonical_mutable_data(tmp_path_factory):
    """Redirect append-only ledgers to ephemeral paths — never mutate repo data/."""
    import oracle_audit_chain as chain

    root = tmp_path_factory.mktemp("canonical_isolation")
    chain_path = root / "oracle_audit_chain.jsonl"
    chain.CHAIN_PATH = chain_path
    os.environ["ORACLE_AUDIT_CHAIN_PATH"] = str(chain_path)
    yield


@pytest.fixture(scope="session", autouse=True)
def _guard_canonical_data_unchanged_by_tests():
    """Fail the session if tests mutate canonical production-like data files."""
    before = {p: _sha256_file(p) for p in _CANONICAL_GUARD_PATHS}
    yield
    after = {p: _sha256_file(p) for p in _CANONICAL_GUARD_PATHS}
    changed = [str(p) for p in _CANONICAL_GUARD_PATHS if before.get(p) != after.get(p)]
    if changed:
        raise AssertionError(
            "Canonical data mutated during pytest session: "
            + ", ".join(changed)
            + ". Use tmp_path/monkeypatch for ledger writes."
        )


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_database_schema():
    """Ensure SQLite schema exists before HTTP/API tests in CI (fresh runners)."""
    import database

    asyncio.run(database.init_db())


@pytest.fixture
async def aiohttp_client_session() -> AsyncIterator[aiohttp.ClientSession]:
    """Yield a dedicated aiohttp session; always close session + connector on teardown."""
    connector = aiohttp.TCPConnector()
    session = aiohttp.ClientSession(connector=connector)
    try:
        yield session
    finally:
        if not session.closed:
            await session.close()
        if not connector.closed:
            await connector.close()


@pytest.fixture(autouse=True)
async def _teardown_shared_aiohttp_session():
    """Close aggregator shared sessions after each test to avoid loop-bound leaks."""
    yield
    try:
        from aggregator import close_shared_http_session

        await close_shared_http_session()
    except Exception:
        pass
