"""
Listing Intelligence Engine — Features #114 + #122 + #129 (Market Radar, Sprint 2).

Unified timeline for listing lifecycle:
  Deposit Opened (#122) → Listing Announced (#114) → First Trade

#129 — Opportunity analysis ("what now") layered on #114 detection ("when").
NOT buy recommendations — event intelligence + risk framing only.
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
    "Opportunity analysis (#129) describes liquidity and slippage risk — never profit promises. "
    "Deposit-open signals precede official listings and may reverse. "
    "Verify contracts and liquidity before any action."
)

_LOW_LIQUIDITY_USD = 100_000
_MEDIUM_LIQUIDITY_USD = 500_000

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
                "opportunity_analysis": rows[-1].get("opportunity_analysis"),
            }
        )
    timelines.sort(key=lambda t: t["symbol"])
    return timelines


def analyze_listing_opportunity(
    event: dict[str, Any],
    *,
    opening_price_usd: float | None = None,
    liquidity_usd: float | None = None,
) -> dict[str, Any]:
    """
    #129 — post-listing opportunity framing (what now, not when).

    Example output:
      "Listed. Opening price: $0.01. Liquidity: $50K.
       Analysis: low liquidity — high slippage risk.
       Recommendation: wait 24 hours for stabilization."
    """
    sym = str(event.get("symbol") or "").upper()
    signal = str(event.get("signal") or "")
    liq = float(liquidity_usd if liquidity_usd is not None else event.get("liquidity_usd") or 0)
    price = float(
        opening_price_usd
        if opening_price_usd is not None
        else event.get("opening_price_usd") or event.get("price_usd") or event.get("last_price") or 0
    )

    if signal == "deposit_opened":
        analysis_en = "Pre-listing deposit window — trading not live; liquidity unknown"
        analysis_ar = "نافذة إيداع قبل الإدراج — التداول غير مفعّل؛ السيولة غير معروفة"
        recommendation_en = "Wait for official listing announcement and first-trade liquidity data"
        recommendation_ar = "انتظر إعلان الإدراج الرسمي وبيانات السيولة عند أول صفقة"
        risk_level = "pre_listing"
    elif liq <= 0 and price <= 0:
        analysis_en = "Insufficient market data — cannot assess slippage risk yet"
        analysis_ar = "بيانات سوق غير كافية — لا يمكن تقييم مخاطر slippage بعد"
        recommendation_en = "Wait for liquidity and price discovery before any action"
        recommendation_ar = "انتظر اكتشاف السيولة والسعر قبل أي إجراء"
        risk_level = "unknown"
    elif liq < _LOW_LIQUIDITY_USD:
        analysis_en = "Low liquidity — high slippage risk"
        analysis_ar = "سيولة منخفضة — مخاطر slippage عالية"
        recommendation_en = "Wait 24 hours for price stabilization"
        recommendation_ar = "انتظر 24 ساعة للاستقرار"
        risk_level = "high_slippage"
    elif liq < _MEDIUM_LIQUIDITY_USD:
        analysis_en = "Moderate liquidity — elevated slippage on larger orders"
        analysis_ar = "سيولة متوسطة — slippage مرتفع على الأوامر الكبيرة"
        recommendation_en = "Use small size; monitor depth for 12–24 hours"
        recommendation_ar = "استخدم حجمًا صغيرًا؛ راقب العمق لمدة 12–24 ساعة"
        risk_level = "moderate_slippage"
    else:
        analysis_en = "Adequate liquidity for small orders — volatility risk remains"
        analysis_ar = "سيولة كافية للأوامر الصغيرة — مخاطر التقلب ما زالت قائمة"
        recommendation_en = "Verify contract and exchange status; no profit guarantees"
        recommendation_ar = "تحقق من العقد وحالة المنصة؛ لا ضمانات ربح"
        risk_level = "standard"

    price_str = f"${price:.4f}" if 0 < price < 1 else (f"${price:,.2f}" if price > 0 else "N/A")
    if liq >= 1_000_000:
        liq_str = f"${liq / 1_000_000:.1f}M"
    elif liq > 0:
        liq_str = f"${liq / 1_000:.0f}K"
    else:
        liq_str = "N/A"

    headline_en = (
        f"Listed — {sym}. Opening price: {price_str}. Liquidity: {liq_str}. "
        f"Analysis: {analysis_en}. Recommendation: {recommendation_en}."
    )
    headline_ar = (
        f"تم الإدراج — {sym}. السعر الافتتاحي: {price_str}. السيولة: {liq_str}. "
        f"التحليل: {analysis_ar}. التوصية: {recommendation_ar}."
    )

    return {
        "feature_id": 129,
        "symbol": sym,
        "signal": signal,
        "opening_price_usd": round(price, 8) if price > 0 else None,
        "liquidity_usd": round(liq, 2) if liq > 0 else None,
        "analysis": analysis_en,
        "analysis_ar": analysis_ar,
        "recommendation": recommendation_en,
        "recommendation_ar": recommendation_ar,
        "risk_level": risk_level,
        "headline": headline_en,
        "headline_ar": headline_ar,
        "no_profit_promises": True,
        "mode": "opportunity_analysis",
        "timestamp": _utcnow(),
    }


async def _fetch_cex_opening_price(session: aiohttp.ClientSession, symbol: str) -> float:
    pair = f"{symbol.upper()}USDT"
    try:
        async with session.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": pair},
        ) as resp:
            if resp.status != 200:
                return 0.0
            data = await resp.json()
        return float(data.get("price") or 0)
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError, TypeError):
        return 0.0


async def _enrich_events_with_opportunity(
    session: aiohttp.ClientSession,
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach #129 opportunity analysis to each listing event."""
    enriched: list[dict[str, Any]] = []
    for event in events:
        row = dict(event)
        price = float(row.get("opening_price_usd") or row.get("price_usd") or 0)
        liq = float(row.get("liquidity_usd") or 0)

        if row.get("signal") == "listing_announced" and price <= 0:
            price = await _fetch_cex_opening_price(session, str(row.get("symbol") or ""))
            if price > 0:
                row["opening_price_usd"] = price

        if row.get("signal") == "first_trade" and liq <= 0:
            liq = float(row.get("liquidity_usd") or 0)

        opportunity = analyze_listing_opportunity(row, opening_price_usd=price or None, liquidity_usd=liq or None)
        row["opportunity_analysis"] = opportunity
        row["headline"] = opportunity["headline"]
        row["headline_ar"] = opportunity["headline_ar"]
        enriched.append(row)
    return enriched


async def analyze_listing_opportunity_for_symbol(
    symbol: str,
    *,
    exchange: str = "binance",
    liquidity_usd: float | None = None,
    opening_price_usd: float | None = None,
) -> dict[str, Any]:
    """On-demand #129 analysis for a single symbol."""
    t0 = time.perf_counter()
    sym = symbol.upper().replace("/USDT", "")
    event: dict[str, Any] = {
        "signal": "listing_announced",
        "feature_id": 114,
        "exchange": exchange,
        "symbol": sym,
        "pair": f"{sym}/USDT",
        "liquidity_usd": liquidity_usd,
        "opening_price_usd": opening_price_usd,
    }

    if opening_price_usd is None or opening_price_usd <= 0:
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            fetched = await _fetch_cex_opening_price(session, sym)
            if fetched > 0:
                event["opening_price_usd"] = fetched

    opportunity = analyze_listing_opportunity(event)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "engine": "Listing Intelligence Engine",
        "features": ["#114", "#122", "#129"],
        "symbol": sym,
        "exchange": exchange,
        "opportunity_analysis": opportunity,
        "disclaimer": _DISCLAIMER,
        "no_profit_promises": True,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


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

        seen_pre: set[str] = set()
        unique_pre: list[dict[str, Any]] = []
        for e in events:
            key = f"{e.get('signal')}:{e.get('exchange')}:{e.get('symbol')}"
            if key in seen_pre:
                continue
            seen_pre.add(key)
            unique_pre.append(e)
            if len(unique_pre) >= limit:
                break

        unique = await _enrich_events_with_opportunity(session, unique_pre)

    timelines = _build_timelines(unique)
    elapsed = time.perf_counter() - t0
    out = {
        "ok": True,
        "engine": "Listing Intelligence Engine",
        "features": ["#114", "#122", "#129"],
        "surface": "listing_intelligence",
        "event_count": len(unique),
        "events": unique,
        "timelines": timelines,
        "timeline_template": "Deposit Opened → Listing Announced → First Trade → Opportunity Analysis (#129)",
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
        "opportunity_analyses": [
            e.get("opportunity_analysis")
            for e in listings.get("events", [])
            if e.get("opportunity_analysis")
        ][:5],
        "disclaimer": _DISCLAIMER,
    }
    return out
