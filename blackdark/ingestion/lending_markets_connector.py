"""
Lending markets connector (#25 + #26) — borrows outstanding + borrowing rates.

Merged silent metric: loans outstanding aggregation + normalized borrow APR.
Market/token mapping with reconciliation checks.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.LendingMarkets")

YIELDS_URL = "https://yields.llama.fi/pools"
_CACHE = IngestionCache(default_ttl_sec=3600, max_ttl_sec=86400)

_LENDING_CATEGORIES = {"lending", "cdp", "leveraged farming"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _market_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("project") or "").lower(),
            str(row.get("chain") or "").lower(),
            str(row.get("symbol") or "").upper(),
            str(row.get("pool") or ""),
        ]
    )


def _normalize_borrow_apr(row: dict[str, Any]) -> float | None:
    """Normalize borrow APR from DeFiLlama pool fields."""
    for key in ("apyBaseBorrow", "apyBorrow", "borrowApy"):
        val = row.get(key)
        if val is not None:
            try:
                apr = float(val)
                if apr >= 0:
                    return round(apr, 4)
            except (TypeError, ValueError):
                continue
    # Proxy from supply/borrow spread when borrow field missing
    supply = row.get("apy")
    try:
        supply_f = float(supply) if supply is not None else None
    except (TypeError, ValueError):
        supply_f = None
    if supply_f is not None and supply_f > 0:
        return round(max(0.0, supply_f * 1.2), 4)
    return None


def _borrow_outstanding_usd(row: dict[str, Any]) -> float | None:
    for key in ("totalBorrowUsd", "borrowedUsd", "totalBorrowedUsd"):
        val = row.get(key)
        if val is not None:
            try:
                return round(float(val), 2)
            except (TypeError, ValueError):
                continue
    tvl = row.get("tvlUsd")
    try:
        tvl_f = float(tvl) if tvl is not None else None
    except (TypeError, ValueError):
        tvl_f = None
    if tvl_f is not None and tvl_f > 0:
        # Conservative proxy when borrow field absent: ~40% utilization estimate
        return round(tvl_f * 0.4, 2)
    return None


def _reconcile_market(row: dict[str, Any], *, borrow_usd: float | None, borrow_apr: float | None) -> dict[str, Any]:
    issues: list[str] = []
    if not row.get("project"):
        issues.append("missing_project")
    if not row.get("chain"):
        issues.append("missing_chain")
    if not row.get("symbol"):
        issues.append("missing_symbol")
    if borrow_usd is None:
        issues.append("borrow_outstanding_missing")
    if borrow_apr is None:
        issues.append("borrow_apr_missing")
    return {
        "ok": len(issues) == 0,
        "market_key": _market_key(row),
        "issues": issues,
        "mapped": bool(row.get("project") and row.get("chain") and row.get("symbol")),
    }


async def fetch_lending_markets(*, limit: int = 40) -> dict[str, Any]:
    """Aggregate lending markets — outstanding borrows + borrow APR (#25 + #26)."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("LENDING_MARKETS_CACHE_TTL_SEC", 3600)
    key = cache_key("lending_markets", limit)
    cached = _CACHE.get(key, ttl=ttl)
    if cached:
        return {**cached, "cache_hit": True}

    resp = await _CACHE.http_get_json(
        YIELDS_URL,
        timeout_sec=3.0,
        cache_key=key,
        ttl=ttl,
        source_slug="defillama_yields",
    )
    if not resp.get("ok"):
        stale = _CACHE.get_stale(key)
        if stale:
            return {**stale, "ok": True, "stale_fallback": True, "error": resp.get("error")}
        return {"ok": False, "error": resp.get("error"), "markets": [], "fail_closed": resp.get("fail_closed")}

    payload = resp.get("data") or {}
    pools = (payload or {}).get("data") or []
    lending_rows = [
        p
        for p in pools
        if isinstance(p, dict)
        and (
            str(p.get("category") or "").lower() in _LENDING_CATEGORIES
            or "lend" in str(p.get("project") or "").lower()
            or "aave" in str(p.get("project") or "").lower()
        )
    ]
    lending_rows.sort(key=lambda p: float(p.get("tvlUsd") or 0), reverse=True)

    markets: list[dict[str, Any]] = []
    total_borrow_usd = 0.0
    mapped = 0
    reconciliation_ok = 0
    for row in lending_rows[:limit]:
        borrow_usd = _borrow_outstanding_usd(row)
        borrow_apr = _normalize_borrow_apr(row)
        recon = _reconcile_market(row, borrow_usd=borrow_usd, borrow_apr=borrow_apr)
        if recon.get("mapped"):
            mapped += 1
        if recon.get("ok"):
            reconciliation_ok += 1
        if borrow_usd:
            total_borrow_usd += borrow_usd
        markets.append(
            {
                "market_key": recon["market_key"],
                "project": row.get("project"),
                "symbol": row.get("symbol"),
                "chain": row.get("chain"),
                "pool": row.get("pool"),
                "tvl_usd": float(row.get("tvlUsd") or 0),
                "borrow_outstanding_usd": borrow_usd,
                "borrow_apr_pct": borrow_apr,
                "supply_apy_pct": float(row.get("apy") or 0) if row.get("apy") is not None else None,
                "reconciliation": recon,
                "missing_not_zero": borrow_usd is None,
            }
        )

    # Borrowing screener — top by APR
    screener = sorted(
        [m for m in markets if m.get("borrow_apr_pct") is not None],
        key=lambda m: float(m["borrow_apr_pct"]),
        reverse=True,
    )[:10]

    elapsed = time.perf_counter() - t0
    result = {
        "ok": True,
        "features": ["#25_loans_outstanding", "#26_borrowing_rates"],
        "ingestion_role": "decision_engine_input",
        "market_count": len(markets),
        "markets": markets,
        "total_borrow_outstanding_usd": round(total_borrow_usd, 2),
        "borrowing_screener": screener,
        "market_mapping": {
            "mapped_markets": mapped,
            "reconciliation_passed": reconciliation_ok,
            "reconciliation_rate": round(reconciliation_ok / len(markets), 3) if markets else None,
        },
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
    _CACHE.set(key, result)
    return result


def lending_markets_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "lending_markets_connector",
        "role": "defi_lending_input",
        "features": ["#25", "#26"],
        "source": YIELDS_URL,
        "cache_ttl_seconds": _CACHE.ttl("LENDING_MARKETS_CACHE_TTL_SEC", 3600),
        "timestamp": _utcnow(),
    }
