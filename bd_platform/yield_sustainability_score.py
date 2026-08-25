"""
Yield Sustainability Score — Feature #709 merged with #198 (Sprint 2).

Yield history with time-series stability, outlier detection,
and incentive/fee decomposition. NOT a standalone yield tracker.

#710 Yield Arbitrage lives in bd_platform.defi_yield_center (DeFi Yield Center).
"""

from __future__ import annotations

import json
import logging
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.YieldSustainability")

_FEATURE_ID = 709
_MERGED_FEATURES = [709, 198]
_SEED_PATH = Path("data/yield_history_seed.json")
_STORE_PATH = Path("data/yield_sustainability.json")

Sustainability = Literal["high", "medium", "low", "critical"]

_STABILITY_THRESHOLD_LOW = 2.0
_STABILITY_THRESHOLD_HIGH = 10.0
_OUTLIER_APY_THRESHOLD = 50.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> list[dict[str, Any]]:
    if not _SEED_PATH.is_file():
        return []
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("yield history seed load failed: %s", exc)
        return []


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    store = {"pools": {p["id"]: p for p in _load_seed()}, "updated_at": _utcnow()}
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    return store


def _stability_label(std_pct: float, outlier: bool) -> str:
    if outlier or std_pct >= _STABILITY_THRESHOLD_HIGH:
        return "volatile"
    if std_pct <= _STABILITY_THRESHOLD_LOW:
        return "stable"
    return "moderate"


def _sustainability_score(
    std_pct: float,
    fee_share: float,
    incentive_share: float,
    outlier: bool,
    current_apy: float,
) -> Sustainability:
    if outlier or current_apy > _OUTLIER_APY_THRESHOLD or std_pct >= _STABILITY_THRESHOLD_HIGH:
        return "critical" if outlier else "low"
    if fee_share >= 70 and std_pct <= _STABILITY_THRESHOLD_LOW:
        return "high"
    if fee_share >= 50 and std_pct <= _STABILITY_THRESHOLD_HIGH:
        return "medium"
    return "low"


def _sustainability_emoji(score: Sustainability) -> str:
    return {"high": "🟢", "medium": "🟡", "low": "🟠", "critical": "🔴"}.get(score, "⚪")


def _enrich_pool(row: dict[str, Any]) -> dict[str, Any]:
    current = float(row.get("current_apy_pct") or 0)
    avg_30d = float(row.get("apy_30d_avg_pct") or 0)
    std_30d = float(row.get("apy_30d_std_pct") or 0)
    fee_share = float(row.get("fee_share_pct") or 0)
    incentive_share = float(row.get("incentive_share_pct") or 0)
    outlier = bool(row.get("outlier_flag"))
    stability = _stability_label(std_30d, outlier)
    sustainability = _sustainability_score(std_30d, fee_share, incentive_share, outlier, current)
    emoji = _sustainability_emoji(sustainability)

    return {
        **row,
        "stability": stability,
        "stability_display": f"30-day avg: {avg_30d}% ({stability})",
        "sustainability": sustainability,
        "sustainability_display": f"Sustainability: {emoji} {sustainability.title()}",
        "yield_display": (
            f"Current APY: {current}% | 30-day avg: {avg_30d}% ({stability}) | "
            f"Analysis: {fee_share:.0f}% fees, {incentive_share:.0f}% temporary incentives"
        ),
        "incentive_decomposition": {
            "fee_share_pct": fee_share,
            "incentive_share_pct": incentive_share,
            "display": f"{fee_share:.0f}% fees | {incentive_share:.0f}% temporary incentives",
        },
        "outlier_detected": outlier,
        "time_series_stability": stability,
        "source_line": f"Source: {row.get('source')}",
        "not_a_prediction": True,
    }


def list_yield_pools(
    *,
    protocol: str | None = None,
    chain: str | None = None,
    sustainability: Sustainability | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    store = _load_store()
    rows = [_enrich_pool(p) for p in store.get("pools", {}).values()]

    if protocol:
        rows = [r for r in rows if protocol.lower() in str(r.get("protocol", "")).lower()]
    if chain:
        rows = [r for r in rows if str(r.get("chain", "")).lower() == chain.lower()]
    if sustainability:
        rows = [r for r in rows if r.get("sustainability") == sustainability]

    rows.sort(key=lambda r: float(r.get("tvl_usd") or 0), reverse=True)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_features": _MERGED_FEATURES,
        "mode": "yield_sustainability_score",
        "count": len(rows[:limit]),
        "pools": rows[:limit],
        "outlier_decomposition": True,
        "time_series_stability": True,
        "timestamp": _utcnow(),
    }


def get_yield_pool(pool_id: str) -> dict[str, Any]:
    store = _load_store()
    row = store.get("pools", {}).get(pool_id)
    if not row:
        return {"ok": False, "error": "pool_not_found"}
    enriched = _enrich_pool(row)
    history = row.get("apy_history_30d") or []
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "pool": enriched,
        "apy_history_30d": history,
        "history_stats": {
            "mean": round(statistics.fmean(history), 2) if history else None,
            "std": round(statistics.pstdev(history), 2) if len(history) > 1 else 0,
            "min": min(history) if history else None,
            "max": max(history) if history else None,
        },
        "timestamp": _utcnow(),
    }


def yield_sustainability_status() -> dict[str, Any]:
    store = _load_store()
    pools = list(store.get("pools", {}).values())
    outliers = sum(1 for p in pools if p.get("outlier_flag"))
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_features": _MERGED_FEATURES,
        "module": "Yield Sustainability Score",
        "sprint": 2,
        "pool_count": len(pools),
        "outlier_count": outliers,
        "outlier_decomposition": True,
        "incentive_decomposition": True,
        "time_series_stability": True,
        "integrated_with": ["#198", "#710", "incentive_tracker"],
        "timestamp": _utcnow(),
    }
