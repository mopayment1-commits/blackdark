"""
Polygonscan API connector (#87) — silent Polygon on-chain ingestion.

NOT a branded surface. Users see "Polygon on-chain data included in analysis".
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.Polygonscan")

API_BASE = "https://api.polygonscan.com/api"
_RPC_FALLBACK = "https://polygon-rpc.com"
_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=86400)
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("POLYGONSCAN_API_KEY") or "").strip()
    return key or None


async def _rpc_block_number() -> dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
    timeout = aiohttp.ClientTimeout(total=3.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.post(_RPC_FALLBACK, json=payload) as resp:
                if resp.status != 200:
                    return {"ok": False, "error": f"http_{resp.status}"}
                data = await resp.json()
        result = data.get("result")
        if not result:
            return {"ok": False, "error": "empty_rpc_result"}
        return {"ok": True, "block_number": int(result, 16), "source": "polygon_rpc"}
    except (aiohttp.ClientError, TimeoutError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


async def fetch_polygon_onchain_health() -> dict[str, Any]:
    """Polygon chain health — block + gas via Polygonscan with RPC fallback."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("POLYGONSCAN_CACHE_TTL_SEC", 300)
    ck = cache_key("polygon_onchain_health")
    cached = _CACHE.get(ck, ttl=ttl)
    if cached:
        return {**cached, "cache_hit": True}

    block_number = None
    gas_gwei = None
    source = "polygonscan"
    api_key = _api_key()

    if api_key:
        params = {"module": "proxy", "action": "eth_blockNumber", "apikey": api_key}
        block_resp = await _CACHE.http_get_json(
            API_BASE,
            params=params,
            timeout_sec=3.0,
            cache_key=cache_key("polygonscan_block"),
            ttl=ttl,
            source_slug="polygonscan",
        )
        if block_resp.get("ok"):
            raw = (block_resp.get("data") or {}).get("result")
            try:
                block_number = int(str(raw), 16) if raw else None
            except (TypeError, ValueError):
                block_number = None

        gas_params = {"module": "proxy", "action": "eth_gasPrice", "apikey": api_key}
        gas_resp = await _CACHE.http_get_json(
            API_BASE,
            params=gas_params,
            timeout_sec=3.0,
            cache_key=cache_key("polygonscan_gas"),
            ttl=ttl,
            source_slug="polygonscan",
        )
        if gas_resp.get("ok"):
            raw_gas = (gas_resp.get("data") or {}).get("result")
            try:
                gas_gwei = round(int(str(raw_gas), 16) / 1e9, 4) if raw_gas else None
            except (TypeError, ValueError):
                gas_gwei = None

    if block_number is None:
        rpc = await _rpc_block_number()
        if rpc.get("ok"):
            block_number = rpc.get("block_number")
            source = "polygon_rpc_fallback"

    stale = _CACHE.get_stale(ck)
    if block_number is None and stale:
        return {**stale, "ok": True, "stale_fallback": True}

    elapsed = time.perf_counter() - t0
    ok = block_number is not None
    result = {
        "ok": ok,
        "feature": "#87",
        "ingestion_role": "polygon_onchain_input",
        "chain": "polygon",
        "chain_id": 137,
        "block_number": block_number,
        "gas_gwei": gas_gwei,
        "source": source,
        "api_key_configured": bool(api_key),
        "user_facing_note": "Polygon on-chain data included in analysis",
        "data_state": "LIVE" if ok else "MISSING",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
    if ok:
        _CACHE.set(ck, result)
    return result


def polygonscan_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "polygonscan_ingestion_connector",
        "role": "polygon_onchain_input",
        "feature": "#87",
        "api_key_configured": bool(_api_key()),
        "cache_ttl_seconds": _CACHE.ttl("POLYGONSCAN_CACHE_TTL_SEC", 300),
        "circuit_open": is_open("polygonscan"),
        "fallback_chain": ["polygonscan", "polygon_rpc", "stale_cache"],
        "timestamp": _utcnow(),
    }
