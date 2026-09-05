"""
Tronscan connector (#103) — via Unified Connector Layer (#194).

Normalizes Tron data to canonical cross-chain schema. NOT a branded user surface.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.canonical.cross_chain_schema import NormalizedAssetBalance, normalize_tron_tx
from blackdark.ingestion.connector_cache import cache_key
from blackdark.ingestion.unified_connector import UnifiedConnector

logger = logging.getLogger("BLACKDARK.Tronscan")

API_BASE = "https://apilist.tronscanapi.com/api"
_CONNECTOR = UnifiedConnector(source_slug="tronscan")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("TRONSCAN_API_KEY") or os.getenv("TRON_PRO_API_KEY") or "").strip()
    return key or None


def _headers() -> dict[str, str]:
    headers = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
    key = _api_key()
    if key:
        headers["TRON-PRO-API-KEY"] = key
    return headers


async def _fallback_account(address: str) -> dict[str, Any]:
    """Public TronGrid fallback when Tronscan is rate-limited or blocked."""
    from blackdark.ingestion.unified_connector import UnifiedConnector

    grid = UnifiedConnector(source_slug="tron_grid")
    resp = await grid.get_json(
        "https://api.trongrid.io/v1/accounts/" + address,
        headers={"Accept": "application/json"},
        timeout_sec=3.0,
        cache_parts=("account", address),
        ttl=300,
    )
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error")}
    data = resp.get("data") or {}
    rows = (data.get("data") or []) if isinstance(data, dict) else []
    row = rows[0] if rows else {}
    balance_sun = 0
    if isinstance(row, dict):
        balance_sun = int((row.get("balance") or 0))
    return {
        "ok": True,
        "address": address,
        "balance_trx": round(balance_sun / 1e6, 6),
        "source": "trongrid_fallback",
        "fallback": True,
    }


async def fetch_tron_account(address: str) -> dict[str, Any]:
    """Normalized Tron account balance."""
    t0 = time.perf_counter()
    addr = (address or "").strip()
    if not addr.startswith("T") or len(addr) < 30:
        return {"ok": False, "error": "invalid_tron_address", "address": addr}

    ttl = _CONNECTOR.ttl("TRONSCAN_CACHE_TTL_SEC", 600)
    resp = await _CONNECTOR.get_json(
        f"{API_BASE}/account",
        params={"address": addr},
        headers=_headers(),
        cache_parts=("account", addr),
        ttl=ttl,
    )
    if not resp.get("ok"):
        fb = await _fallback_account(addr)
        if fb.get("ok"):
            asset = NormalizedAssetBalance(
                chain="tron",
                chain_id="tron",
                address=addr,
                symbol="TRX",
                balance=float(fb.get("balance_trx") or 0),
                balance_usd=None,
                source=str(fb.get("source")),
            )
            return {
                "ok": True,
                "feature": "#103",
                "address": addr,
                "assets": [asset.to_dict()],
                "fallback": True,
                "data_state": "DEGRADED",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                "timestamp": _utcnow(),
            }
        return {"ok": False, "error": resp.get("error"), "address": addr}

    data = resp.get("data") or {}
    balance_trx = float(data.get("balance") or 0) / 1e6 if data.get("balance") else 0.0
    assets = [
        NormalizedAssetBalance(
            chain="tron",
            chain_id="tron",
            address=addr,
            symbol="TRX",
            balance=round(balance_trx, 6),
            balance_usd=None,
            source="tronscan",
        ).to_dict()
    ]
    for token in (data.get("trc20token_balances") or [])[:20]:
        if not isinstance(token, dict):
            continue
        try:
            bal = float(token.get("balance") or 0)
            decimals = int(token.get("tokenDecimal") or token.get("decimals") or 6)
            bal = bal / (10**decimals) if decimals else bal
        except (TypeError, ValueError):
            bal = 0.0
        assets.append(
            NormalizedAssetBalance(
                chain="tron",
                chain_id="tron",
                address=addr,
                symbol=str(token.get("tokenAbbr") or token.get("tokenName") or "TRC20"),
                balance=round(bal, 8),
                balance_usd=None,
                source="tronscan",
            ).to_dict()
        )

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#103",
        "address": addr,
        "assets": assets,
        "asset_count": len(assets),
        "data_state": "LIVE",
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_tron_transactions(address: str, *, limit: int = 50, start: int = 0) -> dict[str, Any]:
    """Normalized Tron transactions for cross-chain index."""
    t0 = time.perf_counter()
    addr = (address or "").strip()
    if not addr.startswith("T"):
        return {"ok": False, "error": "invalid_tron_address", "transactions": []}

    ttl = _CONNECTOR.ttl("TRONSCAN_CACHE_TTL_SEC", 600)
    resp = await _CONNECTOR.get_json(
        f"{API_BASE}/transaction",
        params={
            "address": addr,
            "sort": "-timestamp",
            "count": "true",
            "limit": min(50, limit),
            "start": max(0, start),
        },
        headers=_headers(),
        cache_parts=("txs", addr, limit, start),
        ttl=ttl,
    )
    if not resp.get("ok"):
        stale = _CONNECTOR.cache.get_stale(cache_key("tronscan", "txs", addr, limit, start))
        if stale:
            return {**stale, "ok": True, "stale_fallback": True}
        return {"ok": False, "error": resp.get("error"), "transactions": [], "fail_closed": resp.get("fail_closed")}

    payload = resp.get("data") or {}
    raw_rows = payload.get("data") or []
    txs: list[dict[str, Any]] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        norm = normalize_tron_tx(row, source="tronscan")
        if norm:
            txs.append(norm.to_dict())

    elapsed = time.perf_counter() - t0
    total = int(payload.get("total") or len(txs))
    return {
        "ok": True,
        "feature": "#103",
        "chain": "tron",
        "address": addr,
        "transactions": txs,
        "count": len(txs),
        "total_available": total,
        "pagination": {
            "start": start,
            "limit": limit,
            "has_more": (start + len(txs)) < total,
            "next_start": start + len(txs) if (start + len(txs)) < total else None,
        },
        "data_state": "LIVE",
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


def tronscan_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "tronscan_ingestion_connector",
        "role": "cross_chain_onchain_input",
        "feature": "#103",
        "unified_connector": "#194",
        "api_key_configured": bool(_api_key()),
        "circuit_open": is_open("tronscan"),
        "fallback_chain": ["tronscan", "trongrid", "stale_cache"],
        "cache_ttl_seconds": _CONNECTOR.ttl("TRONSCAN_CACHE_TTL_SEC", 600),
        "timestamp": _utcnow(),
    }
