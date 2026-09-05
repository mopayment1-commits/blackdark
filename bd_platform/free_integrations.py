"""Free-tier integrations — social, wallet, labels, flows (no paid API required)."""

from __future__ import annotations

import base64
import logging
import os
from datetime import UTC, datetime
from typing import Any

import aiohttp

from path_safety import assert_url_path_safe, safe_url_segment

logger = logging.getLogger("BLACKDARK.FreeIntegrations")

_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_BLOCKPOUR_BASE = "https://services.blockpour.com/api"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _get_json(
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
) -> Any:
    merged = {**_HEADERS, **(headers or {})}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        safe_url = assert_url_path_safe(url)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(safe_url, headers=merged, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.debug("GET failed: %s", str(url).replace("\r", " ").replace("\n", " "))
        return None


async def socialtickers_asset(symbol: str) -> dict[str, Any] | None:
    sym = safe_url_segment(symbol.upper().replace("USDT", ""))
    data = await _get_json(f"https://socialtickers.com/api/v1/asset/{sym}")
    if not isinstance(data, dict):
        return None
    return {
        "source": "socialtickers",
        "symbol": sym,
        "mentions": data.get("mentions"),
        "upvotes": data.get("upvotes"),
        "price": data.get("price"),
        "change_24h_pct": data.get("change24"),
        "history": data.get("history"),
        "note": "Free LunarCrush-style social mentions (no API key)",
    }


async def socialtickers_leaderboard(*, limit: int = 20) -> list[dict[str, Any]]:
    data = await _get_json(
        "https://socialtickers.com/api/v1/leaderboard",
        params={"class": "crypto", "sort": "trending", "limit": limit},
    )
    if not isinstance(data, dict):
        return []
    return list(data.get("results") or [])[:limit]


async def lunarcrush_social(symbol: str = "BTC") -> dict[str, Any]:
    """LunarCrush optional key + socialtickers free fallback."""
    sym = safe_url_segment(symbol.upper().replace("USDT", ""))
    key = os.getenv("LUNARCRUSH_API_KEY", "").strip()
    lc_data = None
    lc_source = None
    if key:
        lc_data = await _get_json(
            f"https://lunarcrush.com/api4/public/coins/{safe_url_segment(sym.lower())}/v1",
            headers={"Authorization": f"Bearer {key}"},
        )
        lc_source = "lunarcrush_api4"
        if lc_data is None:
            lc_data = await _get_json(
                "https://lunarcrush.com/api4/public/coins/list/v1",
                headers={"Authorization": f"Bearer {key}"},
            )
            lc_source = "lunarcrush_list"

    free = await socialtickers_asset(sym)
    leaderboard = await socialtickers_leaderboard(limit=10)

    return {
        "available": True,
        "symbol": sym,
        "timestamp": _utcnow(),
        "primary_source": lc_source if lc_data else "socialtickers",
        "lunarcrush_configured": bool(key),
        "free_tier": free,
        "leaderboard_top": leaderboard,
        "lunarcrush": lc_data,
        "lunarcrush_note": "LUNARCRUSH_API_KEY — Hobby: market data 100/day; social needs Individual+",
        "references": ["socialtickers.com", "LunarCrush"],
    }


async def _coinmarketcal_official(limit: int, key: str) -> dict[str, Any] | None:
    data = await _get_json(
        "https://developers.coinmarketcal.com/v1/events",
        headers={"x-api-key": key, "Accept": "application/json"},
        params={"max": min(limit, 50), "page": 1},
    )
    if data is None:
        return None
    events = data if isinstance(data, list) else (data.get("body") or data.get("data") or [])
    return {
        "available": True,
        "source": "coinmarketcal",
        "events": events[:limit],
        "count": len(events),
        "tier": "official_free_key",
        "timestamp": _utcnow(),
    }


def _raise_events(raises: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for row in (raises or [])[:10]:
        if isinstance(row, dict):
            events.append({
                "title": row.get("name") or row.get("project"),
                "type": "funding_raise",
                "amount_usd": row.get("amount"),
                "date": row.get("date"),
                "source": "defillama_free",
            })
    return events


def _trending_events(trending: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for item in ((trending or {}).get("coins") or [])[:10]:
        coin = item.get("item") or item
        events.append({
            "title": f"Trending: {coin.get('name')} ({str(coin.get('symbol', '')).upper()})",
            "type": "trending",
            "score": coin.get("score"),
            "source": "coingecko_free",
        })
    return events


async def coinmarketcal_events(*, limit: int = 20) -> dict[str, Any]:
    key = os.getenv("COINMARKETCAL_API_KEY", "").strip()
    if key:
        official = await _coinmarketcal_official(limit, key)
        if official is not None:
            return official

    # Free fallback: DeFiLlama raises + CoinGecko trending as event proxy
    raises = await _get_json("https://api.llama.fi/raises")
    trending = await _get_json(
        "https://api.coingecko.com/api/v3/search/trending",
    )
    events = _raise_events(raises) + _trending_events(trending)
    return {
        "available": True,
        "source": "free_fallback_composite",
        "events": events[:limit],
        "count": len(events),
        "tier": "free_no_key",
        "note": "Register free key at developers.coinmarketcal.com for official calendar",
        "timestamp": _utcnow(),
    }


async def tracely_address(address: str) -> dict[str, Any] | None:
    addr = safe_url_segment(address)
    data = await _get_json(f"https://tracely.live/api/address/{addr}")
    if not isinstance(data, dict):
        return None
    return data


async def tracely_graph(address: str) -> dict[str, Any] | None:
    addr = safe_url_segment(address)
    data = await _get_json(f"https://tracely.live/api/graph/{addr}")
    if not isinstance(data, dict):
        return None
    return data


async def tracely_portfolio(address: str) -> dict[str, Any] | None:
    addr = safe_url_segment(address)
    data = await _get_json(f"https://tracely.live/api/portfolio/{addr}")
    if not isinstance(data, dict):
        return None
    return data


async def eth_labels(address: str, *, chain_id: int = 1) -> list[dict[str, Any]]:
    addr = safe_url_segment(address)
    data = await _get_json(
        f"https://eth-labels.com/labels/{addr}",
        params={"chainId": chain_id},
    )
    if isinstance(data, list):
        return data
    return []


async def zerion_wallet(address: str) -> dict[str, Any] | None:
    key = os.getenv("ZERION_API_KEY", "").strip()
    if not key:
        return None
    token = base64.b64encode(f"{key}:".encode()).decode()
    addr = safe_url_segment(address)
    data = await _get_json(
        f"https://api.zerion.io/v1/wallets/{addr}/portfolio/",
        headers={"Authorization": f"Basic {token}"},
    )
    if not isinstance(data, dict):
        return None
    return {"source": "zerion", "address": address, "portfolio": data}


async def wallet_balance(address: str) -> dict[str, Any]:
    """DeBank replacement chain: DeBank connector → Zerion key → Tracely portfolio (free)."""
    debank_key = os.getenv("DEBANK_API_KEY", "").strip()
    if debank_key:
        from blackdark.ingestion.debank_connector import fetch_debank_total_balance

        row = await fetch_debank_total_balance(address)
        if row.get("ok"):
            return {
                "available": True,
                "source": "debank",
                "address": address,
                "total_usd": row.get("total_usd"),
                "balance": row.get("raw") or row,
                "tier": "paid_debank",
                "cache_hit": row.get("cache_hit"),
                "stale_fallback": row.get("stale_fallback"),
            }

    zerion = await zerion_wallet(address)
    if zerion:
        attrs = (zerion.get("portfolio") or {}).get("data", {}).get("attributes") or {}
        return {
            "available": True,
            "source": "zerion",
            "address": address,
            "total_usd": attrs.get("total", {}).get("positions"),
            "portfolio": zerion.get("portfolio"),
            "tier": "zerion_free_key",
            "note": "ZERION_API_KEY free tier ~3000 req/day",
        }

    tracely = await tracely_portfolio(address)
    if tracely:
        return {
            "available": True,
            "source": "tracely",
            "address": address,
            "total_usd": tracely.get("total_usd"),
            "chains": tracely.get("chains"),
            "tier": "free_no_key",
            "note": "Free Tracely portfolio (DeBank/Zerion alternative)",
        }

    return {
        "available": False,
        "address": address,
        "reason": "Wallet lookup failed — set ZERION_API_KEY or DEBANK_API_KEY for enhanced coverage",
    }


async def wallet_clusters(address: str) -> dict[str, Any]:
    """Bubblemaps replacement: Tracely graph clusters + optional Bubblemaps key."""
    bubble_key = os.getenv("BUBBLEMAPS_API_KEY", "").strip()
    graph = await tracely_graph(address)
    addr_info = await tracely_address(address)

    nodes = (graph or {}).get("nodes") or []
    edges = (graph or {}).get("edges") or []
    clusters: list[dict[str, Any]] = []
    if nodes:
        clusters.append({
            "cluster_id": f"tracely_{address[:10]}",
            "size": len(nodes),
            "method": "shared_deposit_path",
            "nodes": [
                {"address": n.get("id"), "label": n.get("label"), "type": n.get("type")}
                for n in nodes[:25]
            ],
        })

    return {
        "available": bool(clusters),
        "source": "tracely_free",
        "address": address,
        "clusters": clusters,
        "edge_count": len(edges),
        "center_label": (addr_info or {}).get("address", {}).get("label"),
        "risk_score": (addr_info or {}).get("address", {}).get("risk_score"),
        "bubblemaps_premium": bool(bubble_key),
        "note": "Free Tracely clustering; optional BUBBLEMAPS_API_KEY for commercial map API",
        "reference": "Tracely (free) / Bubblemaps (optional paid)",
        "timestamp": _utcnow(),
    }


async def wallet_labels(address: str) -> dict[str, Any]:
    """Scopescan replacement: Tracely + eth-labels + optional SCOPESCAN key."""
    scope_key = os.getenv("SCOPESCAN_API_KEY", "").strip()
    tracely = await tracely_address(address)
    labels = await eth_labels(address)

    tracely_label = ((tracely or {}).get("address") or {}).get("label")
    merged: list[dict[str, Any]] = []
    if tracely_label:
        merged.append({"label": tracely_label, "source": "tracely", "type": "entity"})
    for row in labels:
        merged.append({
            "label": row.get("nameTag") or row.get("label"),
            "source": "eth-labels",
            "chain_id": row.get("chainId"),
            "type": row.get("label"),
        })

    return {
        "available": bool(merged),
        "source": "tracely_eth_labels",
        "address": address,
        "labels": merged,
        "tracely": tracely,
        "scopescan_premium": bool(scope_key),
        "note": "Free Tracely + eth-labels.com; optional SCOPESCAN_API_KEY for 0xScope depth",
        "timestamp": _utcnow(),
    }


async def cross_chain_flows() -> dict[str, Any]:
    """Blockpour replacement: Blockpour free key → DeFiLlama bridges fallback."""
    key = os.getenv("BLOCKPOUR_API_KEY", "").strip()
    if key:
        health = await _get_json(
            f"{_BLOCKPOUR_BASE}/health-check",
            headers={"Authorization": f"Bearer {key}"},
        )
        stats = await _get_json(
            f"{_BLOCKPOUR_BASE}/stats/networks",
            headers={"Authorization": f"Bearer {key}"},
            params={"days": 1},
        )
        if stats is not None or health is not None:
            return {
                "available": True,
                "source": "blockpour",
                "flows": stats if isinstance(stats, list) else (stats or {}).get("data") or [],
                "tier": "blockpour_free_key",
                "note": "Free token at app.blockpour.com (rate limits apply)",
                "timestamp": _utcnow(),
            }

    bridges = await _get_json("https://api.llama.fi/v2/chains")
    flows: list[dict[str, Any]] = []
    if isinstance(bridges, list):
        ranked = sorted(
            [c for c in bridges if isinstance(c, dict) and float(c.get("tvl") or 0) > 0],
            key=lambda x: float(x.get("tvl") or 0),
            reverse=True,
        )
        for chain in ranked[:20]:
            flows.append({
                "name": chain.get("name"),
                "tvl_usd": chain.get("tvl"),
                "token_symbol": chain.get("tokenSymbol"),
                "source": "defillama_chains_free",
            })
    return {
        "available": bool(flows),
        "source": "defillama_chains_free",
        "flows": flows,
        "tier": "free_no_key",
        "note": "Register free BLOCKPOUR_API_KEY at app.blockpour.com for DEX swap flows; fallback = chain TVL proxy",
        "timestamp": _utcnow(),
    }


async def holder_analytics(asset: str = "BTC") -> dict[str, Any]:
    """IntoTheBlock replacement — ITB API sunset Aug 2025; use CoinGecko + Binance free."""
    from bd_platform.free_market_data import binance_futures_snapshot

    sym = safe_url_segment(asset.upper().replace("USDT", ""))
    coin_id_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
        "XRP": "ripple", "ADA": "cardano", "AVAX": "avalanche-2", "DOT": "polkadot",
        "LINK": "chainlink", "DOGE": "dogecoin",
    }
    mapped = coin_id_map.get(sym)
    if mapped is not None:
        coin_id = mapped  # constant allowlist entry
    else:
        coin_id = sym.lower()
        if not coin_id.isalnum():
            return {"available": False, "asset": sym, "error": "invalid_coin_id"}
    cg = await _get_json(f"https://api.coingecko.com/api/v3/coins/{coin_id}")
    futures = await binance_futures_snapshot(sym)

    md = (cg or {}).get("market_data") or {} if isinstance(cg, dict) else {}
    circ = float(md.get("circulating_supply") or 0)
    total = float(md.get("total_supply") or 0)
    locked_pct = round((total - circ) / total * 100, 2) if total > 0 and circ > 0 else None

    return {
        "available": True,
        "asset": sym,
        "source": "coingecko_binance_free",
        "replacement_for": "intotheblock (API discontinued Aug 2025)",
        "metrics": {
            "price_usd": md.get("current_price"),
            "market_cap_usd": md.get("market_cap"),
            "circulating_supply": circ,
            "total_supply": total,
            "locked_supply_pct": locked_pct,
            "long_short_ratio": futures.get("long_short_ratio"),
            "funding_rate_pct": futures.get("funding_rate_pct"),
            "open_interest_usd": futures.get("open_interest_usd"),
            "taker_buy_sell_ratio": futures.get("taker_buy_sell_ratio"),
        },
        "sentora_research_url": "https://sentora.com/research",
        "timestamp": _utcnow(),
    }
