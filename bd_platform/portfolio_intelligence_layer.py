"""
Portfolio Intelligence Layer — Feature #515 (Sprint 1 Portfolio Layer).

Renamed from standalone "Archive / Historical Portfolio Snapshot".
Point-in-time portfolio reconstruction — reproducible, no current-label leakage.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PortfolioIntelligenceLayer")

_FEATURE_ID = 515
_RENAMED_FROM = "Archive / Historical Portfolio Snapshot"
_TITLE = "Portfolio Intelligence Layer"
_STANDALONE = False
_MERGED_INTO = "Portfolio Layer / Historical Portfolio Snapshot"
_LAYER = "Portfolio Layer"
_SPRINT = 1
_SEED_PATH = Path("data/portfolio_intelligence_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Historical portfolio snapshot — point-in-time reconstruction. "
    "Timestamp exactness required. No current-label leakage. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"portfolios": {}, "snapshots": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("portfolio intelligence layer seed load failed: %s", exc)
        return {"portfolios": {}, "snapshots": {}}


def _snapshot_hash(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def build_historical_snapshot(
    portfolio_id: str,
    *,
    snapshot_timestamp: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Point-in-time portfolio reconstruction — reproducible."""
    seed = seed or _load_seed()
    key = f"{portfolio_id}:{snapshot_timestamp}"
    snapshot = (seed.get("snapshots") or {}).get(key)

    if not snapshot:
        return {
            "ok": False,
            "error": "snapshot_not_found",
            "portfolio_id": portfolio_id,
            "snapshot_timestamp": snapshot_timestamp,
        }

    portfolio = (seed.get("portfolios") or {}).get(portfolio_id, {})
    holdings = snapshot.get("holdings") or []
    total_value_usd = sum(h.get("value_usd", 0) for h in holdings)

    return {
        "ok": True,
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio.get("name", portfolio_id),
        "snapshot_timestamp": snapshot_timestamp,
        "timestamp_exactness": True,
        "point_in_time_reconstruction": True,
        "reproducible": True,
        "snapshot_hash": _snapshot_hash(snapshot),
        "holdings": holdings,
        "total_value_usd": round(total_value_usd, 2),
        "prices_as_of": snapshot.get("prices_as_of"),
        "no_current_label_leakage": snapshot.get("no_current_label_leakage", True),
        "historical_labels_only": True,
        "display": (
            f"Portfolio snapshot at {snapshot_timestamp} | "
            f"Total: ${total_value_usd:,.2f} | Reproducible hash: {_snapshot_hash(snapshot)}"
        ),
    }


def build_portfolio_intelligence_panel(
    portfolio_id: str = "demo_portfolio",
    *,
    snapshot_timestamp: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    portfolio = (seed.get("portfolios") or {}).get(portfolio_id)

    if not portfolio:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "portfolio_not_found", "portfolio_id": portfolio_id}

    if snapshot_timestamp:
        snapshot = build_historical_snapshot(
            portfolio_id, snapshot_timestamp=snapshot_timestamp, seed=seed,
        )
    else:
        latest_ts = portfolio.get("latest_snapshot_timestamp")
        snapshot = build_historical_snapshot(
            portfolio_id, snapshot_timestamp=latest_ts, seed=seed,
        ) if latest_ts else {"ok": False, "error": "no_snapshots"}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": snapshot.get("ok", False),
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "snapshot": snapshot,
        "available_snapshots": portfolio.get("available_snapshots", []),
        "point_in_time_reproducibility": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def portfolio_intelligence_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "portfolio_count": len(seed.get("portfolios") or {}),
        "snapshot_count": len(seed.get("snapshots") or {}),
        "point_in_time_reproducibility": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
