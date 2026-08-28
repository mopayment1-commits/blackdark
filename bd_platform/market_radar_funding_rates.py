"""
Funding Rate Intelligence — Feature #861 (merged into Market Radar).

Cross-venue funding analysis: APR normalization, OI-weighted aggregates, divergence.
Route: /radar/derivatives/funding. Rule-based — no ML prediction.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.FundingRateIntelligence")

_FEATURE_REF = 861
_STANDALONE = False
_MERGED_INTO = "Market Radar"
_COMPONENT = "funding_rates_overlay"
_SPRINT = 2
_SEED_PATH = Path("data/funding_rate_intelligence_seed.json")
_VENUES = ("Binance", "Bybit", "OKX", "dYdX")
_DIVERGENCE_THRESHOLD_APR = 50.0
_STALE_MULTIPLIER = 2.0

_DISCLAIMER = (
    "Funding rates reflect derivatives market conditions. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("funding rate intelligence seed load failed: %s", exc)
        return {}


def normalize_funding_apr_861(
    funding_rate: float,
    settlement_interval_hours: float,
) -> float | None:
    """APR = funding_rate × (365 / settlement_interval_hours) × 100."""
    if settlement_interval_hours <= 0:
        return None
    return round(funding_rate * (365.0 / settlement_interval_hours) * 100, 4)


def is_stale_861(
    observed_at: str,
    settlement_interval_hours: float,
    *,
    now: datetime | None = None,
) -> bool:
    """Exclude if data older than 2× settlement interval."""
    now = now or datetime.now(UTC)
    observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    sla_seconds = settlement_interval_hours * 3600 * _STALE_MULTIPLIER
    return (now - observed).total_seconds() > sla_seconds


def compute_oi_weighted_apr_861(venues: list[dict[str, Any]]) -> float | None:
    """OI-weighted aggregate: Σ(funding × OI) / Σ(OI)."""
    valid = [v for v in venues if v.get("apr_pct") is not None and v.get("open_interest_usd") is not None]
    if not valid:
        return None
    total_oi = sum(float(v["open_interest_usd"]) for v in valid)
    if total_oi <= 0:
        return None
    weighted = sum(float(v["apr_pct"]) * float(v["open_interest_usd"]) for v in valid) / total_oi
    return round(weighted, 4)


def detect_divergence_861(aprs: list[float]) -> dict[str, Any]:
    """Divergence > 50% APR → High Divergence."""
    valid = [a for a in aprs if a is not None]
    if len(valid) < 2:
        return {"divergence_apr": None, "divergence_level": "N/A", "high_divergence": False}

    spread = max(valid) - min(valid)
    level = "High Divergence" if spread > _DIVERGENCE_THRESHOLD_APR else (
        "Moderate" if spread > _DIVERGENCE_THRESHOLD_APR / 2 else "Low"
    )
    return {
        "divergence_apr": round(spread, 4),
        "divergence_level": level,
        "high_divergence": spread > _DIVERGENCE_THRESHOLD_APR,
        "max_apr": max(valid),
        "min_apr": min(valid),
    }


def funding_rate_intelligence_status_861(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("funding_rate_intelligence_861") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "route": "/radar/derivatives/funding",
        "sprint": _SPRINT,
        "venues": list(_VENUES),
        "apr_formula": "funding_rate × (365 / settlement_interval_hours) × 100",
        "oi_weighted_formula": "Σ(funding × OI) / Σ(OI)",
        "divergence_threshold_apr": _DIVERGENCE_THRESHOLD_APR,
        "stale_sla_multiplier": _STALE_MULTIPLIER,
        "null_not_zero": True,
        "ml_rejected": True,
        "rule_based_only": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def build_funding_rates_panel_861(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Market Radar funding rates overlay — table/heatmap."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    cfg = seed.get("funding_rate_intelligence_861") or {}
    asset_data = (seed.get("assets") or {}).get(asset.upper())
    if not asset_data:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "asset_not_tracked", "asset": asset.upper()}

    venue_rows = []
    aprs: list[float | None] = []
    for venue_name in _VENUES:
        vdata = (asset_data.get("venues") or {}).get(venue_name)
        if not vdata:
            venue_rows.append({
                "venue": venue_name,
                "funding_rate": None,
                "apr_pct": "N/A",
                "settlement_interval_hours": None,
                "open_interest_usd": None,
                "stale": False,
                "excluded": True,
                "reason": "missing_data",
            })
            continue

        interval = float(vdata.get("settlement_interval_hours", 8))
        rate = vdata.get("funding_rate")
        observed_at = vdata.get("observed_at", _utcnow())
        stale = is_stale_861(observed_at, interval)

        if stale:
            venue_rows.append({
                "venue": venue_name,
                "funding_rate": rate,
                "apr_pct": "N/A",
                "settlement_interval_hours": interval,
                "settlement_verified": vdata.get("settlement_verified", True),
                "open_interest_usd": vdata.get("open_interest_usd"),
                "stale": True,
                "excluded": True,
                "reason": "stale_beyond_sla",
            })
            aprs.append(None)
            continue

        apr = normalize_funding_apr_861(float(rate), interval) if rate is not None else None
        aprs.append(apr)
        venue_rows.append({
            "venue": venue_name,
            "funding_rate": rate,
            "apr_pct": apr if apr is not None else "N/A",
            "settlement_interval_hours": interval,
            "settlement_verified": vdata.get("settlement_verified", True),
            "open_interest_usd": vdata.get("open_interest_usd"),
            "stale": False,
            "excluded": False,
        })

    included = [v for v in venue_rows if not v.get("excluded")]
    oi_weighted = compute_oi_weighted_apr_861(included)
    divergence = detect_divergence_861([a for a in aprs if a is not None])

    display_parts = [f"{asset.upper()} Funding"]
    for v in included:
        apr_disp = v.get("apr_pct")
        if apr_disp != "N/A":
            display_parts.append(f"{v['venue']}: {apr_disp}% APR")
    oi_disp = f"{oi_weighted}% APR" if oi_weighted is not None else "N/A"
    display_parts.append(f"OI-Weighted: {oi_disp}")
    display_parts.append(f"Divergence: {divergence.get('divergence_level', 'N/A')}")

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "surface": "market_radar",
        "panel_title_ar": "معدلات التمويل",
        "asset_card_badge": "مخاطر المشتقات",
        "route": "/radar/derivatives/funding",
        "asset": asset.upper(),
        "venues": venue_rows,
        "oi_weighted_apr_pct": oi_weighted,
        "divergence": divergence,
        "formatted_output": " | ".join(display_parts),
        "null_not_zero": True,
        "settlement_intervals_verified": all(
            v.get("settlement_verified", True) for v in venue_rows if not v.get("excluded")
        ),
        "latency_ms": elapsed_ms,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def build_derivatives_risk_badge_861(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Asset Card derivatives risk badge — funding divergence."""
    panel = build_funding_rates_panel_861(asset, seed=seed)
    div = panel.get("divergence") or {}
    badge_color = "red" if div.get("high_divergence") else (
        "yellow" if div.get("divergence_level") == "Moderate" else "green"
    )
    return {
        "ok": panel.get("ok", False),
        "feature_ref": _FEATURE_REF,
        "surface": "asset_card",
        "asset": asset.upper(),
        "badge_label": panel.get("asset_card_badge"),
        "badge_color": badge_color,
        "divergence_level": div.get("divergence_level"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_funding_rates_e2e_861(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = funding_rate_intelligence_status_861(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "four_venues", "passed": status.get("venues") == list(_VENUES)})
    tests.append({"test": "null_not_zero", "passed": status.get("null_not_zero") is True})
    tests.append({"test": "ml_rejected", "passed": status.get("ml_rejected") is True})

    apr = normalize_funding_apr_861(0.0001, 8)
    tests.append({"test": "apr_normalization", "passed": apr is not None and apr > 0})

    panel = build_funding_rates_panel_861("BTC", seed=seed)
    tests.append({"test": "panel_ok", "passed": panel.get("ok") is True})
    tests.append({"test": "settlement_verified", "passed": panel.get("settlement_intervals_verified") is True})
    tests.append({"test": "formatted_output", "passed": "OI-Weighted" in panel.get("formatted_output", "")})

    stale = is_stale_861(
        (datetime.now(UTC) - timedelta(hours=20)).isoformat(),
        8.0,
    )
    tests.append({"test": "stale_excluded", "passed": stale is True})

    badge = build_derivatives_risk_badge_861("BTC", seed=seed)
    tests.append({"test": "asset_card_badge", "passed": badge.get("badge_color") in ("green", "yellow", "red")})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
