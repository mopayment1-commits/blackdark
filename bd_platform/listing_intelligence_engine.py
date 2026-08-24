"""
Listing Intelligence Engine — Features #114 + #122 (Market Radar, Sprint 2).

Unified timeline for listing lifecycle:
  Deposit Opened (#122) → Listing Announced (#114) → First Trade

NOT buy recommendations — event intelligence for fast traders.
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

logger = logging.getLogger("BLACKDARK.ListingIntelligence")

_REGISTRY_PATH = Path("data/listing_intelligence_registry.jsonl")
_KNOWN_PATH = Path("data/listing_intelligence_known.json")
_ALERTS_PATH = Path("data/listing_intelligence_alerts.jsonl")
_CACHE_PATH = Path("data/listing_intelligence_cache.json")

_DISCLAIMER = (
    "Listing Intelligence events are informational only — not buy recommendations. "
    "Deposit-open signals precede official listings and may reverse. "
    "Verify contracts and liquidity before any action."
)

_CACHE_TTL_SEC = 3600
_MAX_AGE_HOURS = 72


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_known() -> dict[str, Any]:
    if not _KNOWN_PATH.exists():
        return {"binance": {"trading": [], "deposit_only": []}}
    try:
        return json.loads(_KNOWN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"binance": {"trading": [], "deposit_only": []}}


def _save_known(data: dict[str, Any]) -> None:
    _KNOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utcnow()
    _KNOWN_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_registry(row: dict[str, Any]) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _REGISTRY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _append_alert(row: dict[str, Any]) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


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


async def _fetch_binance_symbol_sets(session: aiohttp.ClientSession) -> tuple[set[str], set[str]]:
    """Return (trading_usdt, deposit_enabled_not_trading)."""
    try:
        async with session.get("https://api.binance.com/api/v3/exchangeInfo") as resp:
            if resp.status != 200:
                return set(), set()
            data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return set(), set()

    trading: set[str] = set()
    deposit_only: set[str] = set()
    for row in data.get("symbols") or []:
        if str(row.get("quoteAsset")) != "USDT":
            continue
        base = str(row.get("baseAsset") or "").upper()
        if not base:
            continue
        status = str(row.get("status") or "")
        if status == "TRADING":
            trading.add(base)
        elif status in {"PRE_TRADING", "BREAK"} or (
            row.get("isSpotTradingAllowed") is False and row.get("isMarginTradingAllowed") is False
        ):
            # Deposit may open before trading — proxy via non-TRADING visible symbols
            deposit_only.add(base)
    deposit_only -= trading
    return trading, deposit_only


async def _detect_deposit_opened(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    """#122 — symbols with deposit opened but not yet trading."""
    trading, deposit_only = await _fetch_binance_symbol_sets(session)
    if not trading and not deposit_only:
        return []

    known = _load_known()
    binance_known = known.setdefault("binance", {"trading": [], "deposit_only": []})
    prev_trading = set(binance_known.get("trading") or [])
    prev_deposit = set(binance_known.get("deposit_only") or [])

    if not prev_trading:
        binance_known["trading"] = sorted(trading)
        binance_known["deposit_only"] = sorted(deposit_only)
        _save_known(known)
        return []

    new_deposit = sorted((deposit_only - prev_deposit) - prev_trading)
    new_listings = sorted(trading - prev_trading)

    binance_known["trading"] = sorted(trading)
    binance_known["deposit_only"] = sorted(deposit_only)
    _save_known(known)

    events: list[dict[str, Any]] = []
    for sym in new_deposit[:15]:
        event = {
            "signal": "deposit_opened",
            "feature_id": 122,
            "exchange": "binance",
            "symbol": sym,
            "pair": f"{sym}/USDT",
            "timeline_stage": 1,
            "headline": f"Deposit opened on Binance — {sym}/USDT (trading not live yet)",
            "mode": "event_only",
            "timestamp": _utcnow(),
        }
        events.append(event)
        _append_registry(event)
        _append_alert(event)

    for sym in new_listings[:15]:
        event = {
            "signal": "listing_announced",
            "feature_id": 114,
            "exchange": "binance",
            "symbol": sym,
            "pair": f"{sym}/USDT",
            "timeline_stage": 2,
            "headline": f"Listing announced on Binance — {sym}/USDT now trading",
            "mode": "event_only",
            "timestamp": _utcnow(),
        }
        events.append(event)
        _append_registry(event)
        _append_alert(event)

    return events


async def _fetch_dexscreener_new(session: aiohttp.ClientSession, *, limit: int = 10) -> list[dict[str, Any]]:
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
        verified = "verified" in [str(x).lower() for x in labels]

        event = {
            "signal": "first_trade",
            "feature_id": 114,
            "exchange": dex,
            "chain": chain,
            "symbol": base,
            "liquidity_usd": round(liq, 0),
            "contract_verified": verified,
            "timeline_stage": 3,
            "headline": (
                f"First trade on {dex} ({chain}) — {base} — liquidity ${liq:,.0f}"
                + (" — Contract Verified" if verified else "")
            ),
            "mode": "event_only",
            "timestamp": _utcnow(),
        }
        events.append(event)
        if len(events) >= limit:
            break
    return events


def _build_timelines(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group events by symbol into lifecycle timelines."""
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        sym = str(e.get("symbol") or "").upper()
        if not sym:
            continue
        by_symbol.setdefault(sym, []).append(e)

    timelines: list[dict[str, Any]] = []
    stage_labels = {
        1: "Deposit Opened",
        2: "Listing Announced",
        3: "First Trade",
    }
    for sym, rows in by_symbol.items():
        rows.sort(key=lambda r: int(r.get("timeline_stage") or 99))
        stages_hit = [stage_labels.get(int(r.get("timeline_stage") or 0), r.get("signal", "")) for r in rows]
        timeline_str = " → ".join(dict.fromkeys(stages_hit))
        timelines.append(
            {
                "symbol": sym,
                "exchange": rows[0].get("exchange"),
                "timeline": timeline_str,
                "stages": rows,
                "latest_headline": rows[-1].get("headline"),
            }
        )
    timelines.sort(key=lambda t: t["symbol"])
    return timelines


async def scan_listing_intelligence(*, limit: int = 20) -> dict[str, Any]:
    """Unified listing intelligence scan (#114 + #122)."""
    t0 = time.perf_counter()
    cached = _cache_get()
    if cached:
        out = dict(cached)
        out["cache_hit"] = True
        out["sla_met"] = (time.perf_counter() - t0) <= 2.0
        return out

    timeout = aiohttp.ClientTimeout(total=8)
    events: list[dict[str, Any]] = []
    async with aiohttp.ClientSession(timeout=timeout) as session:
        cex_events, dex_events = await asyncio.gather(
            _detect_deposit_opened(session),
            _fetch_dexscreener_new(session, limit=limit),
        )
        events.extend(cex_events)
        for e in dex_events:
            _append_registry(e)
            _append_alert(e)
        events.extend(dex_events)

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for e in events:
        key = f"{e.get('signal')}:{e.get('exchange')}:{e.get('symbol')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)
        if len(unique) >= limit:
            break

    timelines = _build_timelines(unique)
    elapsed = time.perf_counter() - t0
    out = {
        "ok": True,
        "engine": "Listing Intelligence Engine",
        "features": ["#114", "#122"],
        "surface": "listing_intelligence",
        "event_count": len(unique),
        "events": unique,
        "timelines": timelines,
        "timeline_template": "Deposit Opened → Listing Announced → First Trade",
        "disclaimer": _DISCLAIMER,
        "mode": "event_only",
        "sources": ["binance_exchange_info", "dexscreener"],
        "cache_hit": False,
        "cache_ttl_sec": _CACHE_TTL_SEC,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
    _cache_set(out)
    return out


def enrich_market_radar(payload: dict[str, Any], listings: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["listing_intelligence"] = {
        "enabled": listings.get("ok", False),
        "event_count": listings.get("event_count", 0),
        "timelines": listings.get("timelines", [])[:5],
        "disclaimer": _DISCLAIMER,
    }
    return out
