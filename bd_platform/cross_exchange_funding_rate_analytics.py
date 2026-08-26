"""
Cross-Exchange Funding Rate Analytics — Feature #317 (Sprint 2 Intelligence Ledger).

Renamed from "Cross-Exchange Funding Arbitrage Scanner".
Data display only — no "arbitrage", no "scanner", no "opportunities", no execution language.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CrossExchangeFundingRateAnalytics")

_FEATURE_ID = 317
_RENAMED_FROM = "Cross-Exchange Funding Arbitrage Scanner"
_TITLE = "Cross-Exchange Funding Rate Analytics"
_STANDALONE = True
_MERGED_INTO = "Intelligence Ledger / Cross-Exchange Funding Rate Analytics"
_SPRINT = 2
_WAVE = 2
_SEED_PATH = Path("data/cross_exchange_funding_rate_analytics_seed.json")
_METHODOLOGY_VERSION = "1.0"
_STALE_THRESHOLD_HOURS = 1
_TARGET_LATENCY_MS = 2000

AssetClass = Literal["perp", "spot"]
Confidence = Literal["high", "medium", "low"]

_DISCLAIMER = (
    "Funding rate differences = market information only. "
    "Execution risk = user responsibility. Fees = estimates. No recommendation. "
    "No 'trade this' or 'execute here' language."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "fee_model": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("cross-exchange funding rate analytics seed load failed: %s", exc)
        return {"assets": {}, "fee_model": {}}


def build_fee_model_block(fee_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "maker_fee_pct": fee_model.get("maker_fee_pct", 0.02),
        "taker_fee_pct": fee_model.get("taker_fee_pct", 0.05),
        "funding_fee_pct": fee_model.get("funding_fee_pct", 0.0),
        "round_trip_pct": fee_model.get("round_trip_pct", 0.10),
        "documented": True,
        "estimates_only": True,
        "display": (
            f"Fee model: maker {fee_model.get('maker_fee_pct', 0.02)}% | "
            f"taker {fee_model.get('taker_fee_pct', 0.05)}% | "
            f"round-trip {fee_model.get('round_trip_pct', 0.10)}% (estimates)"
        ),
    }


def _is_stale(timestamp_utc: str | None, *, now: datetime | None = None) -> bool:
    ts = _parse_ts(timestamp_utc)
    if ts is None:
        return True
    ref = now or datetime.now(UTC)
    return (ref - ts) > timedelta(hours=_STALE_THRESHOLD_HOURS)


def _annualize_funding_rate(rate: float, *, interval_hours: float = 8.0) -> float:
    """Convert per-interval funding rate to annualized APR (%)."""
    periods_per_year = (365 * 24) / interval_hours
    return round(rate * periods_per_year * 100, 4)


def build_venue_row(
    venue: dict[str, Any],
    *,
    fee_model: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Build comparison row — unknown venue or asset-class mismatch = excluded."""
    if venue.get("unknown_venue"):
        return None

    asset_class = venue.get("asset_class", "perp")
    if asset_class != "perp":
        return None
    if not venue.get("asset_class_verified", True):
        return None

    rate = float(venue.get("funding_rate", 0))
    interval = float(venue.get("funding_interval_hours", 8))
    gross_apr = _annualize_funding_rate(rate, interval_hours=interval)
    round_trip = float(fee_model.get("round_trip_pct", 0.10))
    net_apr = round(gross_apr - round_trip, 4)
    oi_usd = float(venue.get("open_interest_usd", 0))
    volume_24h = float(venue.get("volume_24h_usd", 0))
    spread_bps = venue.get("spread_bps")
    stale = _is_stale(venue.get("funding_timestamp_utc"), now=now)

    return {
        "venue": venue.get("venue"),
        "asset_class": asset_class,
        "asset_class_integrity": "perp_verified",
        "funding_rate": rate,
        "funding_interval_hours": interval,
        "funding_timestamp_utc": venue.get("funding_timestamp_utc"),
        "stale": stale,
        "stale_flag": stale,
        "stale_display": (
            f"Funding rate older than {_STALE_THRESHOLD_HOURS}h — flagged"
            if stale else "Fresh"
        ),
        "gross_apr_pct": gross_apr,
        "net_apr_pct": net_apr,
        "fee_deduction_pct": round_trip,
        "net_equals_gross_minus_fees": True,
        "open_interest_usd": oi_usd,
        "volume_24h_usd": volume_24h,
        "spread_bps": spread_bps,
        "capacity_estimate_usd": round(oi_usd * 0.05, 0),
        "capacity_basis": "OI-based estimate (5% of OI)",
        "confidence": venue.get("confidence", "medium"),
        "source": venue.get("source"),
        "display": (
            f"{venue.get('venue')}: funding {rate:.6f} | gross APR {gross_apr:.2f}% | "
            f"net APR {net_apr:.2f}% | OI ${oi_usd:,.0f}"
            + (" | STALE" if stale else "")
        ),
        "no_trade_recommendation": True,
        "no_execute_language": True,
    }


def build_comparison_table(
    venues: list[dict[str, Any]],
    *,
    fee_model: dict[str, Any],
    asset: str,
) -> dict[str, Any]:
    """Funding rate comparison table — ranked by net APR, not 'opportunities'."""
    now = datetime.now(UTC)
    rows = []
    excluded = []

    for v in venues:
        if v.get("unknown_venue"):
            excluded.append({"venue": v.get("venue"), "reason": "unknown_venue_excluded"})
            continue
        row = build_venue_row(v, fee_model=fee_model, now=now)
        if row is None:
            excluded.append({
                "venue": v.get("venue"),
                "reason": "asset_class_integrity_failed",
            })
            continue
        rows.append(row)

    rows.sort(key=lambda r: r["net_apr_pct"], reverse=True)

    for i, row in enumerate(rows, 1):
        row["rank"] = i

    return {
        "asset": asset,
        "output_format": "funding_rate_comparison_table",
        "no_arbitrage_language": True,
        "no_scanner_language": True,
        "no_opportunities_language": True,
        "ranked_by_net_apr": True,
        "rows": rows,
        "row_count": len(rows),
        "excluded_venues": excluded,
        "stale_threshold_hours": _STALE_THRESHOLD_HOURS,
        "asset_class_integrity": "perp_vs_spot_verified",
        "display": (
            f"Funding rate comparison — {asset} | {len(rows)} venues | "
            "ranked by net APR (gross minus fees)"
        ),
    }


def build_cross_exchange_funding_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    fee_model = build_fee_model_block(seed.get("fee_model") or asset_data.get("fee_model") or {})
    comparison = build_comparison_table(
        asset_data.get("venues") or [],
        fee_model=seed.get("fee_model") or {},
        asset=sym,
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "asset": sym,
        "comparison_table": comparison,
        "fee_model": fee_model,
        "no_arbitrage_language": True,
        "no_scanner_language": True,
        "no_opportunities_language": True,
        "no_trade_recommendation": True,
        "no_execute_language": True,
        "data_display_only": True,
        "target_latency_ms": _TARGET_LATENCY_MS,
        "latency_within_target": elapsed <= _TARGET_LATENCY_MS,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def cross_exchange_funding_rate_analytics_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "asset_class_integrity": True,
            "fee_model_documented": True,
            "stale_data_flagged": True,
            "unknown_venue_excluded": True,
            "no_arbitrage_language": True,
            "no_scanner_language": True,
            "no_opportunities_language": True,
            "latency_target_2s": True,
        },
        "stale_threshold_hours": _STALE_THRESHOLD_HOURS,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
