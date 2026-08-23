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
