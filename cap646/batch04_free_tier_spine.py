"""Batch04 free-tier Strangler implementations — #168, #171, #186.

Partial BUILD_PHASE_HOLD lift: CoinGecko trending (#171), Santiment free (#168),
Etherscan/BscScan wallet history (#186). No paid vendor subscriptions.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from path_safety import assert_url_path_safe, safe_url_segment

_HEADERS = {"User-Agent": "BLACKDARK-Batch04/1.0", "Accept": "application/json"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _get_json(url: str, *, params: dict[str, Any] | None = None) -> Any:
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        safe_url = assert_url_path_safe(url)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(safe_url, headers=_HEADERS, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def build_trending_coins_171(*, symbol: str) -> dict[str, Any]:
    """#171 — CoinGecko search/trending (free, no API key)."""
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_trending

    trending = await fetch_coingecko_trending()
    coins_raw = trending.get("coins") or []
    trending_coins: list[dict[str, Any]] = []
    for entry in coins_raw[:15]:
        item = entry.get("item") or entry
        sym = str(item.get("symbol") or "").upper()
        if not sym:
            continue
        trending_coins.append(
            {
                "symbol": sym,
                "name": item.get("name"),
                "market_cap_rank": item.get("market_cap_rank"),
                "score": item.get("score"),
            }
        )
    symbols = [c["symbol"] for c in trending_coins]
    requested = symbol.upper()
    return {
        "ok": True,
        "feature_ref": 171,
        "symbol": requested,
        "catalog_goal": "trending_coins",
        "trending_coins": trending_coins,
        "trending_symbols": symbols,
        "requested_symbol_rank": symbols.index(requested) + 1 if requested in symbols else None,
        "source": "coingecko_search_trending",
        "attribution": "Data: CoinGecko (free public API)",
        "free_tier": True,
        "data_freshness": _utcnow(),
    }


async def build_social_dominance_168(*, symbol: str, seed: dict[str, Any]) -> dict[str, Any]:
    """#168 — Santiment free-tier social metrics via ingest_santiment_metrics_142."""
    from bd_platform.data_sources_layer import ingest_santiment_metrics_142

    asset = symbol.upper()
    santiment = ingest_santiment_metrics_142(asset=asset, seed=seed)
    metrics = santiment.get("metrics") or {}
    social_vol = float((metrics.get("social_volume") or {}).get("value") or 0)
    network_growth = float((metrics.get("network_growth") or {}).get("value") or 1.0)
    # Free-tier proxy: dominance_pct = asset social share vs synthetic benchmark (not Glassnode-grade).
    benchmark = max(social_vol * 1.35, 10_000.0)
    dominance_pct = round(min(100.0, (social_vol / benchmark) * 100.0), 2) if benchmark else 0.0
    return {
        "ok": True,
        "feature_ref": 168,
        "symbol": asset,
        "catalog_goal": "social_dominance_intelligence",
        "dominance_pct": dominance_pct,
        "social_volume": social_vol,
        "network_growth": network_growth,
        "metrics": metrics,
        "source": "santiment_free_tier",
        "attribution": "Data: Santiment (free tier — limited accuracy)",
        "free_tier_only": True,
        "accuracy_disclaimer": "Dominance is a free-tier proxy; not equivalent to paid Santiment social dominance.",
        "data_freshness": _utcnow(),
    }


def _scan_config(chain: str) -> tuple[str, str, str]:
    chain_l = (chain or "ethereum").lower()
    if chain_l in {"bsc", "binance-smart-chain", "bnb"}:
        return (
            "https://api.bscscan.com/api",
            os.getenv("BSCSCAN_API_KEY", "").strip() or "YourApiKeyToken",
            "bscscan",
        )
    return (
        "https://api.etherscan.io/api",
        os.getenv("ETHERSCAN_API_KEY", "").strip() or "YourApiKeyToken",
        "etherscan",
    )


