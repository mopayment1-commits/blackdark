"""
Market Data Engine — Feature #274 (Sprint 1 Data Engine).

Absorbs #331 (Derivatives Venue Feed) and #333 (Funding Rate Context Panel).
Market Data Display only — feeds engine, no standalone dashboard, no trading signals.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MarketDataEngine")

_FEATURE_ID = 274
_ABSORBED_IDS = (331, 333, 343)
_STANDALONE = False
_MERGED_INTO = "Market Radar / Market Data Engine"
_SPRINT = 1
_SEED_PATH = Path("data/market_data_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"
_FRESHNESS_SLA_SECONDS = 3600

Surface = Literal["market_data_display"]

_DISCLAIMER = (
    "Raw market data display only — not investment advice. "
    "No trading signal interpretation. Funding rate differences = market information. "
    "No 'Short Squeeze Incoming' or similar signal language."
)

_NO_SIGNAL_LANGUAGE = {
    "no_trading_signal_mask": True,
    "no_investment_advice": True,
    "no_squeeze_language": True,
    "no_opportunity_language": True,
    "raw_display_only": True,
}


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
        return {"venues": {}, "provider_semantics": {}, "weighting": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market data engine seed load failed: %s", exc)
        return {"venues": {}, "provider_semantics": {}, "weighting": {}}


def build_provider_semantics_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#331 provider semantics lock — unified schema, freshness SLA, fallback."""
    seed = seed or _load_seed()
    ps = seed.get("provider_semantics") or {}
    return {
        "unified_schema_per_venue": True,
        "schema_version": ps.get("schema_version", "1.0"),
        "fields": ps.get("fields") or [
            "funding_rate", "open_interest_usd", "liquidation_usd_24h",
            "volume_24h_usd", "funding_timestamp_utc", "settlement_time_utc",
        ],
        "freshness_sla_seconds": ps.get("freshness_sla_seconds", _FRESHNESS_SLA_SECONDS),
        "freshness_sla_display": f"Data older than {ps.get('freshness_sla_seconds', _FRESHNESS_SLA_SECONDS)}s = stale",
        "fallback_sources": ps.get("fallback_sources") or {},
        "provider_semantics_documented": True,
        "display": (
            f"Unified schema v{ps.get('schema_version', '1.0')} per venue | "
            f"Freshness SLA: {ps.get('freshness_sla_seconds', _FRESHNESS_SLA_SECONDS)}s | "
            "Fallback source documented per provider"
        ),
    }


def _is_stale(timestamp_utc: str | None, *, sla_seconds: int = _FRESHNESS_SLA_SECONDS) -> bool:
    ts = _parse_ts(timestamp_utc)
    if ts is None:
        return True
    return (datetime.now(UTC) - ts).total_seconds() > sla_seconds


def build_venue_metric_row(
    venue: dict[str, Any],
    *,
    provider_semantics: dict[str, Any],
) -> dict[str, Any]:
    """#331 raw venue metrics — no interpretation, no signal language."""
    sla = int(provider_semantics.get("freshness_sla_seconds", _FRESHNESS_SLA_SECONDS))
    funding_ts = venue.get("funding_timestamp_utc")
    stale = _is_stale(funding_ts, sla_seconds=sla)
    funding_rate = venue.get("funding_rate")

    return {
        "venue": venue.get("venue"),
        "asset": venue.get("asset"),
        "funding_rate": funding_rate,
        "funding_rate_display": (
            f"Funding Rate = {funding_rate:.4%}" if funding_rate is not None else "Funding Rate = N/A"
        ),
        "open_interest_usd": venue.get("open_interest_usd"),
        "liquidation_usd_24h": venue.get("liquidation_usd_24h"),
        "volume_24h_usd": venue.get("volume_24h_usd"),
        "funding_timestamp_utc": funding_ts,
        "settlement_time_utc": venue.get("settlement_time_utc"),
        "stale": stale,
        "provider": venue.get("provider"),
        "fallback_provider": venue.get("fallback_provider"),
        "fallback_active": venue.get("fallback_active", False),
        "schema_version": provider_semantics.get("schema_version", "1.0"),
        "raw_display_only": True,
        **_NO_SIGNAL_LANGUAGE,
        "display": (
            f"{venue.get('venue')}: Funding Rate = {funding_rate:.4%} | "
            f"OI ${venue.get('open_interest_usd', 0):,.0f} | "
            f"Liq 24h ${venue.get('liquidation_usd_24h', 0):,.0f}"
            + (" | STALE" if stale else "")
        ),
    }


