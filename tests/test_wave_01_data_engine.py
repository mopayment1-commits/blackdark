"""Wave 01 data engine unit tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


def test_parse_binance_klines():
    from blackdark.data.ingestors.binance import parse_klines

    rows = [
        [
            1704067200000,
            "42000.1",
            "42500",
            "41800",
            "42300.5",
            "100.5",
            1704070799999,
            "4200000",
            1200,
            "50.2",
            "2100000",
        ]
    ]
    parsed = parse_klines("BTCUSDT", "1h", rows)
    assert len(parsed) == 1
    assert parsed[0]["symbol"] == "BTCUSDT"
    assert parsed[0]["quote_asset"] == "USDT"
    assert parsed[0]["close"] == Decimal("42300.5")


def test_parse_funding():
    from blackdark.data.ingestors.binance import parse_funding

    rows = [{"symbol": "BTCUSDT", "fundingTime": 1704067200000, "fundingRate": "0.0001"}]
    parsed = parse_funding("BTCUSDT", rows)
    assert parsed[0]["symbol"] == "BTCUSDT"
    assert parsed[0]["funding_rate"] == Decimal("0.0001")


def test_data_api_requires_postgres(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import config
    import database

    db_path = tmp_path / "w1.db"
    monkeypatch.setattr(config, "DATABASE_URL", "")
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.setenv("ENV", "test")

    import asyncio

    asyncio.run(database.init_db())

    from dashboard import app

    client = TestClient(app)
    resp = client.get("/api/v1/data/status")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_count_ohlcv_rows():
    from unittest.mock import AsyncMock, MagicMock

    from blackdark.data.repository import count_ohlcv_rows

    session = AsyncMock()
    result = MagicMock()
    result.mappings.return_value.fetchone.return_value = {"n": 42}
    session.execute = AsyncMock(return_value=result)
    assert await count_ohlcv_rows(session) == 42


@pytest.mark.asyncio
async def test_ensure_data_engine_ready_skips_bootstrap_when_rows_exist(monkeypatch):
    from blackdark.data import db as db_mod

    monkeypatch.setattr(db_mod, "_schema_ready", True)
    monkeypatch.setattr(db_mod, "_bootstrapped", False)
    monkeypatch.setenv("DATA_ENGINE_BOOTSTRAP_INGEST", "true")

    seed_called = False
    bootstrap_called = False

    async def fake_seed(session):
        nonlocal seed_called
        seed_called = True
        return {"seeded": 2}

    async def fake_count(session):
        return 100

    async def fake_bootstrap():
        nonlocal bootstrap_called
        bootstrap_called = True

    class _SessionCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(db_mod, "get_session", lambda: _SessionCtx())
    monkeypatch.setattr("blackdark.data.repository.seed_data_sources", fake_seed)
    monkeypatch.setattr("blackdark.data.repository.count_ohlcv_rows", fake_count)
    monkeypatch.setattr("blackdark.data.jobs.run_bootstrap_ingest_once", fake_bootstrap)

    await db_mod.ensure_data_engine_ready()
    assert seed_called
    assert not bootstrap_called
    assert db_mod._bootstrapped is True

