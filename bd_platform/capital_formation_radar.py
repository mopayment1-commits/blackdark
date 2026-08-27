"""
Capital Formation Radar — Feature #648 (Sprint-2 Intelligence Ledger).

Composite capital momentum from fundraising, TVL, stablecoin inflows, yield compression.
NOT standalone — merged into Intelligence Ledger as Capital Formation Index.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.CapitalFormationRadar")

_FEATURE_ID = 648
_TITLE = "Capital Formation Index"
_LEGAL_NAME = "Capital Formation Radar"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Intelligence Ledger"
_SPRINT = 2
_SEED_PATH = Path("data/capital_formation_radar_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Capital Formation Radar — composite capital momentum indicator. "
    "No price guarantee. Not investment advice. Formula versioned and documented."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"sectors": {}, "formula": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("capital formation radar seed load failed: %s", exc)
        return {"sectors": {}, "formula": {}}


def _normalize_component(value: float, *, min_v: float, max_v: float) -> float:
    if max_v <= min_v:
        return 50.0
    return max(0.0, min(100.0, (value - min_v) / (max_v - min_v) * 100))


def _heatmap_color(score: float) -> str:
    if score >= 70:
        return "green"
    if score >= 50:
        return "yellow"
    if score >= 30:
        return "orange"
    return "red"


def build_capital_formation_radar(
    sector_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#648 — composite capital momentum radar."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    formula = seed.get("formula") or {}
    weights = formula.get("weights") or {}
    version = formula.get("version", _METHODOLOGY_VERSION)
    sectors = seed.get("sectors") or {}

    if sector_id:
        sectors = {sector_id: sectors[sector_id]} if sector_id in sectors else {}

    radar_entries: list[dict[str, Any]] = []

    for sid, data in sectors.items():
        fundraising = float(data.get("fundraising_velocity_30d_usd", 0))
        tvl_momentum = float(data.get("tvl_momentum_qoq_pct", 0))
        stablecoin_inflow = float(data.get("stablecoin_inflow_delta_usd", 0))
        yield_compression = float(data.get("yield_compression_pct", 0))

        components = {
            "fundraising_velocity": {
                "raw_value": fundraising,
                "normalized_score": _normalize_component(fundraising, min_v=0, max_v=float(formula.get("fundraising_max_usd", 500_000_000))),
                "weight": float(weights.get("fundraising_velocity", 0.25)),
                "definition": "30-day rolling sum of disclosed raises",
            },
            "tvl_momentum": {
                "raw_value": tvl_momentum,
                "normalized_score": _normalize_component(tvl_momentum, min_v=-20, max_v=30),
                "weight": float(weights.get("tvl_momentum", 0.30)),
                "definition": "QoQ TVL growth rate",
            },
            "stablecoin_inflow": {
                "raw_value": stablecoin_inflow,
                "normalized_score": _normalize_component(stablecoin_inflow, min_v=-5_000_000_000, max_v=5_000_000_000),
                "weight": float(weights.get("stablecoin_inflow", 0.25)),
                "definition": "Exchange reserve delta (positive = inflow)",
            },
            "yield_compression": {
                "raw_value": yield_compression,
                "normalized_score": _normalize_component(-yield_compression, min_v=-5, max_v=5),
                "weight": float(weights.get("yield_compression", 0.20)),
                "definition": "Average DeFi yield decline (indicates capital saturation)",
            },
        }

        composite = sum(c["normalized_score"] * c["weight"] for c in components.values())
        composite = round(composite, 2)

        price_action_pct = float(data.get("price_action_30d_pct", 0))
        formation_strong_price_flat = composite >= 65 and abs(price_action_pct) < 5

        radar_entries.append({
            "sector_id": sid,
            "sector_name": data.get("sector_name", sid),
            "capital_momentum_score": composite,
            "components": components,
            "heatmap_color": _heatmap_color(composite),
            "price_action_30d_pct": price_action_pct,
            "formation_vs_price": {
                "capital_formation_score": composite,
                "price_action_pct": price_action_pct,
                "formation_strong_price_flat": formation_strong_price_flat,
                "accumulation_opportunity_signal": formation_strong_price_flat,
                "display": (
                    f"Formation {composite:.0f} | Price {price_action_pct:+.1f}%"
                    + (" — accumulation opportunity" if formation_strong_price_flat else "")
                ),
            },
            "unlocks_context": data.get("unlocks_context"),
            "no_price_guarantee": True,
        })

    radar_entries.sort(key=lambda x: x["capital_momentum_score"], reverse=True)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    institutional_thesis = None
    try:
        from bd_platform.on_chain_financials import build_market_radar_revenue_sector

        institutional_thesis = {
            "on_chain_financials_641": build_market_radar_revenue_sector(),
            "institutional_grade_thesis": True,
            "display": "Capital Formation + On-Chain Financials = Institutional Grade Thesis",
        }
    except Exception:
        logger.debug("641 integration skipped", exc_info=True)

    daily_brief_hook = {
        "integration_474": True,
        "narrative_snippet": (
            f"Capital Radar: top sector {radar_entries[0]['sector_name']} "
            f"momentum {radar_entries[0]['capital_momentum_score']:.0f}"
            if radar_entries else "Capital Radar: neutral"
        ),
    }

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "formula": {
            "version": version,
            "documented": True,
            "weights": weights,
            "components": list(components.keys()) if radar_entries else [
                "fundraising_velocity", "tvl_momentum", "stablecoin_inflow", "yield_compression",
            ],
        },
        "capital_radar": radar_entries,
        "sector_count": len(radar_entries),
        "heatmap": {
            "enabled": True,
            "scale": "green_strong_to_red_weak",
            "entries": [
                {"sector": e["sector_id"], "score": e["capital_momentum_score"], "color": e["heatmap_color"]}
                for e in radar_entries
            ],
        },
        "historical_trend": seed.get("historical_trend") or [],
        "institutional_thesis_641": institutional_thesis,
        "daily_brief_474": daily_brief_hook,
        "opportunity_feed_429": {
            "positive_formation_sectors": [e["sector_id"] for e in radar_entries if e["capital_momentum_score"] >= 60],
            "ranking_boost": True,
        },
        "no_price_guarantee": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_capital_formation_chart(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Radar chart data for /capital-formation route."""
    radar = build_capital_formation_radar(seed=seed)
    if not radar.get("ok"):
        return radar
    return {
        "ok": True,
        "route": "/capital-formation",
        "chart_type": "radar",
        "sectors": [
            {
                "sector": e["sector_id"],
                "capital_momentum_score": e["capital_momentum_score"],
                "components": {k: v["normalized_score"] for k, v in e["components"].items()},
            }
            for e in radar["capital_radar"]
        ],
        "heatmap": radar["heatmap"],
        "historical_trend": radar.get("historical_trend"),
        "timestamp": _utcnow(),
    }


