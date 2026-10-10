"""
DeBank Open API connector — wallet/portfolio ingestion (#46).

NOT a user-facing feature. Silent Data Ingestion Layer source for Portfolio AI depth.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from path_safety import safe_url_segment

logger = logging.getLogger("BLACKDARK.DeBankConnector")

BASE_URL = "https://pro-openapi.debank.com/v1"
_CACHE = IngestionCache(default_ttl_sec=3600, max_ttl_sec=86400)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _api_key() -> str | None:
    key = (os.getenv("DEBANK_API_KEY") or "").strip()
    return key or None


def _headers() -> dict[str, str]:
    key = _api_key()
    headers: dict[str, str] = {}
    if key:
        headers["AccessKey"] = key
    return headers


def _normalize_balance(address: str, raw: dict[str, Any]) -> dict[str, Any]:
    total_usd = float(raw.get("total_usd") or raw.get("usd_value") or 0)
    chains = raw.get("chain_list") or raw.get("chains") or []
    return {
        "address": address,
        "total_usd": round(total_usd, 2),
        "chain_count": len(chains) if isinstance(chains, list) else 0,
        "chains": chains[:20] if isinstance(chains, list) else [],
        "raw": raw,
    }


async def fetch_debank_total_balance(address: str) -> dict[str, Any]:
    """Normalized multi-chain wallet balance — primary DeBank ingestion entrypoint."""
    t0 = time.perf_counter()
    addr = safe_url_segment(address)
    if len(addr) < 10:
        return {"ok": False, "error": "invalid_address", "address": addr}

    if not _api_key():
        return {"ok": False, "error": "DEBANK_API_KEY not configured", "address": addr}

    ttl = _CACHE.ttl("DEBANK_CACHE_TTL_SEC", 3600)
    key = cache_key("debank_balance", addr)
    resp = await _CACHE.http_get(
        f"{BASE_URL}/user/total_balance",
        params={"id": addr},
        headers=_headers(),
        timeout_sec=3.0,
        cache_key=key,
        ttl=ttl,
    )
    if not resp.get("ok"):
        return {
            "ok": False,
            "address": addr,
            "error": resp.get("error"),
            "rate_limited": resp.get("rate_limited"),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }

    raw = resp.get("data") or {}
    if not isinstance(raw, dict):
        return {"ok": False, "address": addr, "error": "invalid_response"}

    normalized = _normalize_balance(addr, raw)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "address": addr,
        "source": "debank",
        "ingestion_role": "wallet_portfolio",
        **normalized,
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "rate_limited": resp.get("rate_limited"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def fetch_debank_token_list(address: str) -> dict[str, Any]:
    """Token holdings list for portfolio depth."""
    addr = safe_url_segment(address)
    if not _api_key():
        return {"ok": False, "error": "DEBANK_API_KEY not configured"}

    ttl = _CACHE.ttl("DEBANK_CACHE_TTL_SEC", 3600)
    key = cache_key("debank_tokens", addr)
    resp = await _CACHE.http_get(
        f"{BASE_URL}/user/all_token_list",
        params={"id": addr, "is_all": "true"},
        headers=_headers(),
        timeout_sec=3.0,
        cache_key=key,
        ttl=ttl,
    )
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error"), "tokens": []}

    tokens = resp.get("data") or []
    if not isinstance(tokens, list):
        tokens = []
    return {
        "ok": True,
        "address": addr,
        "token_count": len(tokens),
        "tokens": tokens[:100],
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
    }


def debank_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "debank_ingestion_connector",
        "role": "wallet_portfolio_ingestion",
        "feature": "#46",
        "base_url": BASE_URL,
        "cache_ttl_seconds": _CACHE.ttl("DEBANK_CACHE_TTL_SEC", 3600),
        "api_key_configured": bool(_api_key()),
        "rate_limited": _CACHE.rate_limited(),
        "fallback_chain": ["debank_api", "stale_cache", "zerion", "tracely"],
        "timestamp": _utcnow(),
    }
