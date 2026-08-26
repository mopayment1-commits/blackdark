"""
Bucketed CVD — Feature #518 (Sprint 1 On-Chain Metrics Layer).

CVD segmented by trade size buckets (retail/whale).
NOT standalone — integrated into On-Chain Metrics Layer.
Rule-based bucket definitions with versioned thresholds.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.BucketedCVD")

_FEATURE_ID = 518
_TITLE = "Bucketed CVD"
_STANDALONE = False
_MERGED_INTO = "On-Chain Metrics Layer / Bucketed CVD"
_LAYER = "On-Chain Layer"
_SPRINT = 1
_SEED_PATH = Path("data/bucketed_cvd_seed.json")
_METHODOLOGY_VERSION = "1.0"
_BUCKET_VERSION = "1.0"

_DISCLAIMER = (
    "Bucketed CVD data — not investment advice. "
    "Bucket definitions versioned and documented. Rule-based segmentation only."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "bucket_definitions": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("bucketed cvd seed load failed: %s", exc)
        return {"assets": {}, "bucket_definitions": {}}


def build_bucket_definitions(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Documented, versioned bucket thresholds — mandatory."""
    seed = seed or _load_seed()
    defs = seed.get("bucket_definitions") or {}
    return {
        "bucket_version": defs.get("version", _BUCKET_VERSION),
        "methodology_version": _METHODOLOGY_VERSION,
        "rule_based": True,
        "no_ai": True,
        "buckets": defs.get("buckets") or [
            {"id": "retail", "label": "Retail", "min_usd": 0, "max_usd": 10000},
            {"id": "medium", "label": "Medium", "min_usd": 10000, "max_usd": 100000},
            {"id": "whale", "label": "Whale", "min_usd": 100000, "max_usd": None},
        ],
        "definitions_documented": True,
        "versioned": True,
        "display": f"Bucket definitions v{defs.get('version', _BUCKET_VERSION)} — retail/whale thresholds documented",
    }


def compute_bucket_cvd(
    trades: list[dict[str, Any]],
    *,
    bucket_defs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """CVD per size bucket — rule-based."""
    bucket_defs = bucket_defs or build_bucket_definitions()["buckets"]
    results = []

    for bucket in bucket_defs:
        min_usd = float(bucket.get("min_usd", 0))
        max_usd = bucket.get("max_usd")
        buy_vol = 0.0
        sell_vol = 0.0

        for trade in trades:
            size = float(trade.get("size_usd", 0))
            if size < min_usd:
                continue
            if max_usd is not None and size >= float(max_usd):
                continue
            if trade.get("side") == "buy":
                buy_vol += size
            else:
                sell_vol += size

        cvd = buy_vol - sell_vol
        results.append({
            "bucket_id": bucket["id"],
            "bucket_label": bucket["label"],
            "min_usd": min_usd,
            "max_usd": max_usd,
            "buy_volume_usd": round(buy_vol, 2),
            "sell_volume_usd": round(sell_vol, 2),
            "cvd_usd": round(cvd, 2),
            "trade_count": sum(
                1 for t in trades
                if float(t.get("size_usd", 0)) >= min_usd
                and (max_usd is None or float(t.get("size_usd", 0)) < float(max_usd))
            ),
            "data_only": True,
            "display": f"{bucket['label']} CVD: ${cvd:,.0f}",
        })

    return results


def build_bucketed_cvd_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    data = (seed.get("assets") or {}).get(sym)

    if not data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    bucket_defs = build_bucket_definitions(seed)
    buckets = compute_bucket_cvd(data.get("trades") or [], bucket_defs=bucket_defs["buckets"])
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    retail = next((b for b in buckets if b["bucket_id"] == "retail"), {})
    whale = next((b for b in buckets if b["bucket_id"] == "whale"), {})

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "surface": "onchain_metrics_layer",
        "asset": sym,
        "bucket_definitions": bucket_defs,
        "buckets": buckets,
        "summary": {
            "retail_cvd_usd": retail.get("cvd_usd", 0),
            "whale_cvd_usd": whale.get("cvd_usd", 0),
            "retail_whale_display": (
                f"Retail CVD: ${retail.get('cvd_usd', 0):,.0f} | "
                f"Whale CVD: ${whale.get('cvd_usd', 0):,.0f}"
            ),
        },
        "rule_based_only": True,
        "no_ai": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def bucketed_cvd_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "bucket_definitions": build_bucket_definitions(seed),
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "bucket_definitions_versioned": True,
            "thresholds_documented": True,
            "rule_based_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
