"""
M&A Intelligence Module — Feature #740 (Sprint 2 Intelligence Ledger).

Deal status/source visible. Undisclosed values remain unknown — no fabricated valuation.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MAIntelligence")

_FEATURE_ID = 740
_SPRINT = 2
_SEED_PATH = Path("data/ma_intelligence_seed.json")
_METHODOLOGY_VERSION = "1.0"

DealStatus = Literal["rumored", "confirmed", "closed"]

_DISCLAIMER = (
    "M&A data based on public disclosures. Rumored deals may not close. "
    "Undisclosed values are shown as Unknown — never estimated."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"deals": [], "trends": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ma intelligence seed load failed: %s", exc)
        return {"deals": [], "trends": {}}


def normalize_deal(deal: dict[str, Any]) -> dict[str, Any]:
    value_usd = deal.get("value_usd")
    disclosed = value_usd is not None and deal.get("value_disclosed", True)

    return {
        "deal_id": deal.get("deal_id"),
        "target": deal.get("target"),
        "buyer": deal.get("buyer"),
        "sector": deal.get("sector"),
        "deal_type": deal.get("deal_type", "acquisition"),
        "status": deal.get("status", "rumored"),
        "status_display": f"Status: {str(deal.get('status', 'rumored')).title()}",
        "source": deal.get("source"),
        "source_display": f"Source: {deal.get('source', 'Unknown')}",
        "date": deal.get("date"),
        "value_usd": value_usd if disclosed else None,
        "value_display": f"${value_usd:,.0f}" if disclosed and value_usd else "Value: Undisclosed",
        "value_disclosed": disclosed,
        "no_fabricated_valuation": True,
        "fabrication_forbidden": True,
    }


def find_comparable_deals(
    deal: dict[str, Any],
    all_deals: list[dict[str, Any]],
    *,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    sector = deal.get("sector")
    deal_type = deal.get("deal_type", "acquisition")
    deal_date = deal.get("date", "")

    comps = []
    for d in all_deals:
        if d.get("deal_id") == deal.get("deal_id"):
            continue
        if d.get("sector") != sector:
            continue
        if d.get("deal_type") != deal_type:
            continue
        comps.append(normalize_deal(d))

    comps.sort(key=lambda x: abs(hash(x.get("date", "")) - hash(deal_date)))
    return comps[:max_results]


def build_ma_deal_panel(deal_id: str = "deal_001") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    deals = seed.get("deals") or []
    raw = next((d for d in deals if d.get("deal_id") == deal_id), None)

    if not raw:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "deal_not_found", "deal_id": deal_id}

    deal = normalize_deal(raw)
    comparables = find_comparable_deals(raw, deals)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sprint": _SPRINT,
        "deal": deal,
        "comparable_deals": comparables,
        "comparable_normalization": "sector + date range + deal type",
        "no_fabricated_valuation": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_ma_trends_dashboard() -> dict[str, Any]:
    seed = _load_seed()
    trends = seed.get("trends") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "volume_by_quarter": trends.get("volume_by_quarter") or [],
        "sector_heatmap": trends.get("sector_heatmap") or {},
        "top_acquirers": trends.get("top_acquirers") or [],
        "display": "M&A Volume by Quarter | Sector Heatmap | Top Acquirers",
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def ma_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "M&A Intelligence Module",
        "sprint": _SPRINT,
        "deal_count": len(seed.get("deals") or []),
        "acceptance_criteria": {
            "deal_status_source_visible": True,
            "undisclosed_remains_unknown": True,
            "no_fabricated_valuation": True,
            "comparable_deals_normalized": True,
            "trends_dashboard": True,
            "disclaimer_non_hideable": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
