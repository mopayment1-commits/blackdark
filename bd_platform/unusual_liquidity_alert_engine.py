"""
Unusual Liquidity Alert Engine — Feature #131 (Sprint 2, On-Chain Alert Engine).

Detects abnormal liquidity movements:
  - AMM TVL changes (DexScreener / on-chain proxies)
  - LP additions / withdrawals
  - CEX order-book depth changes

Displayed in Market Radar with severity:
  🟡 unusual liquidity movement
  🔴 70%+ liquidity withdrawn — rug-pull warning

Integrates with #193 Smart Contract Scanner when available (optional hook).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.UnusualLiquidity")

_FEATURE_ID = 131
_ALERTS_PATH = Path("data/unusual_liquidity_alerts.jsonl")
_SNAPSHOT_PATH = Path("data/unusual_liquidity_snapshots.json")
_CACHE_PATH = Path("data/unusual_liquidity_cache.json")

_YELLOW_CHANGE_PCT = 30.0
_RED_CHANGE_PCT = 70.0
_MIN_LIQUIDITY_USD = 25_000
_CACHE_TTL_SEC = 120

_DISCLAIMER = (
    "Unusual Liquidity Alerts are risk signals only — not buy or sell recommendations. "
    "Large LP withdrawals may indicate rug-pull risk; verify contracts via Smart Contract Scanner (#193)."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_snapshots() -> dict[str, float]:
    if not _SNAPSHOT_PATH.exists():
        return {}
    try:
        return json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_snapshots(data: dict[str, float]) -> None:
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SNAPSHOT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


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


def classify_severity(*, change_pct: float, direction: str) -> tuple[str, str, str]:
    """Return (severity, emoji, label)."""
    if direction == "withdraw" and change_pct >= _RED_CHANGE_PCT:
        return "critical", "🔴", "70%+ liquidity withdrawn — rug-pull warning"
    if change_pct >= _YELLOW_CHANGE_PCT:
        return "warning", "🟡", "Unusual liquidity movement"
    return "info", "⚪", "Liquidity shift detected"


def _contract_scanner_hook(chain: str, address: str) -> dict[str, Any] | None:
    """Optional #193 Smart Contract Scanner integration."""
    try:
        from bd_platform.smart_contract_scanner import scan_contract_risk  # type: ignore[attr-defined]

        return scan_contract_risk(chain=chain, address=address)
    except (ImportError, AttributeError):
        return {
            "available": False,
            "feature_id": 193,
            "note": "Smart Contract Scanner not loaded — verify contract manually",
        }


