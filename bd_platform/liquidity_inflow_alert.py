"""
Liquidity Inflow Alert — Feature #116 (On-Chain Alpha, Sprint 2).

On-chain signal alerts — NOT "opportunity" or "فرصة".
Signals:
  1. Trading volume up 3x in 1 hour vs baseline
  2. New active wallets proxy > 100 (txn buys h1)
  3. TVL / liquidity sudden spike vs snapshot

Includes Confidence Score (#149) for Market Radar.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.LiquidityInflow")

_SNAPSHOT_PATH = Path("data/liquidity_inflow_snapshots.jsonl")
_ALERTS_PATH = Path("data/liquidity_inflow_alerts.jsonl")
_CACHE_PATH = Path("data/liquidity_inflow_cache.json")

_DISCLAIMER = (
    "Liquidity Inflow Alerts are on-chain signal observations — not buy recommendations "
    "or profit opportunities. Inflows can reverse quickly. These signals may precede "
    "social media by hours but carry no guarantee of price movement."
)

_VOLUME_SPIKE_MULTIPLIER = 3.0
_MIN_NEW_WALLETS_PROXY = 100
_TVL_SPIKE_PCT = 25.0
_CACHE_TTL_SEC = 300


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _pair_key(pair: dict[str, Any]) -> str:
    chain = str(pair.get("chainId") or "unknown")
    addr = str((pair.get("baseToken") or {}).get("address") or pair.get("pairAddress") or "")
    return f"{chain}:{addr.lower()}"


def _read_last_snapshot(key: str) -> dict[str, Any] | None:
    if not _SNAPSHOT_PATH.exists():
        return None
    last: dict[str, Any] | None = None
    try:
        for line in _SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("key") == key:
                last = row
    except (OSError, json.JSONDecodeError):
        pass
    return last


def _append_snapshot(row: dict[str, Any]) -> None:
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SNAPSHOT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _append_alert(alert: dict[str, Any]) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, default=str) + "\n")


def compute_confidence_score(signals: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Confidence Score (#149) — 0-100 based on signal strength and count.
    """
    if not signals:
        return {"score": 0, "label": "none", "signal_count": 0}

    fired = [s for s in signals if s.get("fired")]
    base = min(100, len(fired) * 30)
    strength_bonus = 0
    for s in fired:
        strength = float(s.get("strength") or 0)
        strength_bonus += min(15, strength * 5)

    score = min(100, int(base + strength_bonus))
    if score >= 75:
        label = "high"
    elif score >= 45:
        label = "medium"
    elif score > 0:
        label = "low"
    else:
        label = "none"

    return {
        "feature_id": 149,
        "score": score,
        "label": label,
        "signal_count": len(fired),
        "signals_fired": [s.get("code") for s in fired],
    }


