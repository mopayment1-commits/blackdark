"""
On-Chain Intelligence API — Feature #164 (Wave 2, module within Unified API #162).

Read-only versioned endpoints with schema parity to UI address intelligence:
  GET /api/v1/entities/{address}
  GET /api/v1/transactions/{hash}

Auth + rate limits required. No write operations.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from security_auth import require_pro_or_above

logger = logging.getLogger("BLACKDARK.V1OnchainIntelligence")

_FEATURE_ID = 164
_API_VERSION = "v1"
_RATE_WINDOW_SEC = 60
_RATE_MAX_REQUESTS = 120
_rate_buckets: dict[str, list[float]] = defaultdict(list)

onchain_intel_router = APIRouter(tags=["unified-api-onchain-intelligence"])


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _check_rate_limit(user: dict) -> None:
    key = str(user.get("id") or user.get("email") or "anonymous")
    now = time.time()
    bucket = _rate_buckets[key]
    _rate_buckets[key] = [t for t in bucket if now - t < _RATE_WINDOW_SEC]
    if len(_rate_buckets[key]) >= _RATE_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for on-chain intelligence API")
    _rate_buckets[key].append(now)


def _entity_schema(ui_row: dict[str, Any], *, address: str, chain: str) -> dict[str, Any]:
    """Canonical entity schema — must match UI address search fields."""
    return {
        "schema_version": _API_VERSION,
        "feature_id": _FEATURE_ID,
        "type": "entity",
        "address": ui_row.get("address") or address,
        "chain": ui_row.get("chain") or chain.lower(),
        "chain_id": ui_row.get("chain_id"),
        "entity_label": ui_row.get("entity_label"),
        "total_usd": ui_row.get("total_usd"),
        "balance": ui_row.get("balance"),
        "labels": ui_row.get("labels"),
        "clusters": ui_row.get("clusters"),
        "arkham_entity": ui_row.get("arkham_entity"),
        "sources": ui_row.get("sources") or [],
        "data_state": ui_row.get("data_state"),
        "capability": ui_row.get("capability", "address_search"),
        "surface": ui_row.get("surface", "on_chain_address_intelligence"),
        "sla_met": ui_row.get("sla_met"),
        "latency_ms": ui_row.get("latency_ms"),
        "timestamp": ui_row.get("timestamp") or _utcnow(),
    }


def _transaction_schema(decoded: dict[str, Any], *, tx_hash: str, chain: str) -> dict[str, Any]:
    """Canonical transaction schema — aligned with UI transaction decoder."""
    return {
        "schema_version": _API_VERSION,
        "feature_id": _FEATURE_ID,
        "type": "transaction",
        "tx_hash": tx_hash,
        "chain": chain.lower(),
        "decoded": decoded.get("decoded"),
        "source": decoded.get("source"),
        "success": bool(decoded.get("success")),
        "free_tier": decoded.get("free_tier"),
        "data_state": "LIVE" if decoded.get("success") else "PARTIAL",
        "surface": "on_chain_transaction_intelligence",
        "sla_met": decoded.get("sla_met", True),
        "latency_ms": decoded.get("latency_ms"),
        "timestamp": decoded.get("timestamp") or _utcnow(),
    }


@onchain_intel_router.get("/api/v1/entities/{address}")
async def get_entity(
    address: str = Path(..., min_length=10, max_length=128),
    chain: str = Query("ethereum"),
    user: dict = Depends(require_pro_or_above),
):
    """Entity intelligence — schema parity with UI address search (#10)."""
    t0 = time.perf_counter()
    _check_rate_limit(user)

    from bd_platform.address_intelligence import search_address

    ui_row = await search_address(address, chain=chain)
    if not ui_row.get("ok"):
        raise HTTPException(status_code=404, detail=ui_row.get("error") or "entity_not_found")

    elapsed = time.perf_counter() - t0
    entity = _entity_schema(ui_row, address=address, chain=chain)
    entity["sla_met"] = elapsed <= 2.0
    entity["latency_ms"] = round(elapsed * 1000, 1)
    entity["auth"] = {"tier": user.get("tier"), "rate_limit_window_sec": _RATE_WINDOW_SEC}

    return {
        "ok": True,
        "api_version": _API_VERSION,
        "module": "unified_api_onchain_intelligence",
        "read_only": True,
        "data": entity,
    }


@onchain_intel_router.get("/api/v1/transactions/{tx_hash}")
async def get_transaction(
    tx_hash: str = Path(..., min_length=10, max_length=128),
    chain: str = Query("ethereum"),
    user: dict = Depends(require_pro_or_above),
):
    """Transaction intelligence — schema parity with UI transaction decoder."""
    t0 = time.perf_counter()
    _check_rate_limit(user)

    from bd_platform.free_tier_capabilities import transaction_decoder

    decoded = await transaction_decoder(tx_hash=tx_hash, chain=chain)
    elapsed = time.perf_counter() - t0
    decoded["sla_met"] = elapsed <= 2.0
    decoded["latency_ms"] = round(elapsed * 1000, 1)

    if not decoded.get("success") and not decoded.get("decoded"):
        raise HTTPException(status_code=404, detail="transaction_not_found")

    tx = _transaction_schema(decoded, tx_hash=tx_hash, chain=chain)
    tx["sla_met"] = elapsed <= 2.0
    tx["latency_ms"] = round(elapsed * 1000, 1)

    return {
        "ok": True,
        "api_version": _API_VERSION,
        "module": "unified_api_onchain_intelligence",
        "read_only": True,
        "data": tx,
    }


def onchain_intelligence_api_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "api_version": _API_VERSION,
        "module": "unified_api_onchain_intelligence",
        "parent_feature": "#162",
        "endpoints": [
            "GET /api/v1/entities/{address}",
            "GET /api/v1/transactions/{tx_hash}",
        ],
        "read_only": True,
        "auth": "pro_or_above",
        "rate_limit": {"window_sec": _RATE_WINDOW_SEC, "max_requests": _RATE_MAX_REQUESTS},
        "schema_parity": "address_intelligence_ui",
        "timestamp": _utcnow(),
    }
