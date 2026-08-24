"""
Early Stage Token Scanner — Feature #115 (Wave 2).

Filtering tool — NOT prediction. Never use "واعدة/promising".
Filters: Market Cap < $10M, Liquidity Locked > 6mo proxy, Contract Verified,
Holder Distribution Healthy.

Integrates #193 Smart Contract Scanner for security.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.EarlyStageScanner")

_CACHE_PATH = Path("data/early_stage_scanner_cache.json")
_DISCLAIMER = (
    "These are research filtering tools — not investment recommendations. "
    "Early-stage tokens carry extreme risk of total loss. Always verify contracts "
    "independently. Past filter matches do not predict future performance."
)

_MAX_MARKET_CAP_USD = 10_000_000
_MIN_LIQUIDITY_USD = 50_000
_MIN_LOCK_AGE_DAYS = 180
_CACHE_TTL_SEC = 3600


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cache_get(key: str) -> dict[str, Any] | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        row = blob.get(key)
        if row and float(row.get("expires_at", 0)) > time.time():
            return row.get("payload")
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return None


def _cache_set(key: str, payload: dict[str, Any]) -> None:
    blob: dict[str, Any] = {}
    if _CACHE_PATH.exists():
        try:
            blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            blob = {}
    blob[key] = {"expires_at": time.time() + _CACHE_TTL_SEC, "payload": payload}
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _holder_distribution_healthy(pair: dict[str, Any]) -> tuple[bool, str]:
    """Proxy: balanced buy/sell txn flow + adequate liquidity depth."""
    txns = pair.get("txns") or {}
    h24 = txns.get("h24") or {}
    buys = int(h24.get("buys") or 0)
    sells = int(h24.get("sells") or 0)
    total = buys + sells
    if total < 20:
        return False, "insufficient_txn_history"
    ratio = buys / total
    if ratio < 0.25 or ratio > 0.85:
        return False, f"skewed_holder_flow_{ratio:.0%}"
    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    if liq < _MIN_LIQUIDITY_USD:
        return False, "low_liquidity"
    return True, "balanced_flow"


def _liquidity_lock_proxy(pair: dict[str, Any]) -> tuple[bool, str]:
    """
    Proxy for liquidity locked > 6 months:
    - 'locked' in DexScreener labels, OR
    - pair age > 180 days with stable liquidity > $50k
    """
    labels = [str(x).lower() for x in (pair.get("labels") or [])]
    if any("lock" in l for l in labels):
        return True, "label_locked"

    created_ms = pair.get("pairCreatedAt")
    if not created_ms:
        return False, "unknown_lock_status"
    try:
        created = datetime.fromtimestamp(int(created_ms) / 1000, tz=UTC)
    except (TypeError, ValueError, OSError):
        return False, "unknown_lock_status"

    age_days = (datetime.now(UTC) - created).days
    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    if age_days >= _MIN_LOCK_AGE_DAYS and liq >= _MIN_LIQUIDITY_USD:
        return True, f"pair_age_{age_days}d_stable_liquidity"
    return False, f"pair_too_new_{age_days}d"


def _contract_verified(pair: dict[str, Any]) -> bool:
    labels = [str(x).lower() for x in (pair.get("labels") or [])]
    return any("verified" in l for l in labels) or bool(pair.get("info"))


def _evaluate_pair(pair: dict[str, Any]) -> dict[str, Any] | None:
    from bd_platform.smart_contract_scanner import scan_contract_from_pair

    mcap = float(pair.get("marketCap") or pair.get("fdv") or 0)
    if mcap <= 0 or mcap >= _MAX_MARKET_CAP_USD:
        return None

    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    if liq < _MIN_LIQUIDITY_USD:
        return None

    lock_ok, lock_reason = _liquidity_lock_proxy(pair)
    verified = _contract_verified(pair)
    holder_ok, holder_reason = _holder_distribution_healthy(pair)
    security = scan_contract_from_pair(pair)

    if security.get("risk_level") in {"critical", "high"}:
        return None

    filters = {
        "market_cap_under_10m": True,
        "liquidity_locked_6m": lock_ok,
        "contract_verified": verified,
        "holder_distribution_healthy": holder_ok,
    }
    passed = sum(1 for v in filters.values() if v)
    if passed < 3:
        return None

    base = pair.get("baseToken") or {}
    symbol = str(base.get("symbol") or "").upper()

    return {
        "symbol": symbol,
        "contract_address": base.get("address"),
        "chain": pair.get("chainId"),
        "dex": pair.get("dexId"),
        "market_cap_usd": round(mcap, 0),
        "liquidity_usd": round(liq, 0),
        "filters_passed": filters,
        "filters_pass_count": passed,
        "lock_reason": lock_reason,
        "holder_reason": holder_reason,
        "security_scan": {
            "risk_level": security.get("risk_level"),
            "headline": security.get("headline"),
            "contract_verified": security.get("contract_verified"),
        },
        "url": pair.get("url"),
        "mode": "filter_only",
        "headline": (
            f"{symbol} — early stage filter match ({passed}/4 filters) — "
            f"mcap ${mcap:,.0f}, liq ${liq:,.0f}"
        ),
    }


async def _fetch_pairs(session: aiohttp.ClientSession, query: str = "USDT") -> list[dict[str, Any]]:
    url = "https://api.dexscreener.com/latest/dex/search"
    headers = {"User-Agent": "BLACKDARK/1.0"}
    try:
        async with session.get(url, params={"q": query}, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return list(data.get("pairs") or [])
    except (aiohttp.ClientError, TimeoutError):
        return []


async def scan_early_stage_tokens(
    *,
    query: str = "USDT",
    limit: int = 20,
) -> dict[str, Any]:
    """Early Stage Token Scanner — filtering tool (#115)."""
    t0 = time.perf_counter()
    cache_key = f"early_stage:{query}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        cached = dict(cached)
        cached["cache_hit"] = True
        cached["sla_met"] = (time.perf_counter() - t0) <= 2.0
        return cached

    timeout = aiohttp.ClientTimeout(total=6)
    matches: list[dict[str, Any]] = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        pairs = await _fetch_pairs(session, query)

    for pair in pairs:
        row = _evaluate_pair(pair)
        if row:
            matches.append(row)
        if len(matches) >= limit:
            break

    matches.sort(key=lambda x: x.get("filters_pass_count", 0), reverse=True)

    out = {
        "ok": True,
        "feature_id": 115,
        "surface": "early_stage_token_scanner",
        "product_name": "Early Stage Token Scanner",
        "query": query,
        "match_count": len(matches),
        "matches": matches,
        "filters": {
            "market_cap_max_usd": _MAX_MARKET_CAP_USD,
            "liquidity_min_usd": _MIN_LIQUIDITY_USD,
            "liquidity_lock_min_days": _MIN_LOCK_AGE_DAYS,
            "required_filters": [
                "market_cap_under_10m",
                "liquidity_locked_6m",
                "contract_verified",
                "holder_distribution_healthy",
            ],
            "min_pass_count": 3,
        },
        "integrated_features": [193],
        "disclaimer": _DISCLAIMER,
        "mode": "filter_only",
        "market_radar": True,
        "cache_hit": False,
        "timestamp": _utcnow(),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }
    _cache_set(cache_key, out)
    return out


def enrich_market_radar(payload: dict[str, Any], scan: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["early_stage_scanner"] = {
        "enabled": scan.get("ok", False),
        "match_count": scan.get("match_count", 0),
        "top_matches": (scan.get("matches") or [])[:3],
        "disclaimer": _DISCLAIMER,
    }
    return out