async def _scan_account_balance(base: str, api_key: str, address: str) -> float | None:
    data = await _get_json(
        base,
        params={"module": "account", "action": "balance", "address": address, "tag": "latest", "apikey": api_key},
    )
    if not isinstance(data, dict) or data.get("status") != "1":
        return None
    try:
        return int(data.get("result", 0)) / 1e18
    except (TypeError, ValueError):
        return None


async def _scan_txlist(base: str, api_key: str, address: str, *, days: int) -> list[dict[str, Any]]:
    start = int((datetime.now(UTC) - timedelta(days=days)).timestamp())
    data = await _get_json(
        base,
        params={
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 50,
            "sort": "desc",
            "apikey": api_key,
        },
    )
    if not isinstance(data, dict) or data.get("status") != "1":
        return []
    txs = data.get("result") or []
    if not isinstance(txs, list):
        return []
    out: list[dict[str, Any]] = []
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        try:
            ts = int(tx.get("timeStamp", 0))
        except (TypeError, ValueError):
            continue
        if ts < start:
            continue
        value_eth = int(tx.get("value", 0)) / 1e18
        out.append(
            {
                "hash": tx.get("hash"),
                "timestamp": datetime.fromtimestamp(ts, tz=UTC).isoformat(),
                "value_eth": round(value_eth, 8),
                "from": tx.get("from"),
                "to": tx.get("to"),
            }
        )
    return out


async def build_wallet_balance_history_186(
    *,
    symbol: str,
    address: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """#186 — Etherscan/BscScan free account balance + txlist history."""
    t0 = time.perf_counter()
    chain = str(params.get("chain") or params.get("network") or "ethereum")
    raw_addr = (address or params.get("wallet") or "").strip()
    if len(raw_addr) < 10:
        return {
            "ok": False,
            "feature_ref": 186,
            "symbol": symbol,
            "catalog_goal": "historical_wallet_balance_tool",
            "error": "wallet_address_required",
            "wallet_tool_status": "missing_address",
        }
    addr = safe_url_segment(raw_addr)

    base, api_key, source = _scan_config(chain)
    days = max(1, min(90, int(params.get("days") or 30)))
    balance_eth = await _scan_account_balance(base, api_key, addr)
    txs = await _scan_txlist(base, api_key, addr, days=days)

    series: list[dict[str, Any]] = []
    data_source = source
    if balance_eth is not None:
        series.append(
            {
                "timestamp": _utcnow(),
                "balance_eth": round(balance_eth, 8),
                "source": source,
                "proxy": False,
            }
        )
    for tx in txs[:20]:
        series.append(
            {
                "timestamp": tx["timestamp"],
                "balance_eth": tx["value_eth"],
                "tx_hash": tx.get("hash"),
                "source": f"{source}_tx",
                "proxy": False,
            }
        )

    if not series:
        from bd_platform.address_intelligence import balance_history

        fallback = await balance_history(addr, chain=chain, days=days)
        for point in fallback.get("series") or []:
            series.append(
                {
                    "timestamp": point.get("timestamp"),
                    "balance_eth": None,
                    "total_usd": point.get("total_usd"),
                    "source": point.get("source", "address_intelligence"),
                    "proxy": bool(point.get("proxy")),
                }
            )
        if series:
            data_source = "address_intelligence_fallback"
            balance_eth = balance_eth or 0.0

    wallet_status = "live" if balance_eth is not None and txs else ("fallback" if series else "degraded")

    return {
        "ok": bool(series),
        "feature_ref": 186,
        "symbol": symbol.upper(),
        "catalog_goal": "historical_wallet_balance_tool",
        "address": addr,
        "chain": chain.lower(),
        "balance_history": series,
        "current_balance_eth": round(balance_eth, 8) if balance_eth is not None else None,
        "transaction_count": len(txs),
        "wallet_tool_status": wallet_status,
        "source": data_source,
        "attribution": f"Data: {data_source} (Etherscan/BscScan free API with address_intelligence fallback)",
        "free_tier": True,
        "api_key_configured": api_key != "YourApiKeyToken",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "data_freshness": _utcnow(),
    }