def _analyze_pair(pair: dict[str, Any]) -> dict[str, Any] | None:
    key = _pair_key(pair)
    base = pair.get("baseToken") or {}
    symbol = str(base.get("symbol") or "").upper()
    if not symbol:
        return None

    volume = pair.get("volume") or {}
    vol_h1 = float(volume.get("h1") or 0)
    vol_h6 = float(volume.get("h6") or 0)
    vol_h24 = float(volume.get("h24") or 0)

    txns = pair.get("txns") or {}
    h1_txns = txns.get("h1") or {}
    h1_buys = int(h1_txns.get("buys") or 0)

    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    prev = _read_last_snapshot(key)
    prev_liq = float(prev.get("liquidity_usd") or 0) if prev else 0

    baseline_h1 = vol_h6 / 6.0 if vol_h6 > 0 else vol_h24 / 24.0 if vol_h24 > 0 else 0
    vol_spike = vol_h1 >= baseline_h1 * _VOLUME_SPIKE_MULTIPLIER if baseline_h1 > 0 else False
    vol_ratio = round(vol_h1 / baseline_h1, 2) if baseline_h1 > 0 else 0

    wallet_surge = h1_buys >= _MIN_NEW_WALLETS_PROXY
    tvl_spike = False
    tvl_spike_pct = 0.0
    if prev_liq > 0 and liq > 0:
        tvl_spike_pct = (liq - prev_liq) / prev_liq * 100.0
        tvl_spike = tvl_spike_pct >= _TVL_SPIKE_PCT

    signals = [
        {
            "code": "VOLUME_3X_1H",
            "fired": vol_spike,
            "strength": min(3.0, vol_ratio / _VOLUME_SPIKE_MULTIPLIER) if vol_spike else 0,
            "message": f"Volume {vol_ratio:.1f}x vs 1h baseline" if vol_spike else "Volume normal",
            "value": vol_ratio,
        },
        {
            "code": "NEW_WALLETS_100",
            "fired": wallet_surge,
            "strength": min(2.0, h1_buys / _MIN_NEW_WALLETS_PROXY) if wallet_surge else 0,
            "message": f"{h1_buys} buy txns in 1h (wallet activity proxy)" if wallet_surge else f"{h1_buys} buy txns in 1h",
            "value": h1_buys,
        },
        {
            "code": "TVL_SPIKE",
            "fired": tvl_spike,
            "strength": min(2.5, tvl_spike_pct / _TVL_SPIKE_PCT) if tvl_spike else 0,
            "message": f"Liquidity +{tvl_spike_pct:.0f}% vs prior snapshot" if tvl_spike else "Liquidity stable",
            "value": round(tvl_spike_pct, 1),
        },
    ]

    fired_count = sum(1 for s in signals if s["fired"])
    if fired_count == 0:
        _append_snapshot({
            "key": key,
            "symbol": symbol,
            "liquidity_usd": liq,
            "volume_h1": vol_h1,
            "timestamp": _utcnow(),
        })
        return None

    confidence = compute_confidence_score(signals)

    alert = {
        "event_type": "liquidity_inflow",
        "symbol": symbol,
        "chain": pair.get("chainId"),
        "dex": pair.get("dexId"),
        "liquidity_usd": round(liq, 0),
        "signals": signals,
        "signals_fired_count": fired_count,
        "confidence_score": confidence,
        "headline": (
            f"Liquidity Inflow Alert — {symbol}: "
            f"{fired_count} on-chain signal(s), confidence {confidence['score']}/100"
        ),
        "url": pair.get("url"),
        "mode": "alert_only",
        "timestamp": _utcnow(),
    }

    _append_snapshot({
        "key": key,
        "symbol": symbol,
        "liquidity_usd": liq,
        "volume_h1": vol_h1,
        "timestamp": _utcnow(),
    })
    _append_alert(alert)
    return alert


async def _fetch_trending_pairs(session: aiohttp.ClientSession) -> list[dict[str, Any]]:
    """Fetch pairs with recent activity from DexScreener."""
    url = "https://api.dexscreener.com/latest/dex/search"
    headers = {"User-Agent": "BLACKDARK/1.0"}
    pairs: list[dict[str, Any]] = []
    for q in ("SOL USDT", "ETH USDT", "BTC USDT"):
        try:
            async with session.get(url, params={"q": q}, headers=headers) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                pairs.extend(data.get("pairs") or [])
        except (aiohttp.ClientError, TimeoutError):
            continue
    return pairs


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


async def scan_liquidity_inflow(*, limit: int = 15) -> dict[str, Any]:
    """Liquidity Inflow Alert scan (#116 + #149 confidence)."""
    t0 = time.perf_counter()
    cached = _cache_get()
    if cached:
        cached = dict(cached)
        cached["cache_hit"] = True
        cached["sla_met"] = (time.perf_counter() - t0) <= 2.0
        return cached

    timeout = aiohttp.ClientTimeout(total=6)
    alerts: list[dict[str, Any]] = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        pairs = await _fetch_trending_pairs(session)

    seen: set[str] = set()
    for pair in pairs:
        key = _pair_key(pair)
        if key in seen:
            continue
        seen.add(key)
        liq = float((pair.get("liquidity") or {}).get("usd") or 0)
        if liq < 30_000:
            continue
        alert = _analyze_pair(pair)
        if alert:
            alerts.append(alert)
        if len(alerts) >= limit:
            break

    alerts.sort(key=lambda a: a.get("confidence_score", {}).get("score", 0), reverse=True)

    out = {
        "ok": True,
        "feature_id": 116,
        "surface": "liquidity_inflow_alert",
        "product_name": "Liquidity Inflow Alert",
        "alert_count": len(alerts),
        "alerts": alerts,
        "signals_monitored": ["VOLUME_3X_1H", "NEW_WALLETS_100", "TVL_SPIKE"],
        "confidence_score_feature": 149,
        "disclaimer": _DISCLAIMER,
        "mode": "alert_only",
        "market_radar": True,
        "cache_hit": False,
        "timestamp": _utcnow(),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }
    _cache_set(out)
    return out


def enrich_market_radar(payload: dict[str, Any], inflow: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["liquidity_inflow"] = {
        "enabled": inflow.get("ok", False),
        "alert_count": inflow.get("alert_count", 0),
        "alerts": (inflow.get("alerts") or [])[:5],
        "disclaimer": _DISCLAIMER,
    }
    return out
