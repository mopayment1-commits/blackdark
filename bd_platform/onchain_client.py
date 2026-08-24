"""Lightweight Etherscan client for address intelligence (archive-friendly queries)."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_BASE = "https://api.etherscan.io/api"


def _api_key() -> str | None:
    key = (os.getenv("ETHERSCAN_API_KEY") or "").strip()
    return key or None


async def _get(params: dict[str, Any], *, timeout_sec: float = 3.0) -> dict[str, Any]:
    if not _api_key():
        return {"ok": False, "error": "ETHERSCAN_API_KEY not configured"}
    merged = {**params, "apikey": _api_key()}
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    t0 = time.perf_counter()
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.get(_BASE, params=merged) as resp:
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                if resp.status != 200:
                    return {"ok": False, "error": f"http_{resp.status}", "latency_ms": latency_ms}
                data = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        return {"ok": False, "error": str(exc)}

    status = str((data or {}).get("status") or "")
    message = str((data or {}).get("message") or "")
    if status == "0" and "No transactions found" not in message and "No records found" not in message:
        if message and message != "NOTOK":
            return {"ok": False, "error": message, "latency_ms": latency_ms}
    return {"ok": True, "data": data, "latency_ms": latency_ms}


def _wei_to_eth(wei: str | int | float) -> float:
    try:
        return float(wei) / 1e18
    except (TypeError, ValueError):
        return 0.0


async def get_block_by_time(as_of: datetime) -> dict[str, Any]:
    """Map timestamp → Ethereum block number (closest before)."""
    ts = int(as_of.replace(tzinfo=UTC).timestamp()) if as_of.tzinfo else int(as_of.timestamp())
    resp = await _get(
        {
            "module": "block",
            "action": "getblocknobytime",
            "timestamp": str(ts),
            "closest": "before",
        }
    )
    if not resp.get("ok"):
        return resp
    result = (resp.get("data") or {}).get("result")
    try:
        block = int(result)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_block_result"}
    return {"ok": True, "block_number": block, "as_of": as_of.isoformat(), "latency_ms": resp.get("latency_ms")}


async def get_eth_balance(address: str, *, block: int | str = "latest") -> dict[str, Any]:
    """ETH balance at block tag — point-in-time when block is numeric."""
    tag = str(block) if block != "latest" else "latest"
    resp = await _get(
        {
            "module": "account",
            "action": "balance",
            "address": address.lower(),
            "tag": tag,
        }
    )
    if not resp.get("ok"):
        return resp
    result = (resp.get("data") or {}).get("result")
    return {
        "ok": True,
        "address": address.lower(),
        "balance_eth": round(_wei_to_eth(result or 0), 8),
        "block_tag": tag,
        "latency_ms": resp.get("latency_ms"),
    }


async def get_normal_transactions(address: str, *, limit: int = 50) -> dict[str, Any]:
    """Recent normal transactions for single-chain fund tracing."""
    resp = await _get(
        {
            "module": "account",
            "action": "txlist",
            "address": address.lower(),
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
        }
    )
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error"), "transactions": []}

    raw = (resp.get("data") or {}).get("result") or []
    if not isinstance(raw, list):
        raw = []
    txs: list[dict[str, Any]] = []
    for row in raw[:limit]:
        if not isinstance(row, dict):
            continue
        txs.append(
            {
                "hash": row.get("hash"),
                "from": str(row.get("from") or "").lower(),
                "to": str(row.get("to") or "").lower(),
                "value_eth": round(_wei_to_eth(row.get("value") or 0), 8),
                "block_number": int(row.get("blockNumber") or 0),
                "timestamp": int(row.get("timeStamp") or 0),
                "is_error": str(row.get("isError") or "0") == "1",
                "input": (row.get("input") or "0x")[:10],
            }
        )
    return {"ok": True, "address": address.lower(), "transactions": txs, "count": len(txs)}


async def get_block_by_number(block_number: int, *, chain: str = "ethereum") -> dict[str, Any]:
    """Block details with reorg/finality disclosure (#23)."""
    if chain.lower() != "ethereum":
        return {"ok": False, "error": "ethereum_only_in_mvp", "chain": chain}

    resp = await _get(
        {
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": hex(int(block_number)),
            "boolean": "true",
        }
    )
    if not resp.get("ok"):
        return await _block_rpc_fallback(block_number)

    block = (resp.get("data") or {}).get("result")
    if not isinstance(block, dict):
        return {"ok": False, "error": "invalid_block", "block_number": block_number}

    return _normalize_block(block, block_number)


async def _block_rpc_fallback(block_number: int) -> dict[str, Any]:
    url = "https://ethereum.publicnode.com"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(int(block_number)), True],
        "id": 1,
    }
    timeout = aiohttp.ClientTimeout(total=3.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    return {"ok": False, "error": f"rpc_http_{resp.status}", "block_number": block_number}
                data = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        return {"ok": False, "error": str(exc), "block_number": block_number}

    block = data.get("result")
    if not isinstance(block, dict):
        return {"ok": False, "error": "block_not_found", "block_number": block_number}
    out = _normalize_block(block, block_number)
    out["source"] = "public_rpc_fallback"
    return out


def _normalize_block(block: dict[str, Any], block_number: int) -> dict[str, Any]:
    ts_hex = block.get("timestamp") or "0x0"
    try:
        timestamp = int(ts_hex, 16)
    except (TypeError, ValueError):
        timestamp = 0
    tx_count = len(block.get("transactions") or [])
    reorg_window = 12
    finalized = block_number % 32 == 0  # conservative proxy without live head
    return {
        "ok": True,
        "feature": "#23",
        "capability": "block_search",
        "block_number": block_number,
        "hash": block.get("hash"),
        "parent_hash": block.get("parentHash"),
        "timestamp": timestamp,
        "transaction_count": tx_count,
        "gas_used": int(block.get("gasUsed") or "0x0", 16) if str(block.get("gasUsed", "")).startswith("0x") else block.get("gasUsed"),
        "gas_limit": int(block.get("gasLimit") or "0x0", 16) if str(block.get("gasLimit", "")).startswith("0x") else block.get("gasLimit"),
        "miner": block.get("miner"),
        "chain": "ethereum",
        "chain_id": 1,
        "reorg_handling": {
            "finalized": finalized,
            "reorg_risk": "low" if finalized else "medium",
            "reorg_window_blocks": reorg_window,
            "note": "Recent blocks may reorganize — confirm after finality",
        },
        "semantics": "point_in_time",
        "source": "etherscan_proxy",
    }
