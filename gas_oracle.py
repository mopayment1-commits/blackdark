"""
BLACKDARK — Live Gas Fee Oracle (Ethereum, BSC, Solana).

Fetches gas/compute prices via public RPCs, converts to USD, caches ~12s.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.GasOracle")

_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TS: dict[str, float] = {}
_REFRESH_TASK: asyncio.Task | None = None
_REFRESH_INTERVAL_SEC = float(getattr(config, "GAS_ORACLE_REFRESH_SEC", 12))

# Typical gas units per swap type
SWAP_GAS_UNITS = {
    "ethereum": 180_000,
    "bsc": 120_000,
    "arbitrum": 250_000,
    "polygon": 200_000,
    "solana": 200_000,  # compute units proxy
}

RPC_ENDPOINTS = {
    "ethereum": "https://ethereum.publicnode.com",
    "bsc": "https://bsc-dataseed.binance.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "polygon": "https://polygon-rpc.com",
    "solana": "https://api.mainnet-beta.solana.com",
}

# Display-only reference levels — NEVER used for executable gas / DeFi P&L.
# Executable paths must fail closed when a live native/USD mid is unavailable.
NATIVE_USD_DISPLAY_ONLY = {
    "ethereum": 3500.0,
    "bsc": 600.0,
    "arbitrum": 3500.0,
    "polygon": 0.5,
    "solana": 180.0,
}

# Cached gas older than this is not executable truth.
_MAX_STALE_SEC = float(getattr(config, "GAS_ORACLE_MAX_STALE_SEC", 60))


async def _rpc_post(session: aiohttp.ClientSession, url: str, payload: dict[str, Any]) -> Any:
    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
        if resp.status != 200:
            return None
        data = await resp.json()
        return data.get("result")


async def _fetch_eth_gas_gwei(session: aiohttp.ClientSession, chain: str) -> float | None:
    url = RPC_ENDPOINTS.get(chain)
    if not url:
        return None
    if chain == "solana":
        return await _fetch_solana_priority_fee(session)

    hex_gas = await _rpc_post(
        session,
        url,
        {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1},
    )
    if not hex_gas:
        return None
    try:
        wei = int(str(hex_gas), 16)
        return wei / 1e9
    except (TypeError, ValueError):
        return None


async def _fetch_solana_priority_fee(session: aiohttp.ClientSession) -> float | None:
    url = RPC_ENDPOINTS["solana"]
    result = await _rpc_post(
        session,
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getRecentPrioritizationFees",
            "params": [[]],
        },
    )
    if not result:
        # Fail closed — do not invent priority fees for executable DeFi P&L.
        return None
    fees = [int(row.get("prioritizationFee") or 0) for row in result if isinstance(row, dict)]
    if not fees:
        return None
    return float(sorted(fees)[len(fees) // 2])


def _native_usd(_session: aiohttp.ClientSession, chain: str) -> float | None:
    """Live native/USD mid for gas conversion. None when unknown (fail closed)."""
    asset_map = {
        "ethereum": "ETH",
        "bsc": "BNB",
        "arbitrum": "ETH",
        "polygon": "MATIC",
        "solana": "SOL",
    }
    asset = asset_map.get(chain)
    if not asset:
        return None
    try:
        from live_book_hub import get_best_price, is_quote_fresh

        symbol = f"{asset}/USDT"
        if not is_quote_fresh("binance", symbol):
            return None
        row = get_best_price("binance", symbol)
        if row and row.get("mid"):
            mid = float(row["mid"])
            if mid > 0:
                return mid
    except Exception as exc:
        import logging

        logging.getLogger("BLACKDARK.GasOracle").debug(
            "native_usd_lookup_failed chain=%s err_type=%s",
            chain,
            type(exc).__name__,
        )
    return None


def _chain_from_dex_chain_id(chain_id: str | None) -> str | None:
    """Map DexScreener/chain labels to gas cache keys. Unknown → None (fail closed)."""
    if not chain_id:
        return None
    c = str(chain_id).lower()
    mapping = {
        "ethereum": "ethereum",
        "eth": "ethereum",
        "bsc": "bsc",
        "bnb": "bsc",
        "binance-smart-chain": "bsc",
        "arbitrum": "arbitrum",
        "polygon": "polygon",
        "matic": "polygon",
        "solana": "solana",
    }
    return mapping.get(c)


def _solana_gas_row(lamports: float, native_usd: float) -> dict[str, Any]:
    # ~2 signatures + swap CU
    cost_usd = (lamports / 1e9) * native_usd * 2
    return {
        "chain": "solana",
        "lamports_priority": lamports,
        "native_usd": native_usd,
        "swap_cost_usd": round(max(0.001, cost_usd), 4),
        "updated_ms": int(time.time() * 1000),
        "native_usd_source": "live_mid",
    }


def _evm_gas_row(chain: str, gwei: float, native_usd: float) -> dict[str, Any]:
    gas_units = SWAP_GAS_UNITS.get(chain, 180_000)
    cost_usd = (gwei * 1e-9) * gas_units * native_usd
    return {
        "chain": chain,
        "gas_gwei": round(gwei, 3),
        "gas_units": gas_units,
        "native_usd": round(native_usd, 2),
        "swap_cost_usd": round(max(0.01, cost_usd), 4),
        "updated_ms": int(time.time() * 1000),
        "native_usd_source": "live_mid",
    }


async def _build_chain_gas_row(
    session: aiohttp.ClientSession,
    chain: str,
) -> dict[str, Any] | None:
    """Build one cache row; None when live gas or native/USD mid is unknown."""
    if chain == "solana":
        lamports = await _fetch_solana_priority_fee(session)
        native_usd = _native_usd(session, chain)
        if lamports is None or native_usd is None:
            return None
        return _solana_gas_row(lamports, native_usd)

    gwei = await _fetch_eth_gas_gwei(session, chain)
    if gwei is None:
        return None
    native_usd = _native_usd(session, chain)
    if native_usd is None:
        return None
    return _evm_gas_row(chain, gwei, native_usd)


async def refresh_gas_cache(*, chains: tuple[str, ...] = ("ethereum", "bsc", "solana")) -> dict[str, Any]:
    global _CACHE, _CACHE_TS
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for chain in chains:
            try:
                row = await _build_chain_gas_row(session, chain)
                if row is None:
                    continue
                _CACHE[chain] = row
                _CACHE_TS[chain] = time.monotonic()
            except Exception:
                logger.debug("Gas refresh failed | chain=%s", chain, exc_info=True)
    return dict(_CACHE)


async def get_swap_gas_usd(chain: str, *, hops: int = 1) -> float | None:
    """Live swap gas cost in USD for chain (cached).

    Returns None when gas or native/USD conversion is unknown/stale.
    Callers MUST fail closed — never invent a default gas USD for P&L.
    """
    chain_key = _chain_from_dex_chain_id(chain)
    if not chain_key:
        return None
    age = time.monotonic() - _CACHE_TS.get(chain_key, 0.0)
    if chain_key not in _CACHE or age > _REFRESH_INTERVAL_SEC:
        await refresh_gas_cache(chains=(chain_key, "ethereum", "bsc", "solana"))
    age = time.monotonic() - _CACHE_TS.get(chain_key, 0.0)
    row = _CACHE.get(chain_key) or {}
    if not row or "swap_cost_usd" not in row:
        return None
    if age > _MAX_STALE_SEC:
        return None
    base = float(row["swap_cost_usd"])
    if base <= 0:
        return None
    return base * max(1, hops)


async def gas_cost_bps(chain: str, quote_usd: float, *, hops: int = 1) -> float | None:
    """Gas cost in bps of quote; None when gas truth is unknown (fail closed)."""
    if quote_usd <= 0:
        return None
    cost = await get_swap_gas_usd(chain, hops=hops)
    if cost is None:
        return None
    return (cost / quote_usd) * 10_000


def oracle_stats() -> dict[str, Any]:
    return {
        "cached_chains": sorted(_CACHE.keys()),
        "quotes": dict(_CACHE),
        "refresh_interval_sec": _REFRESH_INTERVAL_SEC,
    }


def start_gas_oracle_loop() -> asyncio.Task | None:
    global _REFRESH_TASK
    if _REFRESH_TASK is not None:
        return _REFRESH_TASK

    async def _loop() -> None:
        try:
            await refresh_gas_cache()
        except Exception:
            logger.exception("Gas oracle initial refresh failed.")
        while True:
            await asyncio.sleep(_REFRESH_INTERVAL_SEC)
            try:
                await refresh_gas_cache()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Gas oracle loop error")

    _REFRESH_TASK = asyncio.create_task(_loop(), name="gas-oracle")
    logger.info("Gas oracle started (background refresh).")
    return _REFRESH_TASK


async def stop_gas_oracle_loop() -> None:
    global _REFRESH_TASK
    if _REFRESH_TASK is not None:
        _REFRESH_TASK.cancel()
        await asyncio.gather(_REFRESH_TASK, return_exceptions=True)
        _REFRESH_TASK = None