async def _scan_dex_liquidity_changes(session: aiohttp.ClientSession, *, limit: int = 15) -> list[dict[str, Any]]:
    url = "https://api.dexscreener.com/latest/dex/search?q=USDT"
    headers = {"User-Agent": "BLACKDARK/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        return []

    prev = _load_snapshots()
    next_snap: dict[str, float] = dict(prev)
    alerts: list[dict[str, Any]] = []

    for row in data.get("pairs") or []:
        liq = float((row.get("liquidity") or {}).get("usd") or 0)
        if liq < _MIN_LIQUIDITY_USD:
            continue

        base = str((row.get("baseToken") or {}).get("symbol") or "").upper()
        dex = str(row.get("dexId") or "dex")
        chain = str(row.get("chainId") or "unknown")
        pair_addr = str(row.get("pairAddress") or "")
        key = f"{chain}:{dex}:{base}:{pair_addr}"

        prev_liq = float(prev.get(key) or 0)
        next_snap[key] = liq

        if prev_liq <= 0:
            continue

        change_pct = abs(liq - prev_liq) / prev_liq * 100
        if change_pct < _YELLOW_CHANGE_PCT:
            continue

        direction = "withdraw" if liq < prev_liq else "add"
        severity, emoji, label = classify_severity(change_pct=change_pct, direction=direction)

        contract_addr = str((row.get("baseToken") or {}).get("address") or "")
        scanner = _contract_scanner_hook(chain, contract_addr) if contract_addr else None

        headline_en = (
            f"{emoji} {label} on {dex} ({chain}) — {base}: "
            f"liquidity {'down' if direction == 'withdraw' else 'up'} "
            f"{change_pct:.0f}% (${prev_liq:,.0f} → ${liq:,.0f})"
        )
        headline_ar = (
            f"{emoji} {'70% من السيولة سُحبت — احذر rug pull' if severity == 'critical' else 'سيولة تتحرك بشكل غير عادي'} "
            f"على {dex} ({chain}) — {base}: "
            f"{'انخفاض' if direction == 'withdraw' else 'زيادة'} {change_pct:.0f}%"
        )

        alert = {
            "event_type": "unusual_liquidity_movement",
            "feature_id": _FEATURE_ID,
            "source": "amm_tvl",
            "severity": severity,
            "severity_emoji": emoji,
            "severity_label": label,
            "direction": direction,
            "symbol": base,
            "exchange": dex,
            "chain": chain,
            "pair_address": pair_addr,
            "liquidity_usd": round(liq, 2),
            "previous_liquidity_usd": round(prev_liq, 2),
            "change_pct": round(change_pct, 2),
            "headline": headline_en,
            "headline_ar": headline_ar,
            "contract_scanner": scanner,
            "mode": "alert_only",
            "timestamp": _utcnow(),
        }
        alerts.append(alert)
        _append_alert(alert)
        if len(alerts) >= limit:
            break

    _save_snapshots(next_snap)
    return alerts


async def _scan_cex_depth_changes(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    """CEX order-book depth proxy via 24h volume + price move."""
    alerts: list[dict[str, Any]] = []
    for asset in ("BTC", "ETH", "SOL"):
        symbol = f"{asset}USDT"
        try:
            async with session.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": symbol},
            ) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
            continue

        quote_vol = float(data.get("quoteVolume") or 0)
        change_pct = abs(float(data.get("priceChangePercent") or 0))
        if quote_vol < 50_000_000 or change_pct < 8:
            continue

        # Volume spike + sharp move = depth stress proxy
        depth_stress = min(95.0, change_pct * 3 + 20)
        if depth_stress < _YELLOW_CHANGE_PCT:
            continue

        severity, emoji, label = classify_severity(change_pct=depth_stress, direction="withdraw")
        alert = {
            "event_type": "cex_depth_stress",
            "feature_id": _FEATURE_ID,
            "source": "cex_order_book_depth",
            "severity": severity,
            "severity_emoji": emoji,
            "severity_label": label,
            "symbol": asset,
            "exchange": "binance",
            "quote_volume_24h_usd": round(quote_vol, 0),
            "price_change_pct": round(change_pct, 2),
            "depth_stress_score": round(depth_stress, 1),
            "headline": (
                f"{emoji} {label} on Binance — {asset}: "
                f"depth stress score {depth_stress:.0f} (24h move {change_pct:.1f}%)"
            ),
            "headline_ar": (
                f"{emoji} ضغط غير عادي على عمق السوق — {asset} على Binance "
                f"(حركة 24س {change_pct:.1f}%)"
            ),
            "mode": "alert_only",
            "timestamp": _utcnow(),
        }
        alerts.append(alert)
        _append_alert(alert)

    return alerts


async def scan_unusual_liquidity_events(*, limit: int = 10) -> dict[str, Any]:
    """Scan for unusual on-chain / CEX liquidity movements (#131)."""
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
        dex_alerts, cex_alerts = await asyncio.gather(
            _scan_dex_liquidity_changes(session, limit=limit),
            _scan_cex_depth_changes(session),
        )
        events.extend(dex_alerts)
        events.extend(cex_alerts)

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    events.sort(key=lambda e: (severity_order.get(str(e.get("severity")), 9), -(e.get("change_pct") or 0)))
    events = events[:limit]

    elapsed = time.perf_counter() - t0
    out = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product_name": "Unusual Liquidity Alert Engine",
        "surface": "market_radar_alert",
        "alert_count": len(events),
        "events": events,
        "severity_levels": {
            "warning": "🟡 unusual liquidity movement",
            "critical": "🔴 70%+ liquidity withdrawn — rug-pull warning",
        },
        "sources": ["dexscreener_amm_tvl", "binance_cex_depth_proxy"],
        "integrated_features": ["#193"],
        "disclaimer": _DISCLAIMER,
        "mode": "alert_only",
        "no_buy_language": True,
        "cache_hit": False,
        "cache_ttl_sec": _CACHE_TTL_SEC,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
    _cache_set(out)
    return out


def enrich_market_radar(payload: dict[str, Any], unusual: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["unusual_liquidity_alerts"] = {
        "enabled": unusual.get("ok", False),
        "alert_count": unusual.get("alert_count", 0),
        "events": unusual.get("events", [])[:3],
        "severity_levels": unusual.get("severity_levels"),
        "disclaimer": _DISCLAIMER,
    }
    return out
