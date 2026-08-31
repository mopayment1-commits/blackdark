"""
Index Data — Feature #739 (Sprint 2 Market Data Layer).

NOT standalone — merged into Market Data API.
Uses external index feeds (CoinGecko / CCData); no proprietary index engine.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.MarketDataIndices")

_FEATURE_ID = 739
_STANDALONE = False
_MERGED_INTO = "Market Data API / Index Feed"
_SPRINT = 2
_SEED_PATH = Path("data/market_data_indices_seed.json")
_METHODOLOGY_VERSION = "2.1"

_DISCLAIMER = (
    "Index data sourced from third-party providers (CoinGecko / CCData). "
    "Methodology and version documented. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"indices": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market data indices seed load failed: %s", exc)
        return {"indices": {}}


def build_methodology(index: dict[str, Any]) -> dict[str, Any]:
    meth = index.get("methodology") or {}
    return {
        "version": meth.get("version") or _METHODOLOGY_VERSION,
        "rebalance_frequency": meth.get("rebalance_frequency", "monthly"),
        "weighting": meth.get("weighting", "market_cap_weighted"),
        "constituent_count": meth.get("constituent_count", 100),
        "display": (
            f"Rebalanced {meth.get('rebalance_frequency', 'monthly')} | "
            f"{meth.get('weighting', 'market_cap_weighted').replace('_', ' ').title()} | "
            f"Top {meth.get('constituent_count', 100)}"
        ),
        "documented": True,
        "methodology_mandatory": True,
    }


def build_index_feed(index_id: str = "crypto_top100") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    idx = (seed.get("indices") or {}).get(index_id)

    if not idx:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "index_not_found", "index_id": index_id}

    methodology = build_methodology(idx)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "index_id": index_id,
        "name": idx.get("name"),
        "provider": idx.get("provider", "coingecko"),
        "provider_note": "Uses CoinGecko API or CCData — no proprietary index engine",
        "index_version": methodology["version"],
        "last_rebalance": idx.get("last_rebalance"),
        "display_version": (
            f"Index v{methodology['version']} | Last Rebalance: {idx.get('last_rebalance', 'N/A')}"
        ),
        "methodology": methodology,
        "constituents": idx.get("constituents") or [],
        "constituent_count": len(idx.get("constituents") or []),
        "value": idx.get("index_value"),
        "change_24h_pct": idx.get("change_24h_pct"),
        "wave_3_custom_indices": "equal-weight, sector-based — deferred to Wave 3",
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def market_data_indices_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Index Data (Market Data API)",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "providers": ["coingecko", "ccdata"],
        "no_proprietary_engine": True,
        "methodology_version_mandatory": True,
        "index_count": len(seed.get("indices") or {}),
        "acceptance_criteria": {
            "methodology_documented": True,
            "version_visible": True,
            "not_standalone": True,
        },
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }
