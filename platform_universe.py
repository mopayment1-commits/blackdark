"""
BLACKDARK — Target Platform & Asset Universe (100 exchanges · 105 assets).

Source of truth from client blueprint:
  c:\\Users\\o\\Desktop\\المنصات والعملات المطلوب اضافتها.docx

Phased connection strategy:
  Tier 1 — ingestion_ready REST (9 CEX, live in aggregator.py)
  Tier 2 — ccxt_mapped (next REST rollout)
  Tier 3 — dex_subgraph / perp_api (on-chain & perp venues)
  Tier 4 — planned (regional / low-priority CEX)
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Literal

import config

logger = logging.getLogger("BLACKDARK.PlatformUniverse")

ConnectionStatus = Literal[
    "ingestion_ready",
    "ccxt_mapped",
    "dex_subgraph",
    "perp_api",
    "planned",
]
VenueCategory = Literal["cex", "regional_cex", "dex", "perp_dex"]

REGISTRY_PATH = config.DATA_DIR / "universe_registry.json"


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        logger.warning("Universe registry missing | path=%s", REGISTRY_PATH)
        return {"exchanges": [], "assets": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def universe_exchanges() -> list[dict[str, Any]]:
    return list(load_registry().get("exchanges") or [])


def universe_assets() -> list[dict[str, Any]]:
    return list(load_registry().get("assets") or [])


def universe_asset_symbols() -> tuple[str, ...]:
    symbols: list[str] = []
    seen: set[str] = set()
    for row in universe_assets():
        sym = str(row.get("symbol") or "").upper()
        if sym and sym not in seen:
            seen.add(sym)
            symbols.append(sym)
        for raw_alias in row.get("aliases") or []:
            alias = str(raw_alias).upper()
            if alias and alias not in seen:
                seen.add(alias)
                symbols.append(alias)
    return tuple(symbols)


def universe_exchange_ids() -> tuple[str, ...]:
    return tuple(str(row["id"]) for row in universe_exchanges())


def exchanges_by_status(status: str) -> list[dict[str, Any]]:
    return [row for row in universe_exchanges() if row.get("status") == status]


def resolve_asset_symbol(symbol: str) -> str:
    cleaned = symbol.upper().strip()
    for row in universe_assets():
        if cleaned == str(row.get("symbol", "")).upper():
            return str(row["symbol"]).upper()
        for alias in row.get("aliases") or []:
            if cleaned == str(alias).upper():
                return str(row["symbol"]).upper()
    return cleaned


def build_manifest_universe_block() -> dict[str, Any]:
    exchanges = universe_exchanges()
    assets = universe_assets()
    ready = exchanges_by_status("ingestion_ready")
    return {
        "target_exchanges": len(exchanges),
        "target_assets": len(assets),
        "ingestion_ready_count": len(ready),
        "ingestion_ready_ids": [row["id"] for row in ready],
        "ccxt_mapped_count": len(exchanges_by_status("ccxt_mapped")),
        "dex_count": sum(1 for row in exchanges if row.get("category") == "dex"),
        "perp_dex_count": sum(1 for row in exchanges if row.get("category") == "perp_dex"),
        "asset_symbols": [row["symbol"] for row in assets],
        "exchanges": exchanges,
        "assets": assets,
    }


async def compute_universe_coverage() -> dict[str, Any]:
    """Compare target universe vs live ingestion + data lake footprint."""
    from database import fetch_ingestion_health_summary

    block = build_manifest_universe_block()
    health_rows = await fetch_ingestion_health_summary()
    healthy_count = sum(1 for row in health_rows if row.get("last_ok_at"))

    ready_ids = set(block["ingestion_ready_ids"])

    return {
        "target": {
            "exchanges": block["target_exchanges"],
            "assets": block["target_assets"],
        },
        "ingestion_ready_exchanges": block["ingestion_ready_count"],
        "ccxt_next_wave": block["ccxt_mapped_count"],
        "dex_venues": block["dex_count"],
        "perp_dex_venues": block["perp_dex_count"],
        "coverage_percent_exchanges": round(
            block["ingestion_ready_count"] / max(block["target_exchanges"], 1) * 100,
            1,
        ),
        "coverage_percent_assets": round(
            len(block["asset_symbols"]) / max(block["target_assets"], 1) * 100,
            1,
        ),
        "live_ingestion_sources": healthy_count,
        "ingestion_health_rows": len(health_rows),
        "ingestion_ready_ids": sorted(ready_ids),
        "recommended_next_exchanges": [
            row["id"]
            for row in universe_exchanges()
            if row.get("status") == "ccxt_mapped"
        ][:15],
        "strategy": (
            "Phase A: universe registry + storage schema (done). "
            "Phase B/B2: CEX via CCXT + CoinGecko proxy (live). "
            "Phase C: 20 DEX via Jupiter/Raydium/DeFiLlama (live). "
            "Phase D: 10 Perp DEX via Hyperliquid/dYdX/GMX APIs (live)."
        ),
    }
