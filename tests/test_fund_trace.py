"""Tests — fund trace (#18) single-chain path finding."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.fund_trace import _build_adjacency, trace_funds


def test_build_adjacency_marks_bridge():
    txs = [
        {
            "hash": "0xabc",
            "from": "0xuser",
            "to": "0x8315177ab297ba92a06054bd893aff76f9bee014",
            "value_eth": 1.5,
            "block_number": 100,
            "timestamp": 1,
            "is_error": False,
        }
    ]
    graph = _build_adjacency(txs, "0xuser")
    edge = graph["0xuser"][0]
    assert edge["hop_type"] == "bridge_exit"
    assert edge["bridge"] == "arbitrum_inbox"


@pytest.mark.asyncio
async def test_trace_funds_mock():
    fake_txs = {
        "ok": True,
        "transactions": [
            {
                "hash": "0x1",
                "from": "0xuser",
                "to": "0xpeer",
                "value_eth": 2.0,
                "block_number": 10,
                "timestamp": 100,
                "is_error": False,
            },
            {
                "hash": "0x2",
                "from": "0xpeer",
                "to": "0xdest",
                "value_eth": 1.8,
                "block_number": 11,
                "timestamp": 101,
                "is_error": False,
            },
        ],
    }
    with patch(
        "bd_platform.onchain_client.get_normal_transactions",
        new=AsyncMock(return_value=fake_txs),
    ):
        out = await trace_funds("0xuser", chain="ethereum", max_hops=3)
    assert out["ok"] is True
    assert out["fabricated"] is False
    assert out["bridge_handling"] == "explicit"
    assert out["path_count"] >= 1
    assert out["paths"][0]["hop_count"] >= 1


@pytest.mark.asyncio
async def test_trace_rejects_non_ethereum():
    out = await trace_funds("0xuser", chain="polygon")
    assert out["ok"] is False
    assert out["error"] == "single_chain_ethereum_only"
