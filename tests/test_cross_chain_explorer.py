"""Tests — cross-chain explorer (#101), Tronscan (#103), transaction decoder (#100)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.transaction_decoder import _decode_input, decode_transaction
from bd_platform.transaction_index import (
    append_transactions,
    decode_cursor,
    encode_cursor,
    query_index,
)
from blackdark.canonical.cross_chain_schema import normalize_evm_tx, normalize_tron_tx


def test_normalize_evm_tx():
    row = {
        "hash": "0xabc",
        "from": "0xfrom",
        "to": "0xto",
        "value": "1000000000000000000",
        "timeStamp": "1700000000",
        "blockNumber": "123",
        "isError": "0",
    }
    norm = normalize_evm_tx(row, chain="ethereum", chain_id=1, source="test")
    assert norm is not None
    assert norm.tx_hash == "0xabc"
    assert norm.value_native == 1.0


def test_normalize_tron_tx():
    row = {"hash": "tx1", "ownerAddress": "TAddr", "toAddress": "TTo", "timestamp": 1700000000000}
    norm = normalize_tron_tx(row, source="tronscan")
    assert norm is not None
    assert norm.chain == "tron"


def test_index_pagination_high_volume(tmp_path):
    """Pagination correctness on large index (100k rows)."""
    path = tmp_path / "big_index.jsonl"
    rows = [
        {
            "tx_hash": f"0x{i:064x}",
            "chain": "ethereum" if i % 2 == 0 else "bsc",
            "timestamp": 1_700_000_000 - i,
            "from_address": "0xfrom",
            "to_address": "0xto",
        }
        for i in range(100_000)
    ]
    append_transactions(rows, path=path)

    page1 = query_index(address="0xfrom", limit=100, path=path)
    assert page1["count"] == 100
    assert page1["has_more"] is True
    cursor = page1["next_cursor"]
    assert cursor

    page2 = query_index(address="0xfrom", limit=100, cursor=cursor, path=path)
    assert page2["count"] == 100
    assert page2["results"][0]["tx_hash"] != page1["results"][0]["tx_hash"]

    # No overlap between pages
    h1 = {r["tx_hash"] for r in page1["results"]}
    h2 = {r["tx_hash"] for r in page2["results"]}
    assert h1.isdisjoint(h2)

    cur = decode_cursor(cursor)
    assert cur and "timestamp" in cur


def test_cursor_roundtrip():
    c = encode_cursor(1700, "ethereum", "0xabc")
    d = decode_cursor(c)
    assert d["chain"] == "ethereum"
    assert d["tx_hash"] == "0xabc"


def test_decode_input_known_selector():
    out = _decode_input("0xa9059cbb000000000000000000000000")
    assert out["known"] is True
    assert out["action"] == "transfer"
    assert out["intent_inferred"] is False


def test_decode_input_unknown_marked():
    out = _decode_input("0xdeadbeef")
    assert out["known"] is False
    assert out["unknown_marked"] is True
    assert out["intent_inferred"] is False


@pytest.mark.asyncio
async def test_transaction_decoder_uniswap_mint_explanation():
    fake_tx = {
        "from": "0xuser",
        "to": "0xpool",
        "input": "0x8831645600000000000000000000000000000000000000000000000000000000000000",
        "value": "0x0",
    }
    fake_receipt = {"logs": []}
    with patch(
        "bd_platform.transaction_decoder._fetch_tx_and_receipt",
        new=AsyncMock(return_value={"ok": True, "transaction": fake_tx, "receipt": fake_receipt}),
    ):
        out = await decode_transaction(tx_hash="0x" + "a" * 62, chain="ethereum")
    assert out["ok"] is True
    assert out["intent_inferred"] is False
    assert "liquidity provision" in out["explanation"].lower()
    assert "impermanent loss" in out["explanation"].lower()


@pytest.mark.asyncio
async def test_tronscan_fallback_mock():
    with patch(
        "blackdark.ingestion.tronscan_connector._CONNECTOR.get_json",
        new=AsyncMock(return_value={"ok": False, "error": "rate_limited"}),
    ), patch(
        "blackdark.ingestion.tronscan_connector._fallback_account",
        new=AsyncMock(return_value={"ok": True, "balance_trx": 100.0, "source": "trongrid_fallback"}),
    ):
        from blackdark.ingestion.tronscan_connector import fetch_tron_account

        out = await fetch_tron_account("TTestAddress123456789012345678901234")
    assert out["ok"] is True
    assert out["fallback"] is True
    assert out["data_state"] == "DEGRADED"


@pytest.mark.asyncio
async def test_unified_explorer_mock():
    with patch(
        "bd_platform.cross_chain_explorer._fetch_chain_assets",
        new=AsyncMock(return_value={"ok": True, "assets": [{"chain": "ethereum", "symbol": "ETH"}]}),
    ), patch(
        "bd_platform.cross_chain_explorer._fetch_evm_scan_txs",
        new=AsyncMock(return_value=[{"tx_hash": "0x1", "chain": "ethereum", "timestamp": 1700, "from_address": "0xa", "to_address": "0xb"}]),
    ), patch(
        "bd_platform.cross_chain_explorer._detect_address_chains",
        return_value=["ethereum"],
    ):
        from bd_platform.cross_chain_explorer import unified_address_explorer

        out = await unified_address_explorer("0x" + "a" * 40)
    assert out["ok"] is True
    assert out["feature"] == "#101"
    assert "ethereum" in out["chains_queried"]
