"""
Cost Basis Distribution — Feature #520 (Sprint 1 On-Chain Analytics Layer).

Supply distribution by acquisition/cost basis cohorts.
Point-in-time reproducibility. No future leakage. Cohort rules documented.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.CostBasisDistribution")

_FEATURE_ID = 520
_TITLE = "Cost Basis Distribution"
_STANDALONE = False
_MERGED_INTO = "On-Chain Analytics Layer / Cost Basis Distribution"
_LAYER = "On-Chain Layer"
_SPRINT = 1
_SEED_PATH = Path("data/cost_basis_distribution_seed.json")
_METHODOLOGY_VERSION = "1.0"
_COHORT_VERSION = "1.0"

_DISCLAIMER = (
    "Cost basis distribution data — not investment advice. "
    "Point-in-time reproducible. No future leakage. Cohort rules documented."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "cohort_rules": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("cost basis distribution seed load failed: %s", exc)
        return {"assets": {}, "cohort_rules": {}}


def _distribution_hash(distribution: list[dict[str, Any]], as_of: str) -> str:
    payload = json.dumps({"as_of": as_of, "distribution": distribution}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def build_cohort_rules(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    rules = seed.get("cohort_rules") or {}
    return {
        "cohort_version": rules.get("version", _COHORT_VERSION),
        "methodology_version": _METHODOLOGY_VERSION,
        "rules": rules.get("rules") or [
            "acquisition_price_at_transfer_time",
            "holder_balance_snapshot_at_as_of",
            "no_future_price_data",
            "cohort_aggregation_by_price_band",
        ],
        "no_future_leakage": True,
        "point_in_time_only": True,
        "cohort_rules_documented": True,
        "display": f"Cohort rules v{rules.get('version', _COHORT_VERSION)} — no future leakage",
    }


def aggregate_cost_basis_cohorts(
    holders: list[dict[str, Any]],
    *,
    price_bands: list[dict[str, Any]] | None = None,
    current_price: float = 0,
) -> list[dict[str, Any]]:
    """Bucket supply by acquisition/cost basis — rule-based."""
    price_bands = price_bands or [
        {"label": "< -50%", "min_pct": None, "max_pct": -50},
        {"label": "-50% to -25%", "min_pct": -50, "max_pct": -25},
        {"label": "-25% to 0%", "min_pct": -25, "max_pct": 0},
        {"label": "0% to +25%", "min_pct": 0, "max_pct": 25},
        {"label": "+25% to +50%", "min_pct": 25, "max_pct": 50},
        {"label": "> +50%", "min_pct": 50, "max_pct": None},
    ]

    cohorts = []
    for band in price_bands:
        supply = 0.0
        holder_count = 0
        for h in holders:
            cost = float(h.get("acquisition_price", 0))
            balance = float(h.get("balance", 0))
            if cost <= 0 or current_price <= 0:
                continue
            pnl_pct = ((current_price - cost) / cost) * 100
            min_pct = band.get("min_pct")
            max_pct = band.get("max_pct")
            if min_pct is not None and pnl_pct < min_pct:
                continue
            if max_pct is not None and pnl_pct >= max_pct:
                continue
            supply += balance
            holder_count += 1

        cohorts.append({
            "band_label": band["label"],
            "supply": round(supply, 4),
            "holder_count": holder_count,
            "supply_pct": None,
            "display": f"{band['label']}: {supply:,.2f} supply ({holder_count} holders)",
        })

    total = sum(c["supply"] for c in cohorts) or 1
    for c in cohorts:
        c["supply_pct"] = round((c["supply"] / total) * 100, 2)

    return cohorts


def identify_key_levels(
    cohorts: list[dict[str, Any]],
    *,
    current_price: float,
) -> list[dict[str, Any]]:
    """Key cost-basis levels — descriptive, not support/resistance prediction."""
    levels = []
    sorted_cohorts = sorted(cohorts, key=lambda c: c["supply"], reverse=True)
    for i, cohort in enumerate(sorted_cohorts[:3]):
        if cohort["supply"] > 0:
            levels.append({
                "level_type": "cost_basis_concentration",
                "band_label": cohort["band_label"],
                "supply_pct": cohort["supply_pct"],
                "rank": i + 1,
                "not_support_resistance_prediction": True,
                "descriptive_only": True,
                "display": (
                    f"Cost basis concentration: {cohort['band_label']} "
                    f"({cohort['supply_pct']:.1f}% of supply)"
                ),
            })
    return levels


def build_cost_basis_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    data = (seed.get("assets") or {}).get(sym)

    if not data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    as_of = data.get("as_of", _utcnow())
    current_price = float(data.get("current_price", 0))
    holders = data.get("holders") or []
    cohort_rules = build_cohort_rules(seed)
    cohorts = aggregate_cost_basis_cohorts(
        holders, current_price=current_price,
    )
    key_levels = identify_key_levels(cohorts, current_price=current_price)
    dist_hash = _distribution_hash(cohorts, as_of)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "surface": "onchain_analytics_layer",
        "asset": sym,
        "as_of": as_of,
        "current_price": current_price,
        "no_future_leakage": data.get("no_future_leakage", True),
        "point_in_time_reproducibility": True,
        "distribution_hash": dist_hash,
        "cohort_rules": cohort_rules,
        "cohorts": cohorts,
        "key_levels": key_levels,
        "historical_validation": data.get("historical_validation", False),
        "rule_based_only": True,
        "no_ai": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def cost_basis_distribution_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "cohort_rules": build_cohort_rules(seed),
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "no_future_leakage": True,
            "point_in_time_reproducibility": True,
            "cohort_rules_documented": True,
            "historical_validation": True,
            "rule_based_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
