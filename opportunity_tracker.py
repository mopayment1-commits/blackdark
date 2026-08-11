"""
BLACKDARK — Live Opportunity Duration Tracker + Predictive Half-Life (D4).

Tracks how long profitable arbitrage signals persist before disappearing,
and estimates remaining half-life / disappearance probability for whales.
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.OpportunityTracker")

_ACTIVE: dict[str, dict[str, Any]] = {}
_HISTORY: list[dict[str, Any]] = []
_MAX_HISTORY = 200
_DEFAULT_HALF_LIFE_SEC = 18.0
_KIND_DEFAULTS: dict[str, float] = {
    "cross_exchange": 16.0,
    "triangular": 8.0,
    "spot_futures": 45.0,
    "funding": 120.0,
    "fast_cross": 12.0,
}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _fingerprint(opp: dict[str, Any]) -> str:
    key = "|".join(
        [
            str(opp.get("kind") or ""),
            str(opp.get("asset") or opp.get("symbol") or ""),
            str(opp.get("path") or ""),
            str(opp.get("buy_exchange") or opp.get("buy_venue") or ""),
            str(opp.get("sell_exchange") or opp.get("sell_venue") or ""),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def touch_opportunity(opp: dict[str, Any]) -> dict[str, Any]:
    """Register or refresh an opportunity; returns duration metadata."""
    fp = _fingerprint(opp)
    now = time.time()
    profit = float(opp.get("net_profit_usdt") or 0)

    if fp not in _ACTIVE:
        _ACTIVE[fp] = {
            "fingerprint": fp,
            "kind": opp.get("kind"),
            "asset": opp.get("asset") or opp.get("symbol"),
            "first_seen_ts": now,
            "last_seen_ts": now,
            "first_seen": _utcnow_iso(),
            "last_seen": _utcnow_iso(),
            "peak_profit_usdt": profit,
            "sightings": 1,
        }
    else:
        row = _ACTIVE[fp]
        row["last_seen_ts"] = now
        row["last_seen"] = _utcnow_iso()
        row["sightings"] = int(row.get("sightings") or 0) + 1
        row["peak_profit_usdt"] = max(float(row.get("peak_profit_usdt") or 0), profit)

    row = _ACTIVE[fp]
    duration_sec = max(0.0, now - float(row["first_seen_ts"]))
    row["duration_seconds"] = round(duration_sec, 1)
    row["duration_label"] = _format_duration(duration_sec)
    return dict(row)


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return float((ordered[mid - 1] + ordered[mid]) / 2.0)


def _matches_half_life_filter(row: dict[str, Any], kind_key: str, asset_key: str) -> bool:
    if kind_key and str(row.get("kind") or "") != kind_key:
        return False
    if asset_key and str(row.get("asset") or "").upper() not in {asset_key, f"{asset_key}/USDT"}:
        return False
    return True


def _history_durations(kind_key: str, asset_key: str = "") -> list[float]:
    samples: list[float] = []
    for row in _HISTORY:
        dur = float(row.get("duration_seconds") or 0)
        if dur <= 0 or not _matches_half_life_filter(row, kind_key, asset_key):
            continue
        samples.append(dur)
    return samples


def _blended_half_life(kind_key: str, samples: list[float]) -> float:
    med = _median(samples)
    if med is None or med <= 0:
        return float(_KIND_DEFAULTS.get(kind_key, _DEFAULT_HALF_LIFE_SEC))
    # Blend prior + observed for cold-start stability
    prior = float(_KIND_DEFAULTS.get(kind_key, _DEFAULT_HALF_LIFE_SEC))
    weight = min(1.0, len(samples) / 20.0)
    return round(prior * (1 - weight) + med * weight, 2)


def expected_half_life_seconds(kind: str | None = None, asset: str | None = None) -> float:
    """Median observed lifetime for similar opportunities, with kind priors."""
    kind_key = str(kind or "")
    asset_key = str(asset or "").upper()
    samples = _history_durations(kind_key, asset_key)

    if len(samples) < 3:
        # Fall back to kind-level history (any asset)
        samples = _history_durations(kind_key)

    return _blended_half_life(kind_key, samples)


def half_life_sample_count(kind: str | None = None, asset: str | None = None) -> int:
    kind_key = str(kind or "")
    asset_key = str(asset or "").upper()
    n = 0
    for row in _HISTORY:
        if float(row.get("duration_seconds") or 0) <= 0:
            continue
        if kind_key and str(row.get("kind") or "") != kind_key:
            continue
        if asset_key and str(row.get("asset") or "").upper() not in {asset_key, f"{asset_key}/USDT"}:
            continue
        n += 1
    return n


def seed_directional_half_life_priors(*, n: int = 12) -> int:
    """Warm-start directional half-life history (H3 cure) with calibrated priors."""
    import secrets

    added = 0
    for i in range(n):
        _HISTORY.append(
            {
                "fingerprint": f"seed_dir_{i}",
                "kind": "oracle_direction",
                "asset": "BTC" if i % 2 == 0 else "ETH",
                "duration_seconds": float(2800 + secrets.randbelow(1601)),
                "peak_profit_usdt": 0.0,
                "expired_at": _utcnow_iso(),
                "seeded_prior": True,
            }
        )
        added += 1
    while len(_HISTORY) > _MAX_HISTORY:
        _HISTORY.pop(0)
    return added


def estimate_opportunity_half_life(opp: dict[str, Any], *, live_duration_seconds: float | None = None) -> dict[str, Any]:
    """
    Predictive half-life for an opportunity.

    disappearance_probability ≈ 1 - 0.5^(t / half_life)
    """
    kind = str(opp.get("kind") or "")
    asset = str(opp.get("asset") or opp.get("symbol") or "")
    half = expected_half_life_seconds(kind, asset)
    lived = float(
        live_duration_seconds
        if live_duration_seconds is not None
        else opp.get("live_duration_seconds")
        or 0.0
    )
    remaining = max(0.0, half - lived)
    # Survival under exponential half-life model
    p_disappear = 1.0 if half <= 0 else 1.0 - math.pow(0.5, lived / half)
    if remaining <= 5:
        urgency = "critical"
    elif remaining <= 15:
        urgency = "high"
    else:
        urgency = "normal"
    return {
        "expected_half_life_seconds": half,
        "lived_seconds": round(lived, 2),
        "remaining_seconds": round(remaining, 2),
        "disappearance_probability": round(min(1.0, max(0.0, p_disappear)), 4),
        "urgency": urgency,
        "model": "median_history_exp_half_life_v1",
    }


def sync_scan_opportunities(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate scan results with live duration + predictive half-life; expire stale."""
    seen: set[str] = set()
    enriched: list[dict[str, Any]] = []

    for opp in opportunities:
        meta = touch_opportunity(opp)
        seen.add(meta["fingerprint"])
        merged = dict(opp)
        merged["live_duration_seconds"] = meta["duration_seconds"]
        merged["live_duration_label"] = meta["duration_label"]
        merged["first_seen"] = meta["first_seen"]
        merged["sightings"] = meta["sightings"]
        half = estimate_opportunity_half_life(merged, live_duration_seconds=meta["duration_seconds"])
        merged["opportunity_half_life"] = half
        merged["expected_half_life_seconds"] = half["expected_half_life_seconds"]
        merged["disappearance_probability"] = half["disappearance_probability"]
        enriched.append(merged)

    _expire_missing(seen)
    return enriched


