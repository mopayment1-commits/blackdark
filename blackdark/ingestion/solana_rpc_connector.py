"""
Solana public RPC connector (#93) — silent on-chain ingestion.

Prototype uses public RPC; production upgrade path: HELIUS / QUICKNODE / ALCHEMY
via `SOLANA_RPC_URL`. Users see "Solana on-chain data included" — not RPC branding.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.SolanaRPC")

_DEFAULT_PUBLIC_ENDPOINTS = (
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
)
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 60


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _rpc_endpoints() -> list[str]:
    primary = (os.getenv("SOLANA_RPC_URL") or "").strip()
    if primary:
        return [primary, *_DEFAULT_PUBLIC_ENDPOINTS]
    return list(_DEFAULT_PUBLIC_ENDPOINTS)


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if row and time.time() - row[0] < _CACHE_TTL:
        return row[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


async def _rpc_call(method: str, params: list[Any], *, timeout_sec: float = 2.0) -> dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    headers = {"Content-Type": "application/json", "User-Agent": "BLACKDARK/1.0"}
    last_error = "rpc_unavailable"
    for url in _rpc_endpoints():
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        last_error = f"http_{resp.status}"
                        continue
                    data = await resp.json()
            if "error" in data:
                last_error = str(data["error"])
                continue
            return {"ok": True, "result": data.get("result"), "endpoint": url}
        except (aiohttp.ClientError, TimeoutError) as exc:
            last_error = str(exc)
    return {"ok": False, "error": last_error}


async def fetch_solana_balance(address: str) -> dict[str, Any]:
    """SOL balance for a base58 address."""
    t0 = time.perf_counter()
    key = f"balance:{address}"
    cached = _cache_get(key)
    if cached:
        return {**cached, "cache_hit": True}

    resp = await _rpc_call("getBalance", [address])
    if not resp.get("ok"):
        return {"ok": False, "address": address, "error": resp.get("error")}

    lamports = int(resp.get("result", {}).get("value") or 0)
    sol = lamports / 1_000_000_000
    elapsed = time.perf_counter() - t0
    out = {
        "ok": True,
        "address": address,
        "balance_sol": round(sol, 9),
        "lamports": lamports,
        "chain": "solana",
        "ingestion_role": "onchain_balance",
        "feature": "#93",
        "rpc_tier": "dedicated" if os.getenv("SOLANA_RPC_URL") else "public",
        "endpoint": resp.get("endpoint"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
    _cache_set(key, out)
    return out


async def fetch_solana_chain_health() -> dict[str, Any]:
    """Slot + health for ingestion monitoring."""
    t0 = time.perf_counter()
    slot_resp = await _rpc_call("getSlot", [])
    health_resp = await _rpc_call("getHealth", [])
    elapsed = time.perf_counter() - t0
    ok = slot_resp.get("ok") is True
    return {
        "ok": ok,
        "feature": "#93",
        "slot": slot_resp.get("result") if ok else None,
        "health": health_resp.get("result"),
        "rpc_tier": "dedicated" if os.getenv("SOLANA_RPC_URL") else "public",
        "upgrade_path": "Set SOLANA_RPC_URL to Helius/QuickNode/Alchemy for production",
        "user_facing_note": "Solana on-chain data included",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def solana_rpc_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "solana_rpc_ingestion_connector",
        "role": "solana_onchain_input",
        "feature": "#93",
        "rpc_tier": "dedicated" if os.getenv("SOLANA_RPC_URL") else "public",
        "endpoints_configured": len(_rpc_endpoints()),
        "cache_ttl_seconds": _CACHE_TTL,
        "timestamp": _utcnow(),
    }
