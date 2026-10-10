"""On-chain hub — DexScreener, GeckoTerminal, free wallet/social integrations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

from path_safety import assert_url_path_safe, safe_url_segment

logger = logging.getLogger("BLACKDARK.OnchainHub")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _get_json(url: str, *, headers: dict | None = None, params: dict | None = None) -> Any:
    timeout = aiohttp.ClientTimeout(total=12)
    safe_url = assert_url_path_safe(url)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(safe_url, headers=headers, params=params) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


async def dexscreener_pairs(query: str = "BTC") -> dict[str, Any]:
    from blackdark.ingestion.dexscreener_connector import fetch_dex_pairs

    row = await fetch_dex_pairs(query)
    q = safe_url_segment(query)
    if not row.get("ok"):
        data = await _get_json(
            "https://api.dexscreener.com/latest/dex/search",
            params={"q": q},
        )
        pairs = (data or {}).get("pairs") or []
        return {"source": "dexscreener", "query": q, "pairs": pairs[:25], "count": len(pairs)}
    return {
        "source": row.get("source", "dexscreener"),
        "query": q,
        "pairs": row.get("pairs") or [],
        "count": row.get("count", 0),
        "liquidity_signal": row.get("liquidity_signal"),
        "cache_hit": row.get("cache_hit"),
        "stale_fallback": row.get("stale_fallback"),
        "sla_met": row.get("sla_met"),
    }


async def geckoterminal_pairs(
    network: str = "eth",
    contract_address: str = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
) -> dict[str, Any]:
    net = safe_url_segment(network)
    address = safe_url_segment(contract_address)
    url = f"https://api.geckoterminal.com/api/v2/networks/{net}/tokens/{address}/pools"
    data = await _get_json(url)
    return {"source": "geckoterminal", "network": net, "pools": (data or {}).get("data") or []}


async def debank_wallet(address: str) -> dict[str, Any]:
    from bd_platform.free_integrations import wallet_balance

    return await wallet_balance(address)


async def l2beat_security() -> dict[str, Any]:
    data = await _get_json("https://l2beat.com/api/tvl")
    return {"source": "l2beat", "timestamp": _utcnow(), "projects": data}


async def defillama_raises() -> dict[str, Any]:
    data = await _get_json("https://api.llama.fi/raises")
    rows = data if isinstance(data, list) else []
    return {"source": "defillama", "raises": rows[:50], "count": len(rows)}


async def lookintobitcoin_macro() -> dict[str, Any]:
    from bd_platform.free_market_data import _get_json

    mempool = await _get_json("https://mempool.space/api/v1/mining/hashrate/1m")
    fees = await _get_json("https://mempool.space/api/v1/fees/recommended")
    hashrate = None
    if isinstance(mempool, dict) and mempool.get("hashrates"):
        latest = mempool["hashrates"][-1] if mempool["hashrates"] else {}
        hashrate = latest.get("avgHashrate")

    return {
        "source": "lookintobitcoin_plus_mempool",
        "timestamp": _utcnow(),
        "live_metrics": {
            "btc_hashrate": hashrate,
            "fee_fastest_sat_vb": (fees or {}).get("fastestFee"),
            "fee_hour_sat_vb": (fees or {}).get("hourFee"),
        },
        "indicators": [
            {"id": "mvrv", "label": "MVRV Z-Score", "url": "https://www.lookintobitcoin.com/charts/mvrv-zscore/"},
            {"id": "puell", "label": "Puell Multiple", "url": "https://www.lookintobitcoin.com/charts/puell-multiple/"},
            {"id": "rhodl", "label": "RHODL Ratio", "url": "https://www.lookintobitcoin.com/charts/rhodl-ratio/"},
            {"id": "hashrate", "label": "Network Hashrate (live)", "value": hashrate, "source": "mempool.space"},
        ],
        "note": "Macro cycle charts on LookIntoBitcoin + live BTC hashrate/fees from mempool.space (free)",
    }


async def lunarcrush_metrics(symbol: str = "BTC") -> dict[str, Any]:
    from bd_platform.free_integrations import lunarcrush_social

    return await lunarcrush_social(symbol)


async def coinmarketcal_events() -> dict[str, Any]:
    from bd_platform.free_integrations import coinmarketcal_events as _events

    return await _events()


async def wallet_clusters(address: str) -> dict[str, Any]:
    from bd_platform.free_integrations import wallet_clusters as _clusters

    return await _clusters(address)


async def scopescan_labels(address: str) -> dict[str, Any]:
    from bd_platform.free_integrations import wallet_labels

    return await wallet_labels(address)


async def blockpour_flows() -> dict[str, Any]:
    from bd_platform.free_integrations import cross_chain_flows

    return await cross_chain_flows()


async def intotheblock_metrics(asset: str = "BTC") -> dict[str, Any]:
    from bd_platform.free_integrations import holder_analytics

    return await holder_analytics(asset)
