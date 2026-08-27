"""Asset metadata registry — loads universe + enrichment into stable canonical records."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

import config
from blackdark.canonical.schema import REGISTRY_VERSION, CanonicalAsset, make_canonical_id
from blackdark.canonical.vendor_maps import (
    BINANCE_QUOTE_SUFFIX,
    COINGECKO_IDS,
    COINGECKO_REVERSE,
    KRAKEN_BASE_REVERSE,
    KRAKEN_PAIRS,
)
from platform_universe import universe_assets

logger = logging.getLogger("BLACKDARK.CanonicalRegistry")

ENRICHMENT_PATH = config.DATA_DIR / "canonical_enrichment.json"


def _load_enrichment() -> dict[str, Any]:
    if not ENRICHMENT_PATH.exists():
        return {"assets": {}}
    return json.loads(ENRICHMENT_PATH.read_text(encoding="utf-8"))


def _build_external_ids(symbol: str, extra: dict[str, Any]) -> dict[str, str]:
    external = dict(extra.get("external_ids") or {})
    sym = symbol.upper()
    cg = COINGECKO_IDS.get(sym)
    if cg and "coingecko_id" not in external:
        external["coingecko_id"] = cg
    if sym not in external and f"binance_pair" not in external:
        external["binance_pair"] = f"{sym}{BINANCE_QUOTE_SUFFIX}"
    kraken = KRAKEN_PAIRS.get(sym)
    if kraken and "kraken_pair" not in external:
        external["kraken_pair"] = kraken
    return external


def _merge_asset_row(row: dict[str, Any], enrichment: dict[str, Any]) -> CanonicalAsset:
    symbol = str(row.get("symbol") or "").upper()
    extra = enrichment.get("assets", {}).get(symbol, {})
    aliases = [str(a).upper() for a in row.get("aliases") or []]
    aliases.extend(str(a).upper() for a in extra.get("aliases_extra") or [])
    aliases = tuple(dict.fromkeys(aliases))
    return CanonicalAsset(
        canonical_id=make_canonical_id(symbol),
        symbol=symbol,
        label=str(row.get("label") or symbol),
        aliases=aliases,
        sector=extra.get("sector"),
        external_ids=_build_external_ids(symbol, extra),
        contracts=dict(extra.get("contracts") or {}),
        registry_version=REGISTRY_VERSION,
    )


@lru_cache(maxsize=1)
def build_registry_index() -> dict[str, Any]:
    """In-memory indexes for O(1) resolution."""
    enrichment = _load_enrichment()
    by_canonical: dict[str, CanonicalAsset] = {}
    by_symbol: dict[str, CanonicalAsset] = {}
    by_alias: dict[str, CanonicalAsset] = {}
    by_coingecko: dict[str, CanonicalAsset] = {}
    by_contract: dict[str, CanonicalAsset] = {}
    by_pair: dict[str, CanonicalAsset] = {}

    for row in universe_assets():
        asset = _merge_asset_row(row, enrichment)
        by_canonical[asset.canonical_id] = asset
        by_symbol[asset.symbol] = asset
        for alias in asset.aliases:
            by_alias[alias.upper()] = asset
        cg = asset.external_ids.get("coingecko_id")
        if cg:
            by_coingecko[cg.lower()] = asset
        bp = asset.external_ids.get("binance_pair", "").upper()
        if bp:
            by_pair[bp] = asset
        for chain_contracts in asset.contracts.values():
            addr = str(chain_contracts.get("address") or "").lower()
            if addr:
                by_contract[addr] = asset

    # Kraken base aliases (XBT → BTC)
    for kraken_base, symbol in KRAKEN_BASE_REVERSE.items():
        target = by_symbol.get(symbol)
        if target:
            by_alias[kraken_base.upper()] = target

    # CoinGecko reverse without universe row (edge)
    for cg_id, symbol in COINGECKO_REVERSE.items():
        if cg_id not in by_coingecko and symbol in by_symbol:
            by_coingecko[cg_id] = by_symbol[symbol]

    return {
        "version": REGISTRY_VERSION,
        "assets": list(by_canonical.values()),
        "by_canonical": by_canonical,
        "by_symbol": by_symbol,
        "by_alias": by_alias,
        "by_coingecko": by_coingecko,
        "by_contract": by_contract,
        "by_pair": by_pair,
    }


def all_canonical_assets() -> list[CanonicalAsset]:
    return list(build_registry_index()["by_canonical"].values())


def get_canonical_asset(symbol_or_id: str) -> CanonicalAsset | None:
    key = symbol_or_id.upper().strip()
    idx = build_registry_index()
    if key.startswith("BD:"):
        return idx["by_canonical"].get(key.upper().replace("BD:", "bd:"))
    if key.startswith("bd:"):
        return idx["by_canonical"].get(key)
    return idx["by_symbol"].get(key) or idx["by_canonical"].get(f"bd:{key}")


def registry_stats() -> dict[str, Any]:
    idx = build_registry_index()
    return {
        "registry_version": idx["version"],
        "asset_count": len(idx["by_canonical"]),
        "alias_mappings": len(idx["by_alias"]),
        "coingecko_mappings": len(idx["by_coingecko"]),
        "contract_mappings": len(idx["by_contract"]),
        "pair_mappings": len(idx["by_pair"]),
        "enrichment_path": str(ENRICHMENT_PATH),
    }


def clear_registry_cache() -> None:
    build_registry_index.cache_clear()