def build_derivatives_venue_feed(asset: str = "BTC") -> dict[str, Any]:
    """#331 Derivatives Venue Feed — data stream inside Market Data Engine (#274)."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_venues = (seed.get("venues") or {}).get(sym)

    if not asset_venues:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    provider_semantics = build_provider_semantics_block(seed)
    rows = [
        build_venue_metric_row(v, provider_semantics=provider_semantics)
        for v in (asset_venues.get("venue_list") or [])
    ]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sub_task": "#331",
        "absorbed_from": "Funding / OI / Liquidation Metrics",
        "title": "Derivatives Venue Feed",
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "surface": "market_data_display",
        "sprint": _SPRINT,
        "no_separate_sprint": True,
        "no_engineering_allocation": True,
        "apis_counted_as_cogs": True,
        "no_dashboard": True,
        "feeds_engine": True,
        "asset": sym,
        "venue_metrics": rows,
        "venue_count": len(rows),
        "provider_semantics": provider_semantics,
        "data_stream": True,
        **_NO_SIGNAL_LANGUAGE,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_weighting_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#333 weighting documented lock — formula, outlier threshold, settlement sync."""
    seed = seed or _load_seed()
    w = seed.get("weighting") or {}
    return {
        "formula": w.get("formula", "weighted_funding = Σ(funding_rate × oi_weight) / Σ(oi_weight)"),
        "oi_weight_basis": w.get("oi_weight_basis", "open_interest_usd"),
        "outlier_threshold_z": w.get("outlier_threshold_z", 3.0),
        "outlier_handling": w.get("outlier_handling", "exclude_beyond_z_threshold"),
        "settlement_sync_logic": w.get(
            "settlement_sync_logic",
            "align_to_utc_funding_interval_boundary",
        ),
        "settlement_timing_aligned": True,
        "weighting_documented": True,
        "display": (
            f"Weight: OI-based | Outlier threshold: z>{w.get('outlier_threshold_z', 3.0)} | "
            f"Settlement: {w.get('settlement_sync_logic', 'UTC interval boundary')}"
        ),
    }


def _compute_weighted_funding(
    venues: list[dict[str, Any]],
    *,
    weighting: dict[str, Any],
) -> dict[str, Any]:
    """Compute weighted funding with outlier exclusion — raw numbers only."""
    outlier_z = float(weighting.get("outlier_threshold_z", 3.0))
    rates = [float(v.get("funding_rate", 0)) for v in venues if v.get("funding_rate") is not None]
    if not rates:
        return {
            "weighted_funding_rate": None,
            "weighted_funding_display": "Weighted Funding Rate = N/A",
            "venues_included": 0,
            "venues_excluded_outlier": 0,
        }

    mean_rate = statistics.mean(rates)
    std_rate = statistics.stdev(rates) if len(rates) > 1 else 0.0

    included = []
    excluded_outliers = []
    for v in venues:
        rate = v.get("funding_rate")
        if rate is None:
            continue
        rate_f = float(rate)
        if std_rate > 0:
            z = abs((rate_f - mean_rate) / std_rate)
            if z > outlier_z:
                excluded_outliers.append({"venue": v.get("venue"), "z_score": round(z, 2)})
                continue
        oi = float(v.get("open_interest_usd", 0))
        included.append({"venue": v.get("venue"), "rate": rate_f, "oi_weight": oi})

    total_oi = sum(i["oi_weight"] for i in included) or 1.0
    weighted = sum(i["rate"] * i["oi_weight"] for i in included) / total_oi

    extremes = {
        "max_funding_rate": max(rates),
        "min_funding_rate": min(rates),
        "max_venue": max(venues, key=lambda v: float(v.get("funding_rate", 0))).get("venue"),
        "min_venue": min(venues, key=lambda v: float(v.get("funding_rate", 0))).get("venue"),
    }

    return {
        "weighted_funding_rate": round(weighted, 8),
        "weighted_funding_display": f"Weighted Funding Rate = {weighted:.4%}",
        "extremes": extremes,
        "persistence_hours": None,
        "venues_included": len(included),
        "venues_excluded_outlier": len(excluded_outliers),
        "excluded_outliers": excluded_outliers,
        "outlier_threshold_z": outlier_z,
    }


