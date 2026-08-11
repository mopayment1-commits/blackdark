"""
BLACKDARK — Unified Market Fetcher Hub (B2 + C + D).

Routes each venue id to native REST, CCXT, CoinGecko proxy, DEX, or Perp DEX fetcher.
"""

from __future__ import annotations

import config
import logging

logger = logging.getLogger(__name__)

NATIVE_EXCHANGES: frozenset[str] = frozenset(
    {"binance", "okx", "bybit", "coinbase", "kraken", "kucoin", "gateio", "bitget", "mexc"}
)


def build_all_market_fetchers(native_fetchers: dict) -> dict:
    fetchers = dict(native_fetchers)
    try:
        from ccxt_market_fetcher import build_ccxt_market_fetchers

        fetchers.update(build_ccxt_market_fetchers())
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    try:
        from coingecko_cex_fetcher import build_coingecko_market_fetchers

        fetchers.update(build_coingecko_market_fetchers())
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    try:
        from dex_fetcher import build_dex_market_fetchers

        fetchers.update(build_dex_market_fetchers())
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    try:
        from perp_dex_fetcher import build_perp_market_fetchers

        fetchers.update(build_perp_market_fetchers())
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    return fetchers


def build_all_funding_fetchers(native_funding: dict) -> dict:
    funding = dict(native_funding)
    try:
        from ccxt_market_fetcher import build_ccxt_funding_fetchers

        funding.update(build_ccxt_funding_fetchers())
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    try:
        from perp_dex_fetcher import build_perp_funding_fetchers

        funding.update(build_perp_funding_fetchers())
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    return funding


def venue_kind(exchange_id: str) -> str:
    ex = exchange_id.lower()
    if ex in NATIVE_EXCHANGES:
        return "native"
    try:
        from dex_fetcher import DEX_VENUES

        if ex in DEX_VENUES:
            return "dex"
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    try:
        from perp_dex_fetcher import PERP_DEX_VENUES

        if ex in PERP_DEX_VENUES:
            return "perp_dex"
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    try:
        from coingecko_cex_fetcher import PHASE_B2_COINGECKO_EXCHANGES

        if ex in PHASE_B2_COINGECKO_EXCHANGES:
            return "coingecko"
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
    return "ccxt"


def symbols_for_exchange(exchange_id: str, spot_symbols: list[str]) -> list[str]:
    kind = venue_kind(exchange_id)
    if kind == "native":
        return spot_symbols
    if kind == "dex":
        from dex_fetcher import symbols_for_dex

        return symbols_for_dex(spot_symbols)
    if kind == "perp_dex":
        return []
    if kind == "coingecko":
        limit = max(5, int(getattr(config, "COINGECKO_SYMBOL_LIMIT", 10)))
        core = set(config.WHITELIST_ASSETS)
        core_syms = [s for s in spot_symbols if s.split("/")[0] in core]
        rest = [s for s in spot_symbols if s.split("/")[0] not in core]
        return core_syms + rest[: max(0, limit - len(core_syms))]
    if kind == "ccxt":
        from ccxt_market_fetcher import symbols_for_exchange as ccxt_symbols

        return ccxt_symbols(exchange_id, spot_symbols)
    return spot_symbols


def perp_symbols_for_exchange(exchange_id: str, perp_symbols: list[str]) -> list[str]:
    kind = venue_kind(exchange_id)
    if kind == "perp_dex":
        from perp_dex_fetcher import symbols_for_perp

        return symbols_for_perp(perp_symbols)
    if kind in {"coingecko", "dex"}:
        return []
    if kind == "ccxt":
        from exchange_adapters import SPOT_ONLY_EXCHANGES

        if exchange_id in SPOT_ONLY_EXCHANGES:
            return []
    return perp_symbols


def is_spot_only(exchange_id: str) -> bool:
    from exchange_adapters import SPOT_ONLY_EXCHANGES

    if exchange_id in SPOT_ONLY_EXCHANGES:
        return True
    kind = venue_kind(exchange_id)
    return kind in {"dex", "coingecko"}


def all_venue_ids() -> frozenset[str]:
    return frozenset(NATIVE_EXCHANGES) | _ccxt_ids() | _coingecko_ids() | _dex_ids() | _perp_ids()


def _ccxt_ids() -> frozenset[str]:
    try:
        from ccxt_market_fetcher import PHASE_B_EXCHANGES

        return PHASE_B_EXCHANGES
    except ImportError:
        return frozenset()


def _coingecko_ids() -> frozenset[str]:
    try:
        from coingecko_cex_fetcher import PHASE_B2_COINGECKO_EXCHANGES

        return PHASE_B2_COINGECKO_EXCHANGES
    except ImportError:
        return frozenset()


def _dex_ids() -> frozenset[str]:
    try:
        from dex_fetcher import DEX_VENUES

        return DEX_VENUES
    except ImportError:
        return frozenset()


def _perp_ids() -> frozenset[str]:
    try:
        from perp_dex_fetcher import PERP_DEX_VENUES

        return PERP_DEX_VENUES
    except ImportError:
        return frozenset()


def provider_for_venue(exchange_id: str) -> str:
    return venue_kind(exchange_id)


async def close_all_pools() -> None:
    try:
        from ccxt_market_fetcher import close_ccxt_pool

        await close_ccxt_pool()
    except ImportError:
        logger.debug("optional operation skipped", exc_info=True)
