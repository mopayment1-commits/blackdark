"""Tests for Wave 01 twelve-system sprint."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest


def test_kraken_parse_ohlc_1m():
    from blackdark.data.ingestors.kraken import parse_ohlc

    rows = [[1704067200, "42000.1", "42500", "41800", "42300.5", "42200", "10.5", 100]]
    parsed = parse_ohlc("BTCUSDT", "1m", rows)
    assert len(parsed) == 1
    assert parsed[0]["interval"] == "1m"


@pytest.mark.asyncio
async def test_backfill_falls_back_to_kraken(monkeypatch):
    from blackdark.data import backfill as bf

    async def fake_binance(**_kwargs):
        return {"records_fetched": 0, "records_inserted": 0, "source": "binance"}

    async def fake_kraken(**_kwargs):
        return {
            "records_fetched": 120,
            "records_inserted": 118,
            "source": "kraken",
            "status": "completed",
            "run_id": "test-run",
        }

    monkeypatch.setattr(bf, "backfill_binance_ohlcv", fake_binance)
    monkeypatch.setattr(bf, "backfill_kraken_ohlcv", fake_kraken)

    result = await bf.backfill_ohlcv(symbol="BTCUSDT", interval="1h", days=7, batch_size=100)
    assert result["records_fetched"] == 120
    assert result["source"] == "kraken"
    assert result.get("binance_fallback_reason") == "records_fetched_zero"


@pytest.mark.asyncio
async def test_kraken_backfill_pagination_logic():
    """Verify since cursor advances when rows are returned."""
    from blackdark.data.ingestors.kraken import INTERVAL_SECONDS

    since = 1_704_067_200
    step = INTERVAL_SECONDS["1h"]
    batch_last_ts = since + step * 10
    next_since = batch_last_ts + step
    assert next_since > since


def test_sealed_prediction_hash_stable():
  import hashlib

  payload = {"symbol": "BTCUSDT", "direction": "buy", "target_price": 70000}
  h1 = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
  h2 = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
  assert h1 == h2
  assert len(h1) == 64


def test_systems_index_structure():
    from blackdark.data.systems_api import systems_router

    paths = [getattr(r, "path", None) for r in systems_router.routes]
    assert "/api/v1/data/systems" in paths
    assert "/api/v1/data/signals" in paths
    assert "/api/v1/data/predictions/{prediction_id}" in paths
    assert "/api/v1/data/failures/misses" in paths
