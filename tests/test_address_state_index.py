"""Tests — address state index point-in-time semantics (#10, #19)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.address_state_index import (
    _snapshot_at_or_before,
    query_balance_at,
)


def test_snapshot_at_or_before():
    as_of = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    snaps = [
        {"timestamp": "2026-08-20T12:00:00+00:00", "total_usd": 90_000},
        {"timestamp": "2026-08-23T12:00:00+00:00", "total_usd": 95_000},
        {"timestamp": "2026-08-25T12:00:00+00:00", "total_usd": 100_000},
    ]
    row = _snapshot_at_or_before(snaps, as_of)
    assert row is not None
    assert row["total_usd"] == 95_000


@pytest.mark.asyncio
async def test_query_balance_at_etherscan_mock(monkeypatch, tmp_path):
    snap = tmp_path / "snapshots.jsonl"
    monkeypatch.setattr("bd_platform.address_state_index._SNAPSHOT_PATH", snap)
    monkeypatch.setattr("bd_platform.address_intelligence._SNAPSHOT_PATH", snap)

    as_of = datetime(2026, 8, 20, tzinfo=UTC)
    with patch(
        "bd_platform.onchain_client.get_block_by_time",
        new=AsyncMock(return_value={"ok": True, "block_number": 18_000_000}),
    ), patch(
        "bd_platform.onchain_client.get_eth_balance",
        new=AsyncMock(return_value={"ok": True, "balance_eth": 42.5, "block_tag": "18000000"}),
    ):
        out = await query_balance_at(
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            chain="ethereum",
            as_of=as_of,
        )
    assert out["ok"] is True
    assert out["semantics"] == "point_in_time"
    assert out["balance_eth"] == 42.5
    assert out["anchor"]["type"] == "block"
    assert out["proxy"] is False


@pytest.mark.asyncio
async def test_query_balance_at_snapshot_fallback(monkeypatch, tmp_path):
    snap = tmp_path / "snapshots.jsonl"
    key = "ethereum:0xabc"
    snap.write_text(
        json.dumps(
            {
                "key": key,
                "address": "0xabc",
                "chain": "ethereum",
                "total_usd": 50_000,
                "block_number": 17_000_000,
                "source": "test",
                "timestamp": "2026-08-22T12:00:00+00:00",
            }
        )
        + "\n"
    )
    monkeypatch.setattr("bd_platform.address_state_index._SNAPSHOT_PATH", snap)

    with patch(
        "bd_platform.onchain_client.get_block_by_time",
        new=AsyncMock(return_value={"ok": False, "error": "no_key"}),
    ):
        out = await query_balance_at(
            "0xabc",
            chain="ethereum",
            as_of=datetime(2026, 8, 23, tzinfo=UTC),
        )
    assert out["ok"] is True
    assert out["semantics"] == "point_in_time"
    assert out["total_usd"] == 50_000
    assert out["anchor"]["type"] == "snapshot"
