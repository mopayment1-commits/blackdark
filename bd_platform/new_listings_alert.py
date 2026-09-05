"""
New Listings Alert Engine — Feature #114 (Market Radar).

Event alerts for new exchange/DEX listings — NOT buy recommendations.
Sources: exchange symbol registry diff, DexScreener recent pairs, optional CMC.

Example: "Listed on Binance — initial liquidity $2M — Contract Verified"
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.NewListingsAlert")

_REGISTRY_PATH = Path("data/new_listings_registry.jsonl")
_KNOWN_SYMBOLS_PATH = Path("data/exchange_known_symbols.json")
_ALERTS_PATH = Path("data/new_listings_alerts.jsonl")
_CACHE_PATH = Path("data/new_listings_cache.json")

_DISCLAIMER = (
    "New listing alerts are informational events only — not buy recommendations. "
    "Initial liquidity and contract status do not guarantee safety or returns."
)

_MAX_AGE_HOURS = 72
_CACHE_TTL_SEC = 3600


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_known_symbols() -> dict[str, list[str]]:
    if not _KNOWN_SYMBOLS_PATH.exists():
        return {}
    try:
        return json.loads(_KNOWN_SYMBOLS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_known_symbols(data: dict[str, list[str]]) -> None:
    _KNOWN_SYMBOLS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _KNOWN_SYMBOLS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_registry(row: dict[str, Any]) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _REGISTRY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _append_alert(alert: dict[str, Any]) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, default=str) + "\n")


def _cache_get() -> dict[str, Any] | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        if float(blob.get("expires_at", 0)) > time.time():
            return blob.get("payload")
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return None


def _cache_set(payload: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps({"expires_at": time.time() + _CACHE_TTL_SEC, "payload": payload}, indent=2),
        encoding="utf-8",
    )


async def _fetch_binance_symbols(session: aiohttp.ClientSession) -> set[str]:
    try:
        async with session.get("https://api.binance.com/api/v3/exchangeInfo") as resp:
            if resp.status != 200:
                return set()
            data = await resp.json()
            symbols = set()
            for row in data.get("symbols") or []:
                if row.get("status") == "TRADING" and str(row.get("quoteAsset")) == "USDT":
                    symbols.add(str(row.get("baseAsset") or "").upper())
            return {s for s in symbols if s}
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return set()


async def _detect_binance_new_listings(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    current = await _fetch_binance_symbols(session)
    if not current:
        return []

    known = _load_known_symbols()
    prev = set(known.get("binance") or [])
    if not prev:
        known["binance"] = sorted(current)
        _save_known_symbols(known)
        return []

    new_syms = sorted(current - prev)
    known["binance"] = sorted(current)
    _save_known_symbols(known)

    events: list[dict[str, Any]] = []
    for sym in new_syms[:20]:
        event = {
            "event_type": "new_listing",
            "exchange": "binance",
            "symbol": sym,
            "pair": f"{sym}/USDT",
            "headline": f"New listing detected on Binance — {sym}/USDT",
            "liquidity_usd": None,
            "contract_verified": None,
            "source": "exchange_symbol_diff",
            "mode": "event_only",
            "timestamp": _utcnow(),
        }
        events.append(event)
        _append_registry(event)
        _append_alert(event)
    return events


async def _fetch_dexscreener_recent(session: aiohttp.ClientSession, *, limit: int = 15) -> list[dict[str, Any]]:
    """Recent DEX pairs from DexScreener search (high liquidity new tokens)."""
    url = "https://api.dexscreener.com/latest/dex/search?q=USDT"
    headers = {"User-Agent": "BLACKDARK/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        return []

    cutoff = datetime.now(UTC) - timedelta(hours=_MAX_AGE_HOURS)
    events: list[dict[str, Any]] = []
    for row in data.get("pairs") or []:
        created_ms = row.get("pairCreatedAt")
        if not created_ms:
            continue
        try:
            created = datetime.fromtimestamp(int(created_ms) / 1000, tz=UTC)
        except (TypeError, ValueError, OSError):
            continue
        if created < cutoff:
            continue

        liq = float((row.get("liquidity") or {}).get("usd") or 0)
        if liq < 50_000:
            continue

        base = str((row.get("baseToken") or {}).get("symbol") or "").upper()
        dex = str(row.get("dexId") or "dex")
        chain = str(row.get("chainId") or "unknown")
        labels = row.get("labels") or []
        verified = "verified" in [str(x).lower() for x in labels] or bool(row.get("info"))

        event = {
            "event_type": "new_listing",
            "exchange": dex,
            "chain": chain,
            "symbol": base,
            "pair": row.get("pairAddress"),
            "liquidity_usd": round(liq, 0),
            "contract_verified": verified,
            "headline": (
                f"New pair on {dex} ({chain}) — {base} — "
                f"initial liquidity ${liq:,.0f}"
                + (" — Contract Verified" if verified else "")
            ),
            "url": row.get("url"),
            "pair_created_at": created.isoformat(),
            "source": "dexscreener",
            "mode": "event_only",
            "timestamp": _utcnow(),
        }
        events.append(event)
        if len(events) >= limit:
            break

    return events


def enrich_market_radar(payload: dict[str, Any], listings: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["new_listings"] = {
        "enabled": listings.get("ok", False),
        "alert_count": listings.get("alert_count", 0),
        "events": listings.get("events", [])[:5],
        "disclaimer": _DISCLAIMER,
    }
    return out


async def scan_new_listings(*, limit: int = 20) -> dict[str, Any]:
    """Alert engine scan — new listings across CEX + DEX (#114)."""
    t0 = time.perf_counter()
    cached = _cache_get()
    if cached:
        cached = dict(cached)
        cached["cache_hit"] = True
        cached["sla_met"] = (time.perf_counter() - t0) <= 2.0
        return cached

    timeout = aiohttp.ClientTimeout(total=8)
    events: list[dict[str, Any]] = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        cex_events, dex_events = await asyncio.gather(
            _detect_binance_new_listings(session),
            _fetch_dexscreener_recent(session, limit=limit),
        )
        events.extend(cex_events)
        events.extend(dex_events)

    # Deduplicate by symbol+exchange
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for e in events:
        key = f"{e.get('exchange')}:{e.get('symbol')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)
        if len(unique) >= limit:
            break

    for e in unique:
        if e.get("source") == "dexscreener":
            _append_registry(e)
            _append_alert(e)

    out = {
        "ok": True,
        "feature_id": 114,
        "surface": "new_listings_alert",
        "product_name": "New Listings Alert Engine",
        "alert_count": len(unique),
        "events": unique,
        "sources": ["binance_exchange_info", "dexscreener"],
        "disclaimer": _DISCLAIMER,
        "mode": "event_only",
        "market_radar": True,
        "cache_hit": False,
        "cache_ttl_sec": _CACHE_TTL_SEC,
        "timestamp": _utcnow(),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }
    _cache_set(out)
    return out


async def listing_alerts_recent(*, limit: int = 50) -> dict[str, Any]:
    """Read recent alerts from JSONL feed."""
    t0 = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if _ALERTS_PATH.exists():
        try:
            for line in reversed(_ALERTS_PATH.read_text(encoding="utf-8").splitlines()):
                if line.strip():
                    rows.append(json.loads(line))
                if len(rows) >= limit:
                    break
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": True,
        "count": len(rows),
        "alerts": rows,
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }
