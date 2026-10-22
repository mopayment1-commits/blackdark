"""
DefiLlama public APIs (no API key) — TVL, fees overview, yield pools.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.DefiLlama")

_TIMEOUT = aiohttp.ClientTimeout(total=16)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

_CHAINS_URL = "https://api.llama.fi/v2/chains"
_PROTOCOLS_URL = "https://api.llama.fi/protocols"
_YIELDS_URL = "https://yields.llama.fi/pools"
_FEES_URL = "https://api.llama.fi/overview/fees"

_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SEC = 120.0

_ASSET_TO_CHAIN: dict[str, str] = {
    "ETH": "Ethereum",
    "SOL": "Solana",
    "BNB": "BNB",
    "AVAX": "Avalanche",
    "MATIC": "Polygon",
    "POL": "Polygon",
    "ARB": "Arbitrum",
    "OP": "Optimism",
    "FTM": "Fantom",
    "BASE": "Base",
}


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > _CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


async def _get_json(url: str, *, params: dict[str, str] | None = None) -> Any | None:
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=_HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.debug("DefiLlama HTTP %s %s", resp.status, url)
                    return None
                return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def fetch_chains_tvl() -> list[dict[str, Any]]:
    cached = _cache_get("chains")
    if cached is not None:
        return cached
    data = await _get_json(_CHAINS_URL)
    if not isinstance(data, list):
        return []
    chains = [
        {"name": c.get("name"), "tvl_usd": float(c.get("tvl") or 0)}
        for c in data
        if isinstance(c, dict) and c.get("name")
    ]
    chains.sort(key=lambda x: x["tvl_usd"], reverse=True)
    _cache_set("chains", chains)
    return chains


async def fetch_top_protocols(limit: int = 8) -> list[dict[str, Any]]:
    cached = _cache_get("protocols")
    if cached is not None:
        return cached[:limit]
    data = await _get_json(_PROTOCOLS_URL)
    if not isinstance(data, list):
        return []
    rows: list[dict[str, Any]] = []
    for p in data:
        if not isinstance(p, dict):
            continue
        try:
            tvl = float(p.get("tvl") or 0)
        except (TypeError, ValueError):
            tvl = 0.0
        if tvl <= 0:
            continue
        rows.append(
            {
                "name": p.get("name"),
                "symbol": (p.get("symbol") or "").upper(),
                "slug": p.get("slug"),
                "tvl_usd": round(tvl, 2),
                "chain": p.get("chain"),
            }
        )
    rows.sort(key=lambda x: x["tvl_usd"], reverse=True)
    _cache_set("protocols", rows)
    return rows[:limit]


async def fetch_fees_leaders(limit: int = 5) -> list[dict[str, Any]]:
    cached = _cache_get("fees")
    if cached is not None:
        return cached[:limit]
    data = await _get_json(
        _FEES_URL,
        params={"excludeTotalDataChart": "true", "dataType": "dailyFees"},
    )
    protocols = (data or {}).get("protocols") if isinstance(data, dict) else None
    if not isinstance(protocols, list):
        return []
    rows: list[dict[str, Any]] = []
    for p in protocols:
        if not isinstance(p, dict):
            continue
        try:
            fees = float(p.get("total24h") or p.get("total7d") or 0)
        except (TypeError, ValueError):
            fees = 0.0
        if fees <= 0:
            continue
        rows.append(
            {
                "name": p.get("name") or p.get("displayName"),
                "slug": p.get("slug") or p.get("defillamaId"),
                "fees_24h_usd": round(fees, 2),
            }
        )
    rows.sort(key=lambda x: x["fees_24h_usd"], reverse=True)
    _cache_set("fees", rows)
    return rows[:limit]


async def fetch_top_yields(
    *,
    chain: str | None = None,
    symbol: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    cache_key = f"yields:{chain or ''}:{symbol or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached[:limit]
    data = await _get_json(_YIELDS_URL)
    pools = (data or {}).get("data") if isinstance(data, dict) else None
    if not isinstance(pools, list):
        return []
    sym = (symbol or "").upper().strip()
    chain_name = (chain or "").strip()
    rows: list[dict[str, Any]] = []
    for pool in pools:
        if not isinstance(pool, dict):
            continue
        try:
            apy = float(pool.get("apy") or 0)
            tvl = float(pool.get("tvlUsd") or 0)
        except (TypeError, ValueError):
            continue
        if apy <= 0 or tvl < 100_000:
            continue
        if chain_name and str(pool.get("chain") or "") != chain_name:
            continue
        if sym and sym not in str(pool.get("symbol") or "").upper():
            continue
        rows.append(
            {
                "project": pool.get("project"),
                "symbol": pool.get("symbol"),
                "chain": pool.get("chain"),
                "apy": round(apy, 2),
                "tvl_usd": round(tvl, 2),
            }
        )
    rows.sort(key=lambda x: (x["apy"], x["tvl_usd"]), reverse=True)
    _cache_set(cache_key, rows)
    return rows[:limit]


async def fetch_defi_context_for_asset(asset: str) -> dict[str, Any]:
    """Macro DeFi snapshot + optional chain/asset slice for Oracle / ledger."""
    sym = (asset or "ETH").upper().strip()
    chain = _ASSET_TO_CHAIN.get(sym)
    chains = await fetch_chains_tvl()
    total_tvl = round(sum(c["tvl_usd"] for c in chains), 2)
    chain_row = next((c for c in chains if c["name"] == chain), None) if chain else None
    protocols = await fetch_top_protocols(6)
    asset_protocols = [p for p in protocols if p.get("symbol") == sym][:3]
    fees = await fetch_fees_leaders(5)
    yields = await fetch_top_yields(chain=chain, symbol=sym if sym in {"ETH", "USDC", "USDT", "DAI"} else None, limit=5)
    if not yields and chain:
        yields = await fetch_top_yields(chain=chain, limit=5)
    return {
        "source": "defillama",
        "attribution": "Data: DefiLlama",
        "total_defi_tvl_usd": total_tvl,
        "chain": chain,
        "chain_tvl_usd": chain_row["tvl_usd"] if chain_row else None,
        "top_chains": chains[:5],
        "top_protocols": protocols[:5],
        "asset_protocols": asset_protocols,
        "fees_leaders_24h": fees,
        "top_yields": yields,
        "fetched_ok": bool(chains),
    }
