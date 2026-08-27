"""Tests — CoinGecko primary ingestion connector (#34)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.coingecko_connector import (
    coingecko_connector_status,
    coingecko_id_for,
    fetch_coingecko_price,
    run_coingecko_primary_ingest,
)


def test_coingecko_id_for_btc():
    assert coingecko_id_for("BTC") == "bitcoin"
    assert coingecko_id_for("MATIC") == "matic-network" or coingecko_id_for("POL")


def test_connector_status():
    st = coingecko_connector_status()
    assert st["role"] == "primary_data_ingestion_source"
    assert "coingecko_api" in st["fallback_chain"][0]


@pytest.mark.asyncio
async def test_fetch_price_mock():
    fake = {
        "ok": True,
        "data": {"bitcoin": {"usd": 65000, "usd_24h_change": 2.5}},
        "latency_ms": 50,
    }

    with patch(
        "blackdark.ingestion.coingecko_connector._request",
        new=AsyncMock(return_value=fake),
    ):
        row = await fetch_coingecko_price("BTC")
    assert row["ok"] is True
    assert row["symbol"] == "BTC"
    assert row["canonical_id"] == "bd:BTC"
    assert row["price_usd"] == 65000


@pytest.mark.asyncio
async def test_fetch_price_kraken_fallback():
    with patch(
        "blackdark.ingestion.coingecko_connector._request",
        new=AsyncMock(return_value={"ok": False, "error": "rate_limited"}),
    ), patch(
        "blackdark.ingestion.coingecko_connector._kraken_fallback_price",
        new=AsyncMock(return_value={"price_usd": 64000, "change_24h_pct": 0, "source": "kraken_fallback"}),
    ):
        row = await fetch_coingecko_price("BTC")
    assert row["ok"] is True
    assert row["fallback"] is True
    assert row["source"] == "kraken_fallback"


@pytest.mark.asyncio
async def test_primary_ingest_mock(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "cg.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    await database.init_db()

    markets = {
        "ok": True,
        "count": 2,
        "markets": [
            {"symbol": "BTC", "canonical_id": "bd:BTC", "price_usd": 1},
            {"symbol": "ETH", "canonical_id": "bd:ETH", "price_usd": 2},
        ],
    }
    with patch(
        "blackdark.ingestion.coingecko_connector.fetch_coingecko_markets",
        new=AsyncMock(return_value=markets),
    ), patch(
        "blackdark.ingestion.coingecko_connector.fetch_coingecko_trending",
        new=AsyncMock(return_value={"ok": True, "coins": []}),
    ), patch(
        "blackdark.ingestion.coingecko_connector.fetch_coingecko_global",
        new=AsyncMock(return_value={"ok": True, "global": {}}),
    ), patch(
        "blackdark.ingestion.coingecko_connector.fetch_coingecko_price",
        new=AsyncMock(return_value={"ok": True, "symbol": "BTC", "price_usd": 1}),
    ):
        out = await run_coingecko_primary_ingest()
    assert out["ok"] is True
    assert out["markets"] == 2


def test_coingecko_api(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "cg_api.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    fake_price = {
        "ok": True,
        "symbol": "ETH",
        "canonical_id": "bd:ETH",
        "price_usd": 3000,
        "sla_met": True,
    }
    with patch(
        "blackdark.ingestion.coingecko_connector.fetch_coingecko_price",
        new=AsyncMock(return_value=fake_price),
    ):
        from fastapi.testclient import TestClient
        from dashboard import app

        c = TestClient(app)
        assert c.get("/api/platform/ingestion/coingecko/status").status_code == 200
        r = c.get("/api/platform/ingestion/coingecko/price?asset=ETH")
        assert r.status_code == 200
        assert r.json()["canonical_id"] == "bd:ETH"