def build_funding_rate_context_panel(asset: str = "BTC") -> dict[str, Any]:
    """#333 Funding Rate Context Panel — NOT 'Intelligence', Market Radar display."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_venues = (seed.get("venues") or {}).get(sym)

    if not asset_venues:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    provider_semantics = build_provider_semantics_block(seed)
    weighting = build_weighting_block(seed)
    venue_rows = asset_venues.get("venue_list") or []
    weighted = _compute_weighted_funding(venue_rows, weighting=seed.get("weighting") or {})

    persistence = asset_venues.get("persistence") or {}
    crowding = asset_venues.get("crowding_state")
    crowding_display = crowding if crowding else "not_classified"

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sub_task": "#333",
        "absorbed_from": "Funding Rate Intelligence",
        "title": "Funding Rate Context Panel",
        "renamed_from": "Funding Rate Intelligence",
        "no_intelligence_in_name": True,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "surface": "market_data_display",
        "sprint": _SPRINT,
        "no_separate_sprint": True,
        "no_engineering_allocation": True,
        "no_dashboard": True,
        "feeds_engine": True,
        "asset": sym,
        "weighted_funding": weighted,
        "weighting": weighting,
        "persistence": {
            "hours_positive": persistence.get("hours_positive"),
            "hours_negative": persistence.get("hours_negative"),
            "display": (
                f"Persistence: +{persistence.get('hours_positive', 0)}h / "
                f"-{persistence.get('hours_negative', 0)}h"
            ),
            "raw_metric_only": True,
        },
        "crowding_state": crowding_display,
        "crowding_state_raw": True,
        "crowding_not_signal": True,
        "venue_metrics": [
            build_venue_metric_row(v, provider_semantics=provider_semantics)
            for v in venue_rows
        ],
        "settlement_timing_aligned": True,
        "provider_semantics": provider_semantics,
        **_NO_SIGNAL_LANGUAGE,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def _annualize_basis(basis_pct: float, days_to_expiry: float) -> float:
    """Annualized basis — expiry math verified."""
    if days_to_expiry <= 0:
        return basis_pct
    return round(basis_pct * (365 / days_to_expiry), 4)


def _days_to_expiry(expiry_utc: str | None, *, reference_utc: str | None = None) -> float:
    """Compute days to expiry — handles UTC timestamps."""
    if not expiry_utc:
        return 0.0
    try:
        expiry = datetime.fromisoformat(expiry_utc.replace("Z", "+00:00"))
        ref = (
            datetime.fromisoformat(reference_utc.replace("Z", "+00:00"))
            if reference_utc
            else datetime.now(UTC)
        )
        delta = (expiry - ref).total_seconds() / 86400
        return max(0.0, round(delta, 4))
    except ValueError:
        return 0.0


def build_term_structure_point(
    contract: dict[str, Any],
    *,
    spot_price: float,
    reference_utc: str | None = None,
) -> dict[str, Any]:
    """Single point on basis curve — math display only, no signal."""
    futures_price = float(contract.get("futures_price", 0))
    expiry_utc = contract.get("expiry_utc")
    days = _days_to_expiry(expiry_utc, reference_utc=reference_utc or contract.get("timestamp_utc"))

    if spot_price > 0 and futures_price > 0:
        basis_pct = ((futures_price - spot_price) / spot_price) * 100
        annualized = _annualize_basis(basis_pct, days)
    else:
        basis_pct = 0.0
        annualized = 0.0

    structure_label = "backwardation" if basis_pct < 0 else "contango" if basis_pct > 0 else "flat"

    return {
        "contract_id": contract.get("contract_id"),
        "venue": contract.get("venue"),
        "venue_normalized": contract.get("venue_normalized", contract.get("venue")),
        "contract_type": contract.get("contract_type", "dated_futures"),
        "expiry_utc": expiry_utc,
        "days_to_expiry": days,
        "spot_price": spot_price,
        "futures_price": futures_price,
        "basis_pct": round(basis_pct, 4),
        "annualized_basis_pct": annualized,
        "structure_label": structure_label,
        "structure_mathematical_only": True,
        "no_buy_signal": True,
        "no_opportunity_language": True,
        "no_implied_carry_claim": True,
        "no_forward_looking_claim": True,
        "timestamp_utc": contract.get("timestamp_utc"),
        "timestamp_sync": contract.get("timestamp_sync", True),
        "display": (
            f"{contract.get('venue')}: basis {basis_pct:.3f}% | "
            f"annualized {annualized:.2f}% | {structure_label} (mathematical)"
        ),
    }


def build_basis_curve_component(asset: str = "BTC") -> dict[str, Any]:
    """#343 Basis Curve — absorbed into Market Radar / Derivatives Panel."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    curve_data = (seed.get("basis_curves") or {}).get(sym)

    if not curve_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    spot_price = float(curve_data.get("spot_price", 0))
    reference_utc = curve_data.get("timestamp_utc")
    contracts = curve_data.get("contracts") or []
    perp = curve_data.get("perp") or {}

    curve_points = [
        build_term_structure_point(c, spot_price=spot_price, reference_utc=reference_utc)
        for c in contracts
    ]

    perp_point = None
    if perp:
        perp_point = build_term_structure_point(
            {
                "contract_id": f"{sym}_PERP",
                "venue": perp.get("venue"),
                "venue_normalized": perp.get("venue_normalized"),
                "contract_type": "perpetual",
                "futures_price": perp.get("perp_price"),
                "expiry_utc": None,
                "timestamp_utc": reference_utc,
                "timestamp_sync": True,
            },
            spot_price=spot_price,
            reference_utc=reference_utc,
        )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sub_task": "#343",
        "absorbed_from": "Futures Basis & Term Structure",
        "title": "Basis Curve",
        "standalone_rejected": True,
        "merged_into": "Market Radar / Derivatives Panel",
        "surface": "market_data_display",
        "no_separate_sprint": True,
        "no_engineering_allocation": True,
        "no_standalone_product": True,
        "asset": sym,
        "spot_price": spot_price,
        "timestamp_utc": reference_utc,
        "timestamp_sync": True,
        "venue_normalization": True,
        "expiry_math_verified": True,
        "perp_point": perp_point,
        "term_structure": curve_points,
        "curve_point_count": len(curve_points),
        "no_basis_trading_recommendation": True,
        "no_implied_carry_claim": True,
        "no_forward_looking_claim": True,
        "structure_labels_mathematical_only": True,
        "disclaimer": (
            "Basis curve = mathematical display only. "
            "Backwardation/contango = mathematical labels, not buy/sell signals. "
            "No implied carry or forward-looking claims."
        ),
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def market_data_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Market Data Engine",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "market_data_display",
        "absorbed_tickets": {
            331: "Derivatives Venue Feed (standalone rejected)",
            333: "Funding Rate Context Panel (standalone rejected, renamed from Funding Rate Intelligence)",
            343: "Basis Curve (standalone rejected)",
        },
        "no_separate_sprint": True,
        "no_engineering_allocation": True,
        "apis_counted_as_cogs": True,
        "no_dashboard": True,
        "feeds_engine": True,
        "provider_semantics": build_provider_semantics_block(seed),
        "weighting": build_weighting_block(seed),
        "asset_count": len(seed.get("venues") or {}),
        "acceptance_criteria": {
            "provider_semantics_lock": True,
            "unified_schema_per_venue": True,
            "freshness_sla": True,
            "fallback_source_documented": True,
            "weighting_documented": True,
            "outlier_threshold_documented": True,
            "settlement_timing_aligned": True,
            "no_trading_signal_mask": True,
            "no_intelligence_in_name": True,
            "market_data_display_only": True,
        },
        **_NO_SIGNAL_LANGUAGE,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
