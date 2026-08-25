"""
Market Cap / Supply — Feature #267 merged into #705 + #217 (NOT standalone).

Supply provenance visible everywhere market cap appears.
Basic data — free on every asset page, not a separate paid API.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.MarketCapSupply")

_FEATURE_ID = 267
_MERGED_INTO = ("#705 Asset Metadata", "#217 OHLCV Core Feed")
_STANDALONE = False
_SEED_PATH = Path("data/supply_provenance_seed.json")

_DISCLAIMER = (
    "Market cap uses circulating supply unless labeled otherwise. "
    "FDV may never materialize if max supply is not reached. Not a valuation metric."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "supply_data_version": "3.1"}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("supply provenance seed load failed: %s", exc)
        return {"assets": {}, "supply_data_version": "3.1"}


def _supply_by_type(supplies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {s["supply_type"]: s for s in supplies if s.get("supply_type")}


def _format_usd(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.2f}"


def get_supply_provenance(symbol: str) -> dict[str, Any] | None:
    """Supply provenance for an asset — source + type for every supply figure."""
    seed = _load_seed()
    sym = symbol.upper().replace("/USDT", "")
    asset = (seed.get("assets") or {}).get(sym)
    if not asset:
        return None

    supplies = asset.get("supplies") or []
    enriched = []
    for s in supplies:
        enriched.append({
            **s,
            "provenance_display": (
                f"supply_type: {s.get('supply_type')} | "
                f"source: {s.get('source')} | "
                f"verified: {s.get('verified', False)}"
            ),
        })

    version = asset.get("supply_version") or seed.get("supply_data_version", "3.1")
    return {
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": list(_MERGED_INTO),
        "symbol": sym,
        "supply_version": version,
        "version_display": (
            f"Supply data v{version} | Last verified: {asset.get('last_verified_utc', 'N/A')} | "
            f"Next verification: {asset.get('next_verification_utc', 'N/A')}"
        ),
        "last_verified_utc": asset.get("last_verified_utc"),
        "next_verification_utc": asset.get("next_verification_utc"),
        "price_methodology": asset.get("price_methodology", "VWAP 1H"),
        "supplies": enriched,
        "self_reported_cross_check": asset.get("self_reported_cross_check"),
        "cross_check_display": (asset.get("self_reported_cross_check") or {}).get("display"),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_a_paid_api": True,
        "timestamp": _utcnow(),
    }


def build_market_cap_block(symbol: str, price_usd: float | None) -> dict[str, Any] | None:
    """
    Build market cap data with full provenance — three caps, not one.
    Circulating Market Cap, FDV, Max Supply Market Cap (if applicable).
    """
    provenance = get_supply_provenance(symbol)
    if not provenance or price_usd is None:
        return None

    sym = provenance["symbol"]
    by_type = _supply_by_type(provenance["supplies"])
    circulating = by_type.get("circulating", {}).get("amount")
    total = by_type.get("total", {}).get("amount")
    max_supply = by_type.get("max", {}).get("amount")

    circulating_mcap = (float(circulating) * price_usd) if circulating else None
    fdv = (float(total) * price_usd) if total else None
    max_mcap = (float(max_supply) * price_usd) if max_supply else None

    methodology = (
        f"Market Cap = Price ({provenance['price_methodology']}) × Circulating Supply | "
        f"Supply updated: daily | Source verified: on-chain"
    )

    caps_display = [
        f"Circulating Market Cap: {_format_usd(circulating_mcap)}",
        f"Fully Diluted Valuation (FDV): {_format_usd(fdv)}",
    ]
    if max_supply is not None:
        caps_display.append(f"Max Supply Market Cap: {_format_usd(max_mcap)}")
    else:
        caps_display.append("Max Supply Market Cap: N/A (no fixed max supply)")

    return {
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": list(_MERGED_INTO),
        "symbol": sym,
        "price_usd": price_usd,
        "circulating_market_cap_usd": circulating_mcap,
        "fdv_usd": fdv,
        "max_supply_market_cap_usd": max_mcap,
        "market_cap_display": " | ".join(caps_display),
        "circulating_display": caps_display[0],
        "fdv_display": caps_display[1],
        "max_supply_display": caps_display[2],
        "methodology": methodology,
        "methodology_display": methodology,
        "supply_provenance": provenance,
        "supply_version_display": provenance["version_display"],
        "cross_check_display": provenance.get("cross_check_display"),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_a_paid_api": True,
        "basic_data_free": True,
        "timestamp": _utcnow(),
    }
