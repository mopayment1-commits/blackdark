"""
Oracle VWAP Layer — Feature #413 (Oracle API Enhancement, merged with #409).

VWAP calculation across 10–15 major liquidity venues — NOT standalone Rate API.
Fair Value Index endpoint on existing Oracle API with constituent/source metadata.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.OracleVwapLayer")

_FEATURE_ID = 413
_MERGED_WITH = 409
_TITLE = "Oracle VWAP / Fair Value Index"
_STANDALONE = False
_MERGED_INTO = "Oracle API Enhancement"
_PRIORITY = "medium"
_SEED_PATH = Path("data/oracle_vwap_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Fair Value Index — volume-weighted reference price across major venues. "
    "Historical percentile context only — not investment advice. "
    "Constituent/source metadata mandatory per price."
)

_BANNED_TERMS = ("fair value target", "you should buy", "you should sell")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "venues": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("oracle vwap seed load failed: %s", exc)
        return {"assets": {}, "venues": []}


def compute_volume_weighted_vwap(constituents: list[dict[str, Any]]) -> dict[str, Any]:
    """VWAP across venue constituents using 1h VWAP when available, else last price."""
    if not constituents:
        return {"ok": False, "error": "no_constituents"}

    total_volume = 0.0
    weighted_sum = 0.0
    venue_vwaps: list[dict[str, Any]] = []

    for c in constituents:
        vol = float(c.get("volume_24h_usd", 0))
        price = float(c.get("vwap_1h") or c.get("price", 0))
        if vol <= 0 or price <= 0:
            continue
        weighted_sum += price * vol
        total_volume += vol
        venue_vwaps.append({
            "venue": c.get("venue"),
            "vwap": price,
            "volume_24h_usd": vol,
            "source": c.get("source"),
            "timestamp": c.get("timestamp"),
            "weight_pct": 0.0,
        })

    if total_volume <= 0:
        return {"ok": False, "error": "zero_volume"}

    fair_value = weighted_sum / total_volume
    for v in venue_vwaps:
        v["weight_pct"] = round(float(v["volume_24h_usd"]) / total_volume * 100, 2)
        v["deviation_pct"] = round((float(v["vwap"]) - fair_value) / fair_value * 100, 4)

    return {
        "ok": True,
        "fair_value_index": round(fair_value, 8),
        "total_volume_24h_usd": round(total_volume, 2),
        "constituent_count": len(venue_vwaps),
        "constituents": venue_vwaps,
        "method": "volume_weighted_vwap",
        "constituent_source_metadata": True,
    }


def build_fair_value_index(
    symbol: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fair Value Index for asset — Oracle API layer (not standalone endpoint namespace)."""
    seed = seed or _load_seed()
    sym = symbol.upper().replace("USDT", "").replace("/", "")
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "error": "asset_not_found", "symbol": sym}

    constituents = asset_data.get("constituents") or []
    vwap_result = compute_volume_weighted_vwap(constituents)

    if not vwap_result.get("ok"):
        return {**vwap_result, "symbol": sym}

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "symbol": sym,
        "quote": asset_data.get("quote", "USDT"),
        "fair_value_index": vwap_result["fair_value_index"],
        "vwap": vwap_result,
        "venue_count": len(constituents),
        "venues_used": seed.get("venues") or [],
        "constituent_source_metadata": True,
        "each_price_has_source": all(c.get("source") for c in constituents),
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def build_market_radar_vwap_context(
    symbol: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Market Radar integration — VWAP + per-venue deviation %."""
    fvi = build_fair_value_index(symbol, seed=seed)
    if not fvi.get("ok"):
        return {**fvi, "integration": "market_radar"}

    deviations = [
        {
            "venue": c["venue"],
            "price": c["vwap"],
            "deviation_pct": c["deviation_pct"],
            "source": c["source"],
        }
        for c in (fvi.get("vwap") or {}).get("constituents") or []
    ]

    return {
        "ok": True,
        "integration": "market_radar",
        "symbol": fvi["symbol"],
        "fair_value_index": fvi["fair_value_index"],
        "venue_deviations": deviations,
        "display": (
            f"Fair Value ${fvi['fair_value_index']:,.2f} | "
            f"{len(deviations)} venues with deviation %"
        ),
    }


def build_arbitrage_vwap_benchmark(
    symbol: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Arbitrage Scanner (#403) integration — VWAP as benchmark not best bid/ask."""
    fvi = build_fair_value_index(symbol, seed=seed)
    if not fvi.get("ok"):
        return {**fvi, "integration": "arbitrage_scanner"}

    return {
        "ok": True,
        "integration": "arbitrage_scanner",
        "feature_ref": 403,
        "symbol": fvi["symbol"],
        "benchmark_type": "vwap_fair_value",
        "benchmark_price": fvi["fair_value_index"],
        "not_best_bid_ask": True,
        "constituents": (fvi.get("vwap") or {}).get("constituents"),
        "display": f"Arbitrage benchmark: VWAP ${fvi['fair_value_index']:,.2f} (not best bid/ask)",
    }


def build_breakeven_vwap_price(
    symbol: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#404 Live Breakeven integration — VWAP reference for breakeven calculations."""
    fvi = build_fair_value_index(symbol, seed=seed)
    if not fvi.get("ok"):
        return {**fvi, "integration": "live_breakeven_tracker"}

    return {
        "ok": True,
        "integration": "live_breakeven_tracker",
        "feature_ref": 404,
        "symbol": fvi["symbol"],
        "vwap_reference_price": fvi["fair_value_index"],
        "use_for_breakeven": True,
        "source_metadata": True,
        "display": f"Breakeven VWAP reference: ${fvi['fair_value_index']:,.2f}",
    }


def build_cross_rates(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "cross_rates": seed.get("cross_rates") or {},
        "method": "vwap_derived",
        "constituent_source_metadata": True,
    }


def oracle_vwap_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_with": _MERGED_WITH,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "priority": _PRIORITY,
        "oracle_api_layer": True,
        "fair_value_index_endpoint": "/api/oracle/fair-value-index/{symbol}",
        "venue_count": seed.get("venue_count", 0),
        "venues": seed.get("venues") or [],
        "asset_count": len(seed.get("assets") or {}),
        "constituent_source_metadata": True,
        "integrations": {
            "arbitrage_scanner_403": True,
            "market_radar": True,
            "live_breakeven_404": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "oracle api layer"})
    checks.append({"id": "venue_count_10_15", "passed": 10 <= seed.get("venue_count", 0) <= 15, "detail": f"venues={seed.get('venue_count')}"})

    fvi = build_fair_value_index("BTC", seed=seed)
    checks.append({"id": "fair_value_index", "passed": fvi.get("ok") and fvi.get("fair_value_index", 0) > 0, "detail": str(fvi.get("fair_value_index"))})
    checks.append({"id": "constituent_source_metadata", "passed": fvi.get("each_price_has_source") is True, "detail": "all sources present"})
    checks.append({"id": "market_radar_integration", "passed": build_market_radar_vwap_context("BTC", seed=seed).get("ok") is True, "detail": "deviations"})
    checks.append({"id": "arbitrage_benchmark", "passed": build_arbitrage_vwap_benchmark("BTC", seed=seed).get("benchmark_type") == "vwap_fair_value", "detail": "vwap benchmark"})
    checks.append({"id": "breakeven_integration", "passed": build_breakeven_vwap_price("BTC", seed=seed).get("use_for_breakeven") is True, "detail": "404 hook"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
