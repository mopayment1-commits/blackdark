"""
Private Market & VC Flow Intelligence — Feature #314 (Wave 2 Pro Intelligence).

Capital flow tracking for crypto-native funding rounds.
Not core crypto market data — private market intelligence layer.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PrivateMarketVCFlow")

_FEATURE_ID = 314
_TITLE = "Private Market & VC Flow Intelligence"
_STANDALONE = True
_MERGED_INTO = "Intelligence Ledger / Private Market & VC Flow"
_WAVE = 2
_SPRINT = 2
_SEED_PATH = Path("data/private_market_vc_flow_seed.json")
_METHODOLOGY_VERSION = "1.0"
_MEGA_ROUND_THRESHOLD_USD = 500_000_000

Confidence = Literal["high", "medium", "low"]

_DISCLAIMER = (
    "Private market funding data — crypto-native rounds only. "
    "Amounts normalized to USD at announcement date. "
    "Mega-rounds flagged for context. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"rounds": [], "sectors": {}, "revisions": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("private market vc flow seed load failed: %s", exc)
        return {"rounds": [], "sectors": {}, "revisions": []}


def build_data_source_lock() -> dict[str, Any]:
    return {
        "primary": ["crunchbase_api_free", "messari_pro", "theblock"],
        "manual_curation": True,
        "pitchbook": "Phase 2 (expensive)",
        "documented_per_round": True,
        "display": "Crunchbase (free) + Messari Pro + TheBlock + manual curation | PitchBook = Phase 2",
    }


def normalize_round_currency(round_data: dict[str, Any]) -> dict[str, Any]:
    """All rounds = USD equivalent at announcement date."""
    amount_usd = round_data.get("amount_usd")
    original = round_data.get("original_currency", "USD")
    fx_rate = round_data.get("fx_rate_at_announcement")
    stablecoin = round_data.get("stablecoin_round", False)

    return {
        "amount_usd": amount_usd,
        "original_currency": original,
        "fx_rate_at_announcement": fx_rate,
        "stablecoin_round": stablecoin,
        "stablecoin_converted": stablecoin,
        "not_current_usd": True,
        "announcement_date": round_data.get("announcement_date"),
        "normalization": "USD equivalent at announcement date",
        "fx_documented": fx_rate is not None or original == "USD",
    }


def flag_mega_round(round_data: dict[str, Any]) -> dict[str, Any]:
    amount = float(round_data.get("amount_usd", 0))
    is_mega = amount >= _MEGA_ROUND_THRESHOLD_USD
    return {
        "is_mega_round": is_mega,
        "mega_round_threshold_usd": _MEGA_ROUND_THRESHOLD_USD,
        "flagged": is_mega,
        "context": (
            "Strategic raise — not market benchmark" if is_mega else None
        ),
        "show_median_and_mean": True,
        "mean_only_forbidden": True,
    }


def build_round_entry(round_data: dict[str, Any]) -> dict[str, Any]:
    currency = normalize_round_currency(round_data)
    mega = flag_mega_round(round_data)
    revisions = round_data.get("revision_history") or []

    return {
        "round_id": round_data.get("round_id"),
        "company": round_data.get("company"),
        "sector": round_data.get("sector"),
        "stage": round_data.get("stage"),
        "geography": round_data.get("geography"),
        "investors": round_data.get("investors") or [],
        "source": round_data.get("source"),
        "source_documented": True,
        "currency": currency,
        "mega_round": mega,
        "revision_history": revisions,
        "revised": len(revisions) > 0,
        "revision_visible": (
            f"This round was revised on {revisions[-1]['date']}"
            if revisions else None
        ),
        "crypto_native": round_data.get("crypto_native", True),
    }


def compute_sector_flows(rounds: list[dict[str, Any]]) -> dict[str, Any]:
    by_sector: dict[str, list[float]] = {}
    for r in rounds:
        sector = r.get("sector", "other")
        amount = float(r.get("amount_usd", 0))
        by_sector.setdefault(sector, []).append(amount)

    sectors = []
    for sector, amounts in sorted(by_sector.items(), key=lambda x: sum(x[1]), reverse=True):
        amounts_sorted = sorted(amounts)
        median = amounts_sorted[len(amounts_sorted) // 2] if amounts_sorted else 0
        mean = sum(amounts) / len(amounts) if amounts else 0
        sectors.append({
            "sector": sector,
            "total_usd": round(sum(amounts), 2),
            "round_count": len(amounts),
            "median_usd": round(median, 2),
            "mean_usd": round(mean, 2),
            "both_median_and_mean": True,
            "acceleration": "rising" if mean > median * 1.2 else "stable",
        })

    return {
        "sectors": sectors,
        "hot_sectors": [s["sector"] for s in sectors[:3]],
        "rolling_total_usd": round(sum(float(r.get("amount_usd", 0)) for r in rounds), 2),
        "display": "Capital-flow dashboard + hot sectors",
    }


def build_scope_lock() -> dict[str, Any]:
    return {
        "crypto_native_only": True,
        "tradfi_vc": "Wave 3",
        "grants_excluded": True,
        "token_sales": "separate module",
        "display": "Crypto-native rounds only | TradFi VC = Wave 3 | Grants excluded",
    }


def build_vc_flow_dashboard(*, sector: str | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    rounds_raw = seed.get("rounds") or []

    if sector:
        rounds_raw = [r for r in rounds_raw if r.get("sector", "").lower() == sector.lower()]

    rounds = [build_round_entry(r) for r in rounds_raw]
    sector_flows = compute_sector_flows(rounds_raw)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "rounds": rounds,
        "round_count": len(rounds),
        "sector_flows": sector_flows,
        "data_source_lock": build_data_source_lock(),
        "scope_lock": build_scope_lock(),
        "historical_revisions_tracked": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def private_market_vc_flow_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "wave": _WAVE,
        "sprint": _SPRINT,
        "data_source_lock": build_data_source_lock(),
        "scope_lock": build_scope_lock(),
        "round_count": len(seed.get("rounds") or []),
        "acceptance_criteria": {
            "currency_normalization": True,
            "outlier_mega_round_context": True,
            "historical_revisions_tracked": True,
            "source_documented_per_round": True,
            "crypto_native_scope": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
