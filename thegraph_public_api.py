"""
The Graph Gateway — indexed on-chain queries (free tier ~100k queries/month).

Requires THE_GRAPH_API_KEY from https://thegraph.com/studio/
Used to enrich address intelligence when explorer APIs are thin or as supplemental DEX activity.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

from config import (
    DATA_DIR,
    THE_GRAPH_API_KEY,
    THE_GRAPH_CACHE_TTL_SEC,
    THE_GRAPH_MONTHLY_LIMIT,
    THE_GRAPH_RPS_LIMIT,
)

logger = logging.getLogger("BLACKDARK.TheGraph")

_TIMEOUT = aiohttp.ClientTimeout(total=18)
_HEADERS_BASE = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

_USAGE_PATH = DATA_DIR / "thegraph_api_usage.json"
_CACHE: dict[str, tuple[float, Any]] = {}
_RPS_TIMES: deque[float] = deque(maxlen=THE_GRAPH_RPS_LIMIT * 2)

_EVM_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Decentralized network subgraph deployment IDs (Uniswap V3 — swap history per address).
_SUBGRAPHS: dict[str, dict[str, str]] = {
    "ethereum": {
        "uniswap_v3": "5zvR82QoaXY961y5LRfcTEmziYxhdT6DwpocY45EiY1k",
    },
    "polygon": {
        "uniswap_v3": "EGUjhM83JKMKNBPboePFqAzf45ZBWzvxySKmgVK4bqMC",
    },
    "arbitrum": {
        "uniswap_v3": "FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oFNNbZoq66",
    },
}

_RECENT_SWAPS_QUERY = """
query RecentSwaps($address: Bytes!) {
  swaps(
    first: 5
    orderBy: timestamp
    orderDirection: desc
    where: { or: [{ origin: $address }, { recipient: $address }] }
  ) {
    id
    timestamp
    amountUSD
    token0 { symbol }
    token1 { symbol }
    transaction { id }
  }
}
"""


def supported_chains() -> tuple[str, ...]:
    return tuple(_SUBGRAPHS.keys())


def _utc_month() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def _load_usage() -> dict[str, Any]:
    try:
        if _USAGE_PATH.exists():
            raw = json.loads(_USAGE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"month": _utc_month(), "count": 0}


def _save_usage(row: dict[str, Any]) -> None:
    try:
        _USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _USAGE_PATH.write_text(json.dumps(row), encoding="utf-8")
    except OSError:
        logger.debug("thegraph usage persist failed")


def usage_stats() -> dict[str, Any]:
    row = _load_usage()
    month = _utc_month()
    count = int(row.get("count") or 0) if row.get("month") == month else 0
    return {
        "configured": bool(THE_GRAPH_API_KEY),
        "month_utc": month,
        "queries_this_month": count,
        "monthly_limit": THE_GRAPH_MONTHLY_LIMIT,
        "rps_limit": THE_GRAPH_RPS_LIMIT,
        "remaining_this_month": max(0, THE_GRAPH_MONTHLY_LIMIT - count),
        "chains": list(_SUBGRAPHS.keys()),
        "plan": "free_studio",
    }


def _try_consume_quota() -> bool:
    if not THE_GRAPH_API_KEY:
        return False
    now = time.time()
    while _RPS_TIMES and now - _RPS_TIMES[0] > 1.0:
        _RPS_TIMES.popleft()
    if len(_RPS_TIMES) >= THE_GRAPH_RPS_LIMIT:
        logger.debug("The Graph RPS limit reached")
        return False
    row = _load_usage()
    month = _utc_month()
    if row.get("month") != month:
        row = {"month": month, "count": 0}
    count = int(row.get("count") or 0)
    if count >= THE_GRAPH_MONTHLY_LIMIT:
        logger.warning("The Graph monthly limit reached (%s)", THE_GRAPH_MONTHLY_LIMIT)
        return False
    row["count"] = count + 1
    row["month"] = month
    _save_usage(row)
    _RPS_TIMES.append(now)
    return True


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > THE_GRAPH_CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


def _norm_chain(chain: str) -> str:
    c = (chain or "ethereum").lower().strip()
    if c in {"eth", "mainnet"}:
        return "ethereum"
    return c


def _valid_address(address: str) -> bool:
    return bool(_EVM_ADDR_RE.match((address or "").strip()))


def _gateway_url(subgraph_id: str) -> str:
    return f"https://gateway.thegraph.com/api/{THE_GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"


async def _post_graphql(
    subgraph_id: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not _try_consume_quota():
        return None
    payload = {"query": query, "variables": variables or {}}
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=_HEADERS_BASE) as session:
            async with session.post(_gateway_url(subgraph_id), json=payload) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200:
                    logger.debug("The Graph HTTP %s", resp.status)
                    return None
                if isinstance(body, dict) and body.get("errors"):
                    logger.debug("The Graph GraphQL errors: %s", body.get("errors"))
                    return None
                return body if isinstance(body, dict) else None
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def fetch_recent_dex_swaps(
    address: str,
    *,
    chain: str = "ethereum",
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not _valid_address(address):
        return []
    ch = _norm_chain(chain)
    subgraphs = _SUBGRAPHS.get(ch)
    if not subgraphs:
        return []
    sid = subgraphs.get("uniswap_v3")
    if not sid:
        return []
    addr = address.lower()
    lim = max(1, min(int(limit), 10))
    cache_key = f"swaps:{ch}:{addr}:{lim}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _post_graphql(sid, _RECENT_SWAPS_QUERY, variables={"address": addr})
    if not data:
        return []
    swaps_raw = (data.get("data") or {}).get("swaps")
    if not isinstance(swaps_raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for sw in swaps_raw[:lim]:
        if not isinstance(sw, dict):
            continue
        t0 = sw.get("token0") if isinstance(sw.get("token0"), dict) else {}
        t1 = sw.get("token1") if isinstance(sw.get("token1"), dict) else {}
        tx = sw.get("transaction") if isinstance(sw.get("transaction"), dict) else {}
        rows.append(
            {
                "id": sw.get("id"),
                "timestamp": sw.get("timestamp"),
                "amount_usd": sw.get("amountUSD"),
                "token0_symbol": t0.get("symbol"),
                "token1_symbol": t1.get("symbol"),
                "transaction_hash": tx.get("id"),
            }
        )
    _cache_set(cache_key, rows)
    return rows


async def fetch_address_onchain_enrichment(
    address: str,
    *,
    chain: str = "ethereum",
    swap_limit: int = 5,
) -> dict[str, Any]:
    """Supplemental indexed on-chain data (DEX swaps) when The Graph is configured."""
    stats = usage_stats()
    if not stats["configured"]:
        return {"ok": False, "error": "not_configured", "usage": stats}
    if stats["remaining_this_month"] <= 0:
        return {"ok": False, "error": "monthly_limit_exceeded", "usage": stats}
    ch = _norm_chain(chain)
    if ch not in _SUBGRAPHS:
        return {"ok": False, "error": "unsupported_chain", "chain": ch, "usage": stats}
    swaps = await fetch_recent_dex_swaps(address, chain=ch, limit=swap_limit)
    return {
        "ok": True,
        "source": "the_graph",
        "attribution": "Data: The Graph (Uniswap V3)",
        "chain": ch,
        "recent_dex_swaps": swaps,
        "swap_count": len(swaps),
        "usage": usage_stats(),
    }


async def maybe_enrich_explorer_row(
    row: dict[str, Any],
    address: str,
    *,
    chain: str = "ethereum",
) -> dict[str, Any]:
    """Attach The Graph enrichment to an explorer fallback payload when useful."""
    if not isinstance(row, dict) or not row.get("ok"):
        return row
    need_more = not row.get("recent_transactions") and not row.get("balance")
    thin_txs = isinstance(row.get("recent_transactions"), list) and len(row["recent_transactions"]) < 2
    if not need_more and not thin_txs:
        return row
    enrichment = await fetch_address_onchain_enrichment(address, chain=chain)
    if enrichment.get("ok"):
        row = dict(row)
        row["thegraph_enrichment"] = enrichment
    return row