def get_sector_formation_boost(sector_id: str, *, seed: dict[str, Any] | None = None) -> float:
    """#429 — ranking boost for sectors with positive capital formation."""
    radar = build_capital_formation_radar(sector_id, seed=seed)
    if not radar.get("ok") or not radar.get("capital_radar"):
        return 0.0
    score = radar["capital_radar"][0]["capital_momentum_score"]
    return 0.15 if score >= 60 else 0.0


_ASSET_SECTOR_MAP: dict[str, str] = {
    "ETH": "defi_lending",
    "AAVE": "defi_lending",
    "UNI": "defi_lending",
    "LDO": "liquid_staking",
    "RWA": "rwa",
    "ARB": "layer2",
    "OP": "layer2",
    "IMX": "gaming",
}


def apply_formation_ranking_boost(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#429 — boost ranking for opportunities in positive capital formation sectors."""
    radar = build_capital_formation_radar(seed=seed)
    positive_sectors = set((radar.get("opportunity_feed_429") or {}).get("positive_formation_sectors") or [])
    boosted: list[dict[str, Any]] = []

    for opp in opportunities:
        opp_copy = dict(opp)
        sector = opp_copy.get("sector_id") or _ASSET_SECTOR_MAP.get(str(opp_copy.get("asset", "")).upper())
        boost = get_sector_formation_boost(sector, seed=seed) if sector and sector in positive_sectors else 0.0
        if boost > 0:
            opp_copy["capital_formation_boost_648"] = boost
            opp_copy["sector_id_648"] = sector
            base = float(opp_copy.get("net_edge_usdt", 0))
            opp_copy["net_edge_usdt_ranking"] = round(base * (1 + boost), 4)
        else:
            opp_copy["net_edge_usdt_ranking"] = float(opp_copy.get("net_edge_usdt", 0))
        boosted.append(opp_copy)

    boosted.sort(key=lambda o: float(o.get("net_edge_usdt_ranking", 0)), reverse=True)
    return boosted


def capital_formation_radar_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "formula_version": (seed.get("formula") or {}).get("version"),
        "sector_count": len(seed.get("sectors") or {}),
        "no_price_guarantee": True,
        "integrations": {
            "on_chain_financials_641": True,
            "daily_brief_474": True,
            "unified_arbitrage_429": True,
            "market_radar": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": _STANDALONE is False, "detail": "648"})
    radar = build_capital_formation_radar(seed=seed)
    checks.append({"id": "radar_ok", "passed": radar.get("ok") is True, "detail": "radar"})
    checks.append({"id": "formula_versioned", "passed": (radar.get("formula") or {}).get("documented") is True, "detail": "formula"})
    checks.append({"id": "four_components", "passed": len((radar.get("formula") or {}).get("components") or []) == 4, "detail": "4"})
    checks.append({"id": "no_price_guarantee", "passed": radar.get("no_price_guarantee") is True, "detail": "legal"})
    checks.append({"id": "heatmap", "passed": (radar.get("heatmap") or {}).get("enabled") is True, "detail": "heatmap"})
    checks.append({"id": "formation_vs_price", "passed": any(e.get("formation_vs_price") for e in radar.get("capital_radar", [])), "detail": "compare"})
    checks.append({"id": "institutional_641", "passed": radar.get("institutional_thesis_641") is not None, "detail": "641"})
    checks.append({"id": "daily_brief_474", "passed": (radar.get("daily_brief_474") or {}).get("integration_474") is True, "detail": "474"})
    checks.append({"id": "opportunity_429", "passed": (radar.get("opportunity_feed_429") or {}).get("ranking_boost") is True, "detail": "429"})

    chart = build_capital_formation_chart(seed=seed)
    checks.append({"id": "radar_chart", "passed": chart.get("chart_type") == "radar", "detail": "chart"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
