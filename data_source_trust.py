"""
BLACKDARK — Source classification overlay (Data Trust Law).

Does not add 100 APIs. Classifies the existing registry so sources are not
used the same way: venue-direct decision-grade vs aggregator discovery.
"""

from __future__ import annotations

from typing import Any, Literal

DecisionRole = Literal["decision_grade", "fallback", "discovery", "enrichment"]
TruthTier = Literal["A", "B", "C", "D", "E", "F"]
SourceClass = Literal[
    "venue_direct",
    "aggregator",
    "chain_primary",
    "macro_primary",
    "macro_secondary",
    "regulatory_primary",
    "news_secondary",
    "enrichment",
]

# Existing registry ids that may feed Act/Wait prices (ticker). L2 is narrower.
_VENUE_DIRECT_IDS: frozenset[str] = frozenset(
    {
        "binance_spot",
        "binance_futures",
        "binance_ws",
        "kucoin_spot",
        "bybit_spot",
        "bybit_linear",
        "okx_spot",
        "okx_swap",
        "gateio_spot",
        "kraken_spot",
        "coinbase_spot",
        "gateio_futures",
        "mexc_spot",
        "bitget_spot",
        "bitget_futures",
        "htx_spot",
        "bitstamp_spot",
        "deribit_index",
        "phemex_spot",
        "bingx_spot",
        "whitebit_spot",
    }
)

_AGGREGATOR_IDS: frozenset[str] = frozenset(
    {
        "coingecko_prices",
        "coingecko_trending",
        "coingecko_events",
        "coingecko_reports",
        "coinmarketcap",
        "cryptocompare_prices",
        "coincap",
        "coinapi",
        "geckoterminal",
        "dexscreener",
    }
)

_CHAIN_PRIMARY_IDS: frozenset[str] = frozenset(
    {
        "etherscan",
        "solana_rpc",
        "blockchain_com",
        "mempool_space",
        "etherscan_gas",
        "bscscan",
        "polygonscan",
        "arbiscan",
        "optimistic_etherscan",
        "tronscan",
        "blockchair",
        "blockchair_btc_stats",
    }
)

_MACRO_PRIMARY_IDS: frozenset[str] = frozenset({"fred", "treasury_yield_10y"})
_REGULATORY_PRIMARY_IDS: frozenset[str] = frozenset({"sec_rss", "cftc_rss"})

# Native venues with real depth endpoints in aggregator.py
VENUE_L2_EXCHANGES: frozenset[str] = frozenset(
    {"binance", "okx", "bybit", "coinbase", "kraken", "kucoin", "gateio", "bitget", "mexc"}
)


def _default_license(source_class: SourceClass) -> dict[str, Any]:
    public = source_class in {
        "venue_direct",
        "chain_primary",
        "macro_primary",
        "regulatory_primary",
        "news_secondary",
        "aggregator",
        "macro_secondary",
        "enrichment",
    }
    return {
        "license_class": "public_api" if public else "unknown",
        "redistribution_allowed": False,
        "note": "Public fetch ≠ redistribution rights for B2B resale.",
    }


def classify_source(source_id: str, *, category: str | None = None) -> dict[str, Any]:
    """Classify one registered source. Aggregators never produce decision-grade L2."""
    sid = (source_id or "").strip().lower()
    cat = (category or "").strip().lower()
    if sid in _VENUE_DIRECT_IDS:
        source_class: SourceClass = "venue_direct"
        tier: TruthTier = "A"
        role: DecisionRole = "decision_grade"
        l2 = sid.split("_", 1)[0] in VENUE_L2_EXCHANGES or sid in {"binance_spot", "binance_futures", "binance_ws"}
    elif sid in _AGGREGATOR_IDS or sid.startswith("coingecko"):
        source_class = "aggregator"
        tier = "B"
        role = "fallback" if sid in {"coingecko_prices", "coinmarketcap"} else "discovery"
        l2 = False
    elif sid in _CHAIN_PRIMARY_IDS:
        source_class = "chain_primary"
        tier = "C"
        role = "decision_grade"
        l2 = False
    elif sid in _MACRO_PRIMARY_IDS:
        source_class = "macro_primary"
        tier = "D"
        role = "enrichment"
        l2 = False
    elif sid in _REGULATORY_PRIMARY_IDS:
        source_class = "regulatory_primary"
        tier = "E"
        role = "enrichment"
        l2 = False
    elif cat == "news" or sid.endswith("_rss"):
        source_class = "news_secondary"
        tier = "E"
        role = "enrichment"
        l2 = False
    elif cat == "macro":
        source_class = "macro_secondary"
        tier = "D"
        role = "enrichment"
        l2 = False
    else:
        source_class = "enrichment"
        tier = "F"
        role = "enrichment"
        l2 = False

    license_meta = _default_license(source_class)
    return {
        "source_id": sid,
        "source_class": source_class,
        "truth_tier": tier,
        "decision_role": role,
        "l2_decision_grade": bool(l2),
        "price_decision_grade": role == "decision_grade" and source_class == "venue_direct",
        "canonical_eligible": source_class == "venue_direct" and role == "decision_grade",
        **license_meta,
    }


def classify_venue(exchange_id: str) -> dict[str, Any]:
    """Classify a market-fetcher venue (native / ccxt / coingecko proxy / dex / perp)."""
    ex = (exchange_id or "").strip().lower()
    kind = "unknown"
    try:
        from market_fetcher_hub import venue_kind

        kind = venue_kind(ex)
    except Exception:
        if ex in VENUE_L2_EXCHANGES:
            kind = "native"

    if kind in {"native", "ccxt"} or ex in VENUE_L2_EXCHANGES:
        return {
            "exchange_id": ex,
            "fetcher_kind": kind if kind != "unknown" else "native",
            "source_class": "venue_direct",
            "truth_tier": "A",
            "book_origin": "venue_l2",
            "decision_grade": True,
            "price_decision_grade": True,
        }
    if kind == "coingecko":
        return {
            "exchange_id": ex,
            "fetcher_kind": "coingecko",
            "source_class": "aggregator",
            "truth_tier": "B",
            "book_origin": "synthetic",
            "decision_grade": False,
            "price_decision_grade": False,
            "honesty": "CoinGecko proxy is discovery/fallback — never venue L2.",
        }
    if kind == "dex":
        return {
            "exchange_id": ex,
            "fetcher_kind": "dex",
            "source_class": "venue_direct",
            "truth_tier": "A",
            "book_origin": "synthetic",
            "decision_grade": False,
            "price_decision_grade": True,
            "honesty": "DEX mid/quote may be used as price; synthetic book is not L2.",
        }
    if kind == "perp_dex":
        return {
            "exchange_id": ex,
            "fetcher_kind": "perp_dex",
            "source_class": "venue_direct",
            "truth_tier": "A",
            "book_origin": "synthetic",
            "decision_grade": False,
            "price_decision_grade": True,
            "honesty": "Perp DEX mid is venue price; synthetic book is not L2.",
        }
    return {
        "exchange_id": ex,
        "fetcher_kind": kind,
        "source_class": "enrichment",
        "truth_tier": "F",
        "book_origin": "synthetic",
        "decision_grade": False,
        "price_decision_grade": False,
    }


def l2_honesty_allowed(*, book_origin: str, source_class: str | None = None) -> bool:
    """True only for real venue L2. Aggregator/synthetic books fail the honesty gate."""
    if (book_origin or "").strip().lower() != "venue_l2":
        return False
    if source_class == "aggregator":
        return False
    return True


def classify_registry() -> dict[str, Any]:
    from data_sources_registry import DATA_SOURCES

    rows = [classify_source(spec.source_id, category=spec.category) for spec in DATA_SOURCES]
    by_role: dict[str, int] = {}
    by_class: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    for row in rows:
        by_role[row["decision_role"]] = by_role.get(row["decision_role"], 0) + 1
        by_class[row["source_class"]] = by_class.get(row["source_class"], 0) + 1
        by_tier[row["truth_tier"]] = by_tier.get(row["truth_tier"], 0) + 1
    return {
        "total_registered": len(rows),
        "decision_grade_price_sources": sum(1 for r in rows if r["price_decision_grade"]),
        "l2_decision_grade_sources": sum(1 for r in rows if r["l2_decision_grade"]),
        "by_decision_role": by_role,
        "by_source_class": by_class,
        "by_truth_tier": by_tier,
        "doctrine": (
            "Registry count is catalog size, not decision coverage. "
            "Only venue-direct L2/ticker may feed Canonical Market State."
        ),
    }
