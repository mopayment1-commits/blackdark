"""
Etherscan API connector — on-chain tx/balance ingestion (#50).

NOT a user-facing feature. Silent Data Ingestion Layer for whale wallet intelligence.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from path_safety import safe_url_segment

logger = logging.getLogger("BLACKDARK.EtherscanConnector")

BASE_URL = "https://api.etherscan.io/api"
_CACHE = IngestionCache(default_ttl_sec=3600, max_ttl_sec=86400)

# Known exchange hot-wallet prefixes (partial match for sell-flow heuristics)
_EXCHANGE_HINTS = (
    "binance",
    "coinbase",
    "kraken",
    "okx",
    "okex",
    "huobi",
    "kucoin",
    "gate.io",
    "bybit",
    "bitfinex",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("ETHERSCAN_API_KEY") or "").strip()
    return key or None


def _base_params(**extra: Any) -> dict[str, Any]:
    params: dict[str, Any] = {"apikey": _api_key() or ""}
    params.update(extra)
    return params


async def _etherscan_get(
    *,
    module: str,
    action: str,
    params: dict[str, Any] | None = None,
    cache_key_str: str,
    ttl: int,
) -> dict[str, Any]:
    if not _api_key():
        return {"ok": False, "error": "ETHERSCAN_API_KEY not configured"}
    merged = _base_params(module=module, action=action, **(params or {}))
    return await _CACHE.http_get(
        BASE_URL,
        params=merged,
        timeout_sec=3.0,
        cache_key=cache_key_str,
        ttl=ttl,
    )


def _wei_to_eth(wei: str | int | float) -> float:
    try:
        return float(wei) / 1e18
    except (TypeError, ValueError):
        return 0.0


def _normalize_tx(row: dict[str, Any]) -> dict[str, Any]:
    value_eth = _wei_to_eth(row.get("value") or 0)
    return {
        "hash": row.get("hash"),
        "from": str(row.get("from") or "").lower(),
        "to": str(row.get("to") or "").lower(),
        "value_eth": round(value_eth, 6),
        "value_usd_hint": None,
        "timestamp": int(row.get("timeStamp") or 0),
        "is_error": str(row.get("isError") or "0") == "1",
        "input": (row.get("input") or "0x")[:10],
    }


def _exchange_deposit_score(txs: list[dict[str, Any]]) -> dict[str, Any]:
    """Heuristic whale sell-pressure signal from recent outbound flows."""
    if not txs:
        return {"sell_probability_pct": 0, "signal": "quiet", "exchange_hits": 0}

    outbound = [t for t in txs if t.get("value_eth", 0) > 0.1]
    if not outbound:
        return {"sell_probability_pct": 5, "signal": "quiet", "exchange_hits": 0}

    exchange_hits = 0
    total_eth = 0.0
    exchange_eth = 0.0
    for tx in outbound[:20]:
        eth = float(tx.get("value_eth") or 0)
        total_eth += eth
        to_addr = str(tx.get("to") or "").lower()
        # Etherscan does not label exchanges in tx list — use value heuristics + known patterns
        if eth >= 10:
            exchange_hits += 1
            exchange_eth += eth
        elif any(h in to_addr for h in _EXCHANGE_HINTS):
            exchange_hits += 1
            exchange_eth += eth

    ratio = (exchange_eth / total_eth) if total_eth > 0 else 0
    prob = min(95, max(5, int(ratio * 70 + exchange_hits * 8)))
    signal = "elevated_outflow" if prob >= 55 else "neutral"
    headline = None
    if prob >= 55 and outbound:
        top = max(outbound, key=lambda t: float(t.get("value_eth") or 0))
        headline = (
            f"Whale wallet moved {top.get('value_eth', 0):.2f} ETH "
            f"= {prob}% sell probability (exchange-flow heuristic)"
        )
    return {
        "sell_probability_pct": prob,
        "signal": signal,
        "exchange_hits": exchange_hits,
        "outbound_tx_count": len(outbound),
        "total_outbound_eth": round(total_eth, 4),
        "headline": headline,
    }


async def fetch_eth_balance(address: str) -> dict[str, Any]:
    """Native ETH balance for an address."""
    t0 = time.perf_counter()
    addr = safe_url_segment(address).lower()
    if not addr.startswith("0x") or len(addr) < 10:
        return {"ok": False, "error": "invalid_address", "address": addr}

    ttl = _CACHE.ttl("ETHERSCAN_CACHE_TTL_SEC", 3600)
    key = cache_key("etherscan_balance", addr)
    resp = await _etherscan_get(
        module="account",
        action="balance",
        params={"address": addr, "tag": "latest"},
        cache_key_str=key,
        ttl=ttl,
    )
    if not resp.get("ok"):
        return {"ok": False, "address": addr, "error": resp.get("error")}

    result = (resp.get("data") or {}).get("result")
    balance_eth = _wei_to_eth(result or 0)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "address": addr,
        "balance_eth": round(balance_eth, 6),
        "source": "etherscan",
        "ingestion_role": "onchain_balance",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_eth_transactions(address: str, *, limit: int = 20) -> dict[str, Any]:
    """Recent normal transactions for whale flow analysis."""
    t0 = time.perf_counter()
    addr = safe_url_segment(address).lower()
    if not addr.startswith("0x"):
        return {"ok": False, "error": "invalid_address", "transactions": []}

    ttl = _CACHE.ttl("ETHERSCAN_CACHE_TTL_SEC", 3600)
    key = cache_key("etherscan_txs", addr, limit)
    resp = await _etherscan_get(
        module="account",
        action="txlist",
        params={"address": addr, "startblock": 0, "endblock": 99999999, "sort": "desc"},
        cache_key_str=key,
        ttl=ttl,
    )
    if not resp.get("ok"):
        return {"ok": False, "address": addr, "error": resp.get("error"), "transactions": []}

    raw = (resp.get("data") or {}).get("result") or []
    if not isinstance(raw, list):
        raw = []
    txs = [_normalize_tx(r) for r in raw[:limit] if isinstance(r, dict)]
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "address": addr,
        "transactions": txs,
        "count": len(txs),
        "source": "etherscan",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_whale_flow_signal(address: str) -> dict[str, Any]:
    """
    Whale wallet intelligence — outbound flow heuristics for sell probability.
    Users see the signal headline, not the Etherscan source name.
    """
    t0 = time.perf_counter()
    balance = await fetch_eth_balance(address)
    txs = await fetch_eth_transactions(address, limit=25)
    if not txs.get("ok") and not balance.get("ok"):
        return {
            "ok": False,
            "address": address,
            "error": txs.get("error") or balance.get("error"),
            "data_state": "MISSING",
        }

    flow = _exchange_deposit_score(txs.get("transactions") or [])
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "address": safe_url_segment(address).lower(),
        "balance_eth": balance.get("balance_eth"),
        "flow": flow,
        "headline": flow.get("headline"),
        "sell_probability_pct": flow.get("sell_probability_pct"),
        "signal": flow.get("signal"),
        "ingestion_role": "whale_flow_intelligence",
        "data_state": "LIVE",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_gas_oracle() -> dict[str, Any]:
    """Gas tracker for ingestion health checks."""
    ttl = _CACHE.ttl("ETHERSCAN_CACHE_TTL_SEC", 3600)
    key = cache_key("etherscan_gas")
    resp = await _etherscan_get(
        module="gastracker",
        action="gasoracle",
        cache_key_str=key,
        ttl=ttl,
    )
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error")}
    result = (resp.get("data") or {}).get("result") or {}
    return {
        "ok": True,
        "gas": result,
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
    }


def etherscan_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "etherscan_ingestion_connector",
        "role": "onchain_tx_balance_ingestion",
        "feature": "#50",
        "base_url": BASE_URL,
        "cache_ttl_seconds": _CACHE.ttl("ETHERSCAN_CACHE_TTL_SEC", 3600),
        "api_key_configured": bool(_api_key()),
        "rate_limited": _CACHE.rate_limited(),
        "fallback_chain": ["etherscan_api", "stale_cache"],
        "timestamp": _utcnow(),
    }
