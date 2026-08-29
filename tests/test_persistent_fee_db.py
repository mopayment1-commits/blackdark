"""Persistent fee DB — SQLite durability + oracle fail-closed gate."""

from __future__ import annotations

import sqlite3

import pytest

import config
import database
import fee_matrix
from oracle_unified import finalize_unified_score


@pytest.fixture
async def isolated_fee_db(tmp_path, monkeypatch):
    """Fresh SQLite file per test (simulates durable storage)."""
    db_path = tmp_path / "fees.db"
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", db_path)
    fee_matrix._matrix.clear()
    await database.init_db()
    yield db_path
    fee_matrix._matrix.clear()


@pytest.mark.asyncio
async def test_fees_table_created_by_migration(isolated_fee_db):
    conn = sqlite3.connect(str(isolated_fee_db))
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "fees" in tables
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert "idx_fees_opp_exchange_symbol" in indexes
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_calculate_opportunity_fees_writes_row(isolated_fee_db):
    record = await fee_matrix.calculate_opportunity_fees(
        "opp-1",
        "binance",
        "BTC/USDT",
        "buy",
        500.0,
        gross_profit_usdt=12.5,
    )
    assert record is not None
    assert record["opportunity_id"] == "opp-1"
    assert record["total_fee_usdt"] > 0
    assert record["net_profit_usdt"] == pytest.approx(12.5 - record["total_fee_usdt"])

    fetched = await database.fetch_fee_record("opp-1", "binance", "BTC/USDT")
    assert fetched is not None
    assert fetched["trading_fee_usdt"] == pytest.approx(record["trading_fee_usdt"])
    assert fetched["total_fee_usdt"] == pytest.approx(record["total_fee_usdt"])


@pytest.mark.asyncio
async def test_fees_survive_app_restart(isolated_fee_db):
    await fee_matrix.calculate_opportunity_fees(
        "restart-opp",
        "okx",
        "ETH/USDT",
        "sell",
        250.0,
        gross_profit_usdt=3.0,
    )

    # Simulate restart: drop in-memory fee matrix cache and re-open DB.
    fee_matrix._matrix.clear()

    conn = sqlite3.connect(str(isolated_fee_db))
    try:
        row = conn.execute(
            """
            SELECT opportunity_id, exchange, symbol, side, total_fee_usdt, net_profit_usdt
            FROM fees
            WHERE opportunity_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            ("restart-opp",),
        ).fetchone()
        assert row is not None
        assert row[0] == "restart-opp"
        assert row[1] == "okx"
        assert row[2] == "ETH/USDT"
        assert row[3] == "sell"
        assert row[4] > 0
    finally:
        conn.close()

    await database.init_db()
    persisted = await database.fetch_fee_record("restart-opp", "okx", "ETH/USDT")
    assert persisted is not None
    assert persisted["net_profit_usdt"] is not None


@pytest.mark.asyncio
async def test_oracle_unified_blocks_without_fee_record(isolated_fee_db):
    breakdown = {"market_regime": "neutral", "dimension_weights": {}}
    blocked = await finalize_unified_score(
        72.0,
        "BTC",
        breakdown,
        opportunity_id="missing-opp",
        exchange="binance",
        symbol="BTC/USDT",
        side="buy",
    )
    assert blocked["blocked"] is True
    assert blocked["fee_gate"]["reason"] == "fee_record_missing"
    assert blocked["opportunity_score"] == 0
    assert blocked["internal_verdict"] == "blocked"


@pytest.mark.asyncio
async def test_oracle_unified_allows_with_fee_record(isolated_fee_db):
    await fee_matrix.calculate_opportunity_fees(
        "allowed-opp",
        "binance",
        "BTC/USDT",
        "buy",
        400.0,
        gross_profit_usdt=5.0,
    )
    breakdown = {"market_regime": "neutral", "dimension_weights": {}}
    result = await finalize_unified_score(
        72.0,
        "BTC",
        breakdown,
        include_ml=False,
        opportunity_id="allowed-opp",
        exchange="binance",
        symbol="BTC/USDT",
        side="buy",
    )
    assert result.get("blocked") is not True
    assert result["fee_record"] is not None
    assert result["net_profit_usdt"] is not None
    assert result["opportunity_score"] > 0


@pytest.mark.asyncio
async def test_calculate_opportunity_fees_fail_closed_unknown_venue(isolated_fee_db):
    record = await fee_matrix.calculate_opportunity_fees(
        "bad-opp",
        "unknown_venue_xyz",
        "BTC/USDT",
        "buy",
        100.0,
    )
    assert record is None
    assert await database.fetch_fee_record("bad-opp", "unknown_venue_xyz", "BTC/USDT") is None
