"""
BLACKDARK — Multi-exchange symbol mapping and tracked-asset helpers (Priority 3).

Shared by aggregator (order books) and ingestion_fetchers (data lake prices).
"""

from __future__ import annotations

from typing import Literal

import config

MarketType = Literal["spot", "cross", "perpetual"]

# Core assets polled on every spot venue for cross-exchange comparison.
TRACKED_PRICE_ASSETS: tuple[str, ...] = tuple(config.WHITELIST_ASSETS)

# Venues with spot books only (no linear perp + funding in aggregator v1).
SPOT_ONLY_EXCHANGES: frozenset[str] = frozenset({"coinbase", "kraken", "mexc"})

# Venues with spot + USDT-margined perpetual + funding.
PERP_READY_EXCHANGES: frozenset[str] = frozenset(
    {"binance", "okx", "bybit", "kucoin", "gateio", "bitget"}
)

_KRAKEN_BASE: dict[str, str] = {"BTC": "XBT"}


def split_pair(symbol: str) -> tuple[str, str]:
    base, quote = symbol.split("/")
    return base.upper(), quote.upper()


def native_symbol(
    exchange_id: str,
    symbol: str,
    market_type: MarketType = "spot",
) -> str:
    """Map BLACKDARK pair (e.g. BTC/USDT) to exchange-native instrument id."""
    base, quote = split_pair(symbol)
    ex = exchange_id.strip().lower()

    if ex == "okx":
        if market_type == "perpetual":
            return f"{base}-{quote}-SWAP"
        return f"{base}-{quote}"

    if ex == "coinbase":
        return f"{base}-{quote}"

    if ex == "kraken":
        kraken_base = _KRAKEN_BASE.get(base, base)
        return f"{kraken_base}{quote}"

    if ex == "kucoin":
        if market_type == "perpetual":
            fut_base = _KRAKEN_BASE.get(base, base)
            return f"{fut_base}{quote}M"
        return f"{base}-{quote}"

    if ex == "gateio":
        return f"{base}_{quote}"

    if ex == "bitget":
        return f"{base}{quote}"

    if ex == "mexc":
        return f"{base}{quote}"

    if ex == "bybit" and market_type == "perpetual":
        return f"{base}{quote}"

    return f"{base}{quote}"


def kraken_ticker_pairs(assets: tuple[str, ...] | None = None) -> str:
    """Comma-separated Kraken pair list for batch Ticker requests."""
    assets = assets or TRACKED_PRICE_ASSETS
    pairs = [native_symbol("kraken", f"{asset}/{config.QUOTE_BASE}", "spot") for asset in assets]
    return ",".join(pairs)


def gateio_currency_pairs(assets: tuple[str, ...] | None = None) -> list[str]:
    assets = assets or TRACKED_PRICE_ASSETS
    return [native_symbol("gateio", f"{asset}/{config.QUOTE_BASE}", "spot") for asset in assets]
