"""
Unified Cross-Chain Explorer (#101) — one address, all chains, all transactions.

Core infrastructure: pluggable chain adapters + shared index. NOT a generic search UI bolt-on.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from blackdark.canonical.cross_chain_schema import (
    normalize_evm_tx,
    normalize_solana_sig,
)
from bd_platform.transaction_index import append_transactions, encode_cursor, query_index

logger = logging.getLogger("BLACKDARK.CrossChainExplorer")

_CHAIN_REGISTRY: dict[str, dict[str, Any]] = {
    "ethereum": {"chain_id": 1, "env_key": "ETHERSCAN_API_KEY", "base": "https://api.etherscan.io/api"},
    "bsc": {"chain_id": 56, "env_key": "BSCSCAN_API_KEY", "base": "https://api.bscscan.com/api"},
    "arbitrum": {"chain_id": 42161, "env_key": "ARBISCAN_API_KEY", "base": "https://api.arbiscan.io/api"},
    "polygon": {"chain_id": 137, "env_key": "POLYGONSCAN_API_KEY", "base": "https://api.polygonscan.com/api"},
    "solana": {"chain_id": "solana", "env_key": None, "base": None},
    "tron": {"chain_id": "tron", "env_key": "TRONSCAN_API_KEY", "base": None},
}

_SUPPORTED_CHAINS = tuple(_CHAIN_REGISTRY.keys())


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _detect_address_chains(address: str) -> list[str]:
    addr = (address or "").strip()
    if addr.startswith("T") and len(addr) >= 30:
        return ["tron"]
    if addr.startswith("0x") and len(addr) >= 40:
        return ["ethereum", "bsc", "arbitrum", "polygon"]
    if len(addr) >= 32 and not addr.startswith("0x"):
        return ["solana"]
    return list(_SUPPORTED_CHAINS)


async def _fetch_evm_scan_txs(
    address: str,
    *,
    chain: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    cfg = _CHAIN_REGISTRY[chain]
    env_key = cfg.get("env_key")
    api_key = (os.getenv(env_key or "") or "").strip() if env_key else ""
    if not api_key:
        if chain == "ethereum":
            from bd_platform.onchain_client import get_normal_transactions

            resp = await get_normal_transactions(address, limit=limit)
            if resp.get("ok"):
                return [
                    {
                        **t,
                        "chain": chain,
                        "chain_id": cfg["chain_id"],
                        "timeStamp": t.get("timestamp"),
                        "hash": t.get("hash"),
                    }
                    for t in resp.get("transactions") or []
                ]
        return []

    from blackdark.ingestion.unified_connector import UnifiedConnector

    slug = f"{chain}_scan"
    conn = UnifiedConnector(source_slug=slug)
    resp = await conn.get_json(
        str(cfg["base"]),
        params={
            "module": "account",
            "action": "txlist",
            "address": address.lower(),
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": api_key,
        },
        cache_parts=("txlist", chain, address.lower(), limit),
        ttl=conn.ttl(f"{chain.upper()}_SCAN_CACHE_TTL_SEC", 300),
    )
    if not resp.get("ok"):
        return []
    raw = (resp.get("data") or {}).get("result") or []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for row in raw[:limit]:
        norm = normalize_evm_tx(row, chain=chain, chain_id=int(cfg["chain_id"]), source=slug)
        if norm:
            out.append(norm.to_dict())
    return out


async def _fetch_solana_txs(address: str, *, limit: int = 50) -> list[dict[str, Any]]:
    from blackdark.ingestion.solana_rpc_connector import _rpc_call

    resp = await _rpc_call(
        "getSignaturesForAddress",
        [address, {"limit": min(50, limit)}],
        timeout_sec=3.0,
    )
    if not resp.get("ok"):
        return []
    rows = resp.get("result") or []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        norm = normalize_solana_sig(
            {
                "signature": row.get("signature"),
                "blockTime": row.get("blockTime"),
                "slot": row.get("slot"),
                "from": address,
            },
            source="solana_rpc",
        )
        if norm:
            out.append(norm.to_dict())
    return out


async def _fetch_tron_txs(address: str, *, limit: int = 50) -> list[dict[str, Any]]:
    from blackdark.ingestion.tronscan_connector import fetch_tron_transactions

    resp = await fetch_tron_transactions(address, limit=limit)
    return list(resp.get("transactions") or []) if resp.get("ok") else []


_CHAIN_FETCHERS: dict[str, Callable[..., Awaitable[list[dict[str, Any]]]]] = {
    "ethereum": _fetch_evm_scan_txs,
    "bsc": _fetch_evm_scan_txs,
    "arbitrum": _fetch_evm_scan_txs,
    "polygon": _fetch_evm_scan_txs,
    "solana": _fetch_solana_txs,
    "tron": _fetch_tron_txs,
}


async def _fetch_chain_assets(address: str, chain: str) -> dict[str, Any]:
    if chain == "tron":
        from blackdark.ingestion.tronscan_connector import fetch_tron_account

        return await fetch_tron_account(address)
    if chain == "solana":
        from blackdark.ingestion.solana_rpc_connector import fetch_solana_balance

        bal = await fetch_solana_balance(address)
        return {
            "ok": bal.get("ok"),
            "chain": "solana",
            "assets": [
                {
                    "chain": "solana",
                    "symbol": "SOL",
                    "balance": bal.get("balance_sol"),
                    "source": "solana_rpc",
                }
            ]
            if bal.get("ok")
            else [],
        }
    from bd_platform.address_intelligence import search_address

    result = await search_address(address, chain=chain)
    total_usd = float(result.get("total_usd") or 0) if result.get("ok") else 0.0
    assets: list[dict[str, Any]] = []
    if total_usd > 0 or result.get("ok"):
        assets.append(
            {
                "chain": chain,
                "chain_id": _CHAIN_REGISTRY[chain]["chain_id"],
                "address": address,
                "symbol": "MULTI",
                "balance_usd": round(total_usd, 2),
                "source": (result.get("balance") or {}).get("source", "address_search"),
            }
        )
    return {"ok": result.get("ok", False), "chain": chain, "assets": assets, "data_state": result.get("data_state", "LIVE")}


async def fetch_and_index_address(address: str, *, chains: list[str] | None = None) -> dict[str, Any]:
    """Pull live txs from adapters and append to index."""
    target_chains = [c.lower() for c in (chains or _detect_address_chains(address))]
    all_rows: list[dict[str, Any]] = []
    for chain in target_chains:
        fetcher = _CHAIN_FETCHERS.get(chain)
        if not fetcher:
            continue
        if chain in {"ethereum", "bsc", "arbitrum", "polygon"}:
            rows = await fetcher(address, chain=chain, limit=50)
        else:
            rows = await fetcher(address, limit=50)
        all_rows.extend(rows)
    indexed = append_transactions(all_rows)
    return {"ok": True, "fetched": len(all_rows), "indexed_new": indexed}


async def search_transactions(
    *,
    address: str | None = None,
    chains: list[str] | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    cursor: str | None = None,
    limit: int = 50,
    refresh: bool = False,
) -> dict[str, Any]:
    """Transaction search with indexed filtering, pagination, chain/time semantics (#101)."""
    t0 = time.perf_counter()
    if refresh and address:
        await fetch_and_index_address(address, chains=chains)

    page = query_index(
        address=address,
        chains=chains,
        start_time=start_time,
        end_time=end_time,
        cursor=cursor,
        limit=limit,
    )

    # Live supplement when index empty for address
    if address and not page.get("results") and not cursor:
        await fetch_and_index_address(address, chains=chains)
        page = query_index(
            address=address,
            chains=chains,
            start_time=start_time,
            end_time=end_time,
            cursor=cursor,
            limit=limit,
        )

    elapsed = time.perf_counter() - t0
    return {
        **page,
        "feature": "#101",
        "capability": "transaction_search",
        "surface": "unified_cross_chain_explorer",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def unified_address_explorer(address: str, *, tx_limit: int = 25) -> dict[str, Any]:
    """
    Unified Cross-Chain Explorer — one address, assets + transactions across chains.
    """
    t0 = time.perf_counter()
    addr = (address or "").strip()
    if len(addr) < 10:
        return {"ok": False, "error": "invalid_address", "address": addr}

    chains = _detect_address_chains(addr)
    asset_tasks = [_fetch_chain_assets(addr, c) for c in chains]
    tx_tasks = []
    for chain in chains:
        fetcher = _CHAIN_FETCHERS.get(chain)
        if not fetcher:
            continue
        if chain in {"ethereum", "bsc", "arbitrum", "polygon"}:
            tx_tasks.append(fetcher(addr, chain=chain, limit=tx_limit))
        else:
            tx_tasks.append(fetcher(addr, limit=tx_limit))

    asset_results, tx_results = await asyncio.gather(
        asyncio.gather(*asset_tasks, return_exceptions=True),
        asyncio.gather(*tx_tasks, return_exceptions=True),
    )

    per_chain_assets: dict[str, Any] = {}
    all_assets: list[dict[str, Any]] = []
    for chain, result in zip(chains, asset_results):
        if isinstance(result, BaseException) or not isinstance(result, dict):
            per_chain_assets[chain] = {"ok": False, "assets": []}
            continue
        assets = result.get("assets") or result.get("balance", {}).get("assets") or []
        if isinstance(assets, dict):
            assets = [assets]
        per_chain_assets[chain] = {"ok": result.get("ok"), "assets": assets, "data_state": result.get("data_state", "LIVE")}
        all_assets.extend(assets if isinstance(assets, list) else [])

    per_chain_txs: dict[str, list[dict[str, Any]]] = {}
    unified_txs: list[dict[str, Any]] = []
    for chain, result in zip(chains, tx_results):
        if isinstance(result, BaseException):
            per_chain_txs[chain] = []
            continue
        rows = result if isinstance(result, list) else []
        per_chain_txs[chain] = rows
        unified_txs.extend(rows)

    unified_txs.sort(key=lambda r: (-int(r.get("timestamp") or 0), str(r.get("chain") or ""), str(r.get("tx_hash") or "")))
    append_transactions(unified_txs)

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#101",
        "capability": "unified_cross_chain_explorer",
        "address": addr,
        "chains_queried": chains,
        "assets_by_chain": per_chain_assets,
        "assets_unified": all_assets,
        "transactions_by_chain": per_chain_txs,
        "transactions_unified": unified_txs[: tx_limit * len(chains)],
        "transaction_count": len(unified_txs),
        "headline": f"Cross-chain view: {len(chains)} chains, {len(unified_txs)} recent transactions",
        "semantics": "point_in_time",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 5.0,
        "timestamp": _utcnow(),
    }


def chain_registry() -> dict[str, Any]:
    """Expose registry for adding chains without restructuring."""
    return {
        "chains": list(_SUPPORTED_CHAINS),
        "registry": _CHAIN_REGISTRY,
        "add_chain_note": "Register adapter in _CHAIN_FETCHERS + _CHAIN_REGISTRY",
    }