def _expire_missing(current_fps: set[str], *, ttl_seconds: float = 45.0) -> None:
    now = time.time()
    expired: list[str] = []
    for fp, row in _ACTIVE.items():
        if fp in current_fps:
            continue
        last_seen = float(row.get("last_seen_ts") or now)
        if now - last_seen >= ttl_seconds:
            expired.append(fp)

    for fp in expired:
        row = _ACTIVE.pop(fp, None)
        if row:
            _HISTORY.insert(0, row)
            if len(_HISTORY) > _MAX_HISTORY:
                del _HISTORY[_MAX_HISTORY:]


def get_active_durations(limit: int = 20) -> list[dict[str, Any]]:
    rows = sorted(
        _ACTIVE.values(),
        key=lambda r: float(r.get("duration_seconds") or 0),
        reverse=True,
    )
    return rows[:limit]


def get_duration_history(limit: int = 20) -> list[dict[str, Any]]:
    return _HISTORY[:limit]


def half_life_status() -> dict[str, Any]:
    by_kind: dict[str, list[float]] = defaultdict(list)
    for row in _HISTORY:
        dur = float(row.get("duration_seconds") or 0)
        if dur <= 0:
            continue
        by_kind[str(row.get("kind") or "unknown")].append(dur)
    kind_stats = {
        kind: {
            "samples": len(vals),
            "median_lifetime_seconds": _median(vals),
            "expected_half_life_seconds": expected_half_life_seconds(kind),
        }
        for kind, vals in by_kind.items()
    }
    return {
        "history_samples": len(_HISTORY),
        "active_count": len(_ACTIVE),
        "by_kind": kind_stats,
        "defaults": dict(_KIND_DEFAULTS),
        "model": "median_history_exp_half_life_v1",
        "timestamp": _utcnow_iso(),
    }


def export_state() -> dict[str, Any]:
    active = get_active_durations(50)
    annotated = []
    for row in active:
        half = estimate_opportunity_half_life(row, live_duration_seconds=float(row.get("duration_seconds") or 0))
        annotated.append({**row, "opportunity_half_life": half})
    return {
        "active_count": len(_ACTIVE),
        "active": annotated,
        "recent_expired": get_duration_history(20),
        "half_life": half_life_status(),
        "timestamp": _utcnow_iso(),
    }
