"""Tests — silent data layer batch 2 (#54, #59, #66, #68)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.exchange_netflow_intelligence import (
    _reconcile,
    compute_exchange_netflow,
)
from blackdark.ingestion.futures_cvd_metric import _classify_taker_qa, compute_futures_cvd
from blackdark.ingestion.historical_flat_archive import (
    backtest_coverage_years,
    load_manifest,
    verify_manifest,
    write_partition,
)
from blackdark.ingestion.investing_com_connector import _ai_context_line, _parse_rss


def test_netflow_formula_reconciliation():
    r = _reconcile(1_000_000, 400_000, 600_000)
    assert r["ok"] is True
    assert r["formula"] == "netflow = inflow - outflow"


def test_netflow_reconciliation_missing():
    r = _reconcile(None, 100, 50)
    assert r["ok"] is False


def test_taker_qa_valid():
    qa = _classify_taker_qa(volume=100, taker_buy=60)
    assert qa["classification_valid"] is True
    assert qa["taker_buy_ratio"] == 0.6


def test_taker_qa_invalid():
    qa = _classify_taker_qa(volume=100, taker_buy=110)
    assert qa["classification_valid"] is False
    assert "taker_buy_exceeds_volume" in qa["issues"]


@pytest.mark.asyncio
async def test_exchange_netflow_mock(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "blackdark.ingestion.exchange_netflow_intelligence._HISTORY_PATH",
        tmp_path / "hist.jsonl",
    )
    with patch(
        "blackdark.ingestion.exchange_flow_metric.compute_token_exchange_flows",
        new=AsyncMock(
            return_value={
                "ok": True,
                "inflow_usd": 2_000_000,
                "outflow_usd": 500_000,
                "net_flow_usd": 1_500_000,
                "risk_score_delta": 3,
                "sla_met": True,
                "latency_ms": 20,
            }
        ),
    ):
        out = await compute_exchange_netflow("ETH")
    assert out["ok"] is True
    assert out["formula"] == "netflow = inflow - outflow"
    assert out["netflow_usd"] == 1_500_000
    assert out["reconciliation"]["ok"] is True
    assert out["missing_not_zero"] is True


@pytest.mark.asyncio
async def test_futures_cvd_mock():
    fake_klines = [
        [1, "0", "0", "0", "0", "100", 0, "0", 10, "60", "0", "0"],
        [2, "0", "0", "0", "0", "200", 0, "0", 10, "80", "0", "0"],
    ]
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=fake_klines)
        mock_get.return_value.__aenter__.return_value = mock_resp
        out = await compute_futures_cvd("BTC", limit=2)
    assert out["ok"] is True
    assert out["cvd"] is not None
    assert out["trade_side_qa"]["classification_valid"] is True


def test_flat_archive_manifest_and_checksum(tmp_path, monkeypatch):
    monkeypatch.setattr("blackdark.ingestion.historical_flat_archive.ARCHIVE_ROOT", tmp_path)
    monkeypatch.setattr(
        "blackdark.ingestion.historical_flat_archive.MANIFEST_PATH", tmp_path / "manifest.json"
    )
    entry = write_partition(
        dataset="ohlcv",
        symbol="BTC",
        interval="1d",
        date="2026-08-24",
        rows=[{"close": 60000, "volume": 100}],
    )
    assert entry["sha256"]
    manifest = load_manifest()
    assert manifest["file_count"] == 1
    verified = verify_manifest()
    assert verified["ok"] is True
    cov = backtest_coverage_years(symbol="BTC", interval="1d")
    assert cov["partition_count"] == 1


def test_investing_rss_high_impact():
    xml = """<?xml version="1.0"?><rss><channel>
    <item><title>Bitcoin ETF approval drives market surge</title>
    <description>SEC approves new product</description></item>
    </channel></rss>"""
    rows = _parse_rss(xml)
    assert rows[0]["high_impact"] is True
    line = _ai_context_line(rows, scanned_estimate=1200)
    assert line is not None
    assert "1,200" in line
    assert "high-impact" in line
