"""
BLACKDARK — Activate full 100-exchange universe (Excel plan priority #1).

Approves operational manifest and ensures all registry venues are polled.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.UniverseRollout")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _registry_exchange_ids() -> list[str]:
    from platform_universe import universe_exchange_ids

    return sorted(universe_exchange_ids())


def _registry_asset_symbols() -> list[str]:
    from platform_universe import universe_asset_symbols

    return sorted(universe_asset_symbols())


def activate_full_universe(*, save: bool = True) -> dict[str, Any]:
    """
    Approve manifest + set operational block to full 100-exchange / 105-asset universe.
    Idempotent — safe to run on every startup.
    """
    from liquidity_discovery import (
        load_operational_manifest,
        save_operational_manifest,
        symbols_for_assets,
    )

    path = config.OPERATIONAL_MANIFEST_PATH
    manifest = load_operational_manifest()
    if manifest is None:
        manifest = {
            "generated_at": _utcnow(),
            "guards": {
                "whitelist_exchanges_locked": True,
                "whitelist_assets_locked": True,
                "whitelist_exchanges": sorted(config.WHITELIST_EXCHANGES),
                "whitelist_assets": sorted(config.WHITELIST_ASSETS),
            },
            "filters": {
                "min_trust_score": config.LIQUIDITY_MIN_TRUST_SCORE,
                "min_24h_volume_usd": config.LIQUIDITY_MIN_24H_VOLUME_USD,
                "quote_currencies": list(config.LIQUIDITY_QUOTE_CURRENCIES),
                "max_dynamic_exchanges": config.LIQUIDITY_MAX_DYNAMIC_EXCHANGES,
                "max_dynamic_assets": config.LIQUIDITY_MAX_DYNAMIC_ASSETS,
            },
            "dynamic_candidates": {},
        }

    exchange_ids = _registry_exchange_ids()
    asset_symbols = _registry_asset_symbols()
    symbols = symbols_for_assets(asset_symbols)

    manifest["status"] = "approved"
    manifest["generated_at"] = _utcnow()
    manifest["operational"] = {
        "exchanges": exchange_ids,
        "assets": asset_symbols,
        "symbols": symbols,
        "ingestion_ready_exchanges": sorted(
            set(exchange_ids) & set(config.INGESTION_READY_EXCHANGES)
        ),
    }
    manifest["review"] = {
        **(manifest.get("review") or {}),
        "approved": True,
        "approved_at": _utcnow(),
        "approval_mode": "universe_rollout",
        "instruction": "Full 100-exchange universe activated automatically.",
    }
    try:
        from platform_universe import build_manifest_universe_block

        manifest["universe"] = build_manifest_universe_block()
    except Exception:
        logger.debug("Universe block attach skipped", exc_info=True)

    saved_path = str(path)
    if save:
        saved_path = save_operational_manifest(manifest)

    try:
        import aggregator

        fetcher_count = len(aggregator.MARKET_FETCHERS)
    except Exception:
        fetcher_count = 0

    return {
        "timestamp": _utcnow(),
        "manifest_path": saved_path,
        "exchanges": len(exchange_ids),
        "assets": len(asset_symbols),
        "symbols": len(symbols),
        "fetchers_registered": fetcher_count,
        "approved": True,
        "message": (
            f"Activated {len(exchange_ids)} venues and {len(asset_symbols)} assets — manifest approved"
        ),
    }


async def live_rollout_status() -> dict[str, Any]:
    """How many of the 100 venues have recent price data."""
    from database import get_connection

    try:
        import aggregator

        registered = sorted(aggregator.MARKET_FETCHERS.keys())
    except Exception:
        registered = _registry_exchange_ids()

    target = set(_registry_exchange_ids())
    healthy: set[str] = set()
    try:
        async with get_connection() as db:
            rows = await (
                await db.execute(
                    """
                    SELECT DISTINCT exchange FROM pricing_logs
                    WHERE timestamp >= datetime('now', '-2 hours')
                    """
                )
            ).fetchall()
        healthy = {str(row[0]).lower() for row in rows if row[0]}
    except Exception:
        logger.debug("pricing_logs health query failed", exc_info=True)

    return {
        "timestamp": _utcnow(),
        "target_exchanges": len(target),
        "fetchers_registered": len(registered),
        "manifest_approved": _manifest_is_approved(),
        "healthy_exchanges": len(healthy & target),
        "healthy_sample": sorted(healthy & target)[:15],
        "inactive_exchanges": sorted(target - healthy)[:20],
        "coverage_percent": round(len(healthy & target) / max(len(target), 1) * 100, 1),
    }


def _manifest_is_approved() -> bool:
    from liquidity_discovery import load_operational_manifest, manifest_approved

    return manifest_approved(load_operational_manifest())


def rollout_summary_json() -> dict[str, Any]:
    path = config.OPERATIONAL_MANIFEST_PATH
    manifest = {}
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    operational = manifest.get("operational") or {}
    return {
        "manifest_exists": path.exists(),
        "manifest_status": manifest.get("status"),
        "review_approved": (manifest.get("review") or {}).get("approved"),
        "operational_exchanges": len(operational.get("exchanges") or []),
        "operational_assets": len(operational.get("assets") or []),
        "registry_exchanges": len(_registry_exchange_ids()),
    }
