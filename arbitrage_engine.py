"""
BLACKDARK — Parallel Arbitrage Engine (Phase 2: Points 3, 4, 8, 9, 10, & 31).

Evaluates cross-exchange and triangular opportunities from live order-book
snapshots with depth walking, fee deductions, and withdrawal costs.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import signal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

import config
from ai_oracle import OpportunityKind, evaluate_and_store, log_evaluated_opportunity
from database import fetch_latest_funding_rates, fetch_latest_order_books, init_db
from macro_correlations import (
    MacroCorrelationsEngine,
    macro_slippage_multiplier,
    macro_volatility_buffer_bps,
    merge_macro_context,
)
from obi_predictor import build_obi_context_safe, merge_market_context
from onchain_tracker import build_onchain_context_safe, merge_onchain_context
from parquet_compactor import (
    start_midnight_compaction_scheduler,
    stop_midnight_compaction_scheduler,
    trigger_historical_compaction_background,
)
from sentiment_engine import (
    SentimentEngine,
    load_active_sentiment_indices_for_valuation_safe,
    merge_sentiment_context,
)
from whale_tracker import WhaleTracker, build_institutional_context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("BLACKDARK.ArbitrageEngine")

Side = Literal["buy", "sell"]

WITHDRAWAL_FEE_USDT: dict[str, dict[str, float]] = {
    "binance": {
        "BTC": 4.5,
        "ETH": 1.2,
        "SOL": 0.15,
        "BNB": 0.20,
        "XRP": 0.25,
    },
    "okx": {
        "BTC": 5.0,
        "ETH": 1.5,
        "SOL": 0.18,
        "BNB": 0.22,
        "XRP": 0.30,
    },
    "bybit": {
        "BTC": 4.8,
        "ETH": 1.3,
        "SOL": 0.16,
        "BNB": 0.21,
        "XRP": 0.28,
    },
    "coinbase": {
        "BTC": 5.5,
        "ETH": 1.8,
        "SOL": 0.20,
        "BNB": 0.25,
        "XRP": 0.35,
    },
    "kraken": {
        "BTC": 5.0,
        "ETH": 1.6,
        "SOL": 0.18,
        "BNB": 0.24,
        "XRP": 0.32,
    },
    "kucoin": {
        "BTC": 5.2,
        "ETH": 1.4,
        "SOL": 0.17,
        "BNB": 0.22,
        "XRP": 0.30,
    },
    "gateio": {
        "BTC": 4.9,
        "ETH": 1.35,
        "SOL": 0.17,
        "BNB": 0.21,
        "XRP": 0.29,
    },
}


class OrderBookSide(BaseModel):
    levels: list[list[float]]

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, levels: list[list[float]]) -> list[list[float]]:
        cleaned: list[list[float]] = []
        for level in levels:
            if len(level) < 2:
                continue
            price = float(level[0])
            amount = float(level[1])
            if price <= 0 or amount <= 0:
                continue
            cleaned.append([price, amount])
        return cleaned


class BuyExecution(BaseModel):
    average_price: float = Field(gt=0)
    base_amount: float = Field(gt=0)
    quote_cost: float = Field(gt=0)
    best_price: float = Field(gt=0)
    slippage_bps: float = Field(ge=0)
    levels_consumed: int = Field(ge=1)


class SellExecution(BaseModel):
    average_price: float = Field(gt=0)
    base_amount: float = Field(gt=0)
    quote_value: float = Field(gt=0)
    best_price: float = Field(gt=0)
    slippage_bps: float = Field(ge=0)
    levels_consumed: int = Field(ge=1)


class CrossExchangeOpportunity(BaseModel):
    symbol: str
    buy_exchange: str
    sell_exchange: str
    quote_amount: float = Field(gt=0)
    buy_ask: float = Field(gt=0)
    sell_bid: float = Field(gt=0)
    gross_spread_bps: float
    buy_slippage_bps: float = Field(ge=0)
    sell_slippage_bps: float = Field(ge=0)
    total_slippage_bps: float = Field(ge=0)
    trading_fees_usdt: float = Field(ge=0)
    withdrawal_fee_usdt: float = Field(ge=0)
    slippage_buffer_usdt: float = Field(ge=0)
    net_profit_usdt: float
    net_profit_percent: float


class TriangularOpportunity(BaseModel):
    exchange: str
    path: str
    quote_amount: float = Field(gt=0)
    legs: list[tuple[str, Side]]
    gross_spread_bps: float
    total_slippage_bps: float = Field(ge=0)
    trading_fees_usdt: float = Field(ge=0)
    slippage_buffer_usdt: float = Field(ge=0)
    net_profit_usdt: float
    net_profit_percent: float


class SpotFuturesPremiumOpportunity(BaseModel):
    exchange: str
    symbol: str
    quote_amount: float = Field(gt=0)
    spot_price: float = Field(gt=0)
    futures_price: float = Field(gt=0)
    basis_bps: float
    total_slippage_bps: float = Field(ge=0)
    trading_fees_usdt: float = Field(ge=0)
    slippage_buffer_usdt: float = Field(ge=0)
    net_profit_usdt: float
    net_profit_percent: float
    direction: Literal["long_spot_short_perp", "short_spot_long_perp"]


class FundingArbitrageOpportunity(BaseModel):
    symbol: str
    long_exchange: str
    short_exchange: str
    long_funding_rate: float
    short_funding_rate: float
    funding_spread_bps: float
    quote_amount: float = Field(gt=0)
    gross_yield_usdt: float
    trading_fees_usdt: float = Field(ge=0)
    slippage_buffer_usdt: float = Field(ge=0)
    net_yield_usdt: float
    net_yield_percent: float
    base_net_yield_usdt: float = 0.0
    sii_velocity_usd: float = 0.0
    sii_acceleration_usd: float = 0.0
    sii_convergence_adjustment_usdt: float = 0.0
    predictive_convergence_score_delta: float = 0.0
    institutional_risk_buffer_usdt: float = Field(default=0.0, ge=0)
    cvvd_risk_patterns: list[str] = Field(default_factory=list)


def _parse_symbol(symbol: str) -> tuple[str, str]:
    base, quote = symbol.split("/")
    return base, quote


def _normalize_book(order_book: dict[str, Any]) -> dict[str, list[list[float]]]:
    bids = OrderBookSide(levels=order_book.get("bids") or []).levels
    asks = OrderBookSide(levels=order_book.get("asks") or []).levels
    return {"bids": bids, "asks": asks}


def _top_ask(order_book: dict[str, Any]) -> Optional[float]:
    book = _normalize_book(order_book)
    return book["asks"][0][0] if book["asks"] else None


def _top_bid(order_book: dict[str, Any]) -> Optional[float]:
    book = _normalize_book(order_book)
    return book["bids"][0][0] if book["bids"] else None


def _gross_spread_bps(buy_ask: float, sell_bid: float) -> float:
    if buy_ask <= 0:
        return 0.0
    return (sell_bid - buy_ask) / buy_ask * 10_000


def _withdrawal_fee_usdt(exchange_id: str, symbol: str) -> float:
    base, _ = _parse_symbol(symbol)
    return WITHDRAWAL_FEE_USDT.get(exchange_id, {}).get(base, 0.0)


def _slippage_buffer_usdt(
    notional: float,
    slippage_bps: float,
    market_context: dict[str, Any] | None = None,
) -> float:
    buffer_bps = macro_volatility_buffer_bps(market_context)
    multiplier = macro_slippage_multiplier(market_context)
    total_bps = (slippage_bps + buffer_bps) * multiplier
    return notional * (total_bps / 10_000)


def _perpetual_book_key(symbol: str) -> str:
    return f"{symbol}@perpetual"


def _spot_triangle_books(
    order_books: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Merge spot and cross books for triangular path discovery."""
    merged: dict[str, dict[str, dict[str, Any]]] = {}

    for exchange_id, books in order_books.items():
        merged[exchange_id] = {}
        for storage_key, book in books.items():
            market_type = book.get("market_type", "spot")
            if market_type not in {"spot", "cross"}:
                continue
            symbol = str(book.get("symbol", storage_key))
            merged[exchange_id][symbol] = book

    return merged


def _open_leg_fees_usdt(notional: float) -> float:
    """Estimated taker fees to open a spot + perpetual convergence pair."""
    return notional * (config.DEFAULT_TAKER_FEE + config.DEFAULT_FUTURES_TAKER_FEE)


def _funding_open_leg_fees_usdt(notional: float) -> float:
    """Estimated taker fees to open a two-venue perpetual funding pair."""
    return notional * config.DEFAULT_FUTURES_TAKER_FEE * 2


def walk_asks(order_book: dict[str, Any], quote_amount: float) -> Optional[BuyExecution]:
    """Walk the ask side to simulate buying base with a target quote notional."""
    if quote_amount <= 0:
        return None

    book = _normalize_book(order_book)
    asks = book["asks"]
    if not asks:
        return None

    best_price = asks[0][0]
    remaining_quote = quote_amount
    base_amount = 0.0
    quote_cost = 0.0
    levels_consumed = 0

    for price, amount in asks:
        if remaining_quote <= 0:
            break

        levels_consumed += 1
        level_quote_value = price * amount

        if remaining_quote >= level_quote_value:
            base_amount += amount
            quote_cost += level_quote_value
            remaining_quote -= level_quote_value
        else:
            partial_base = remaining_quote / price
            base_amount += partial_base
            quote_cost += remaining_quote
            remaining_quote = 0.0

    if remaining_quote > 0 or base_amount <= 0:
        return None

    average_price = quote_cost / base_amount
    slippage_bps = ((average_price - best_price) / best_price) * 10_000

    return BuyExecution(
        average_price=average_price,
        base_amount=base_amount,
        quote_cost=quote_cost,
        best_price=best_price,
        slippage_bps=max(0.0, slippage_bps),
        levels_consumed=levels_consumed,
    )


def walk_bids(order_book: dict[str, Any], base_amount: float) -> Optional[SellExecution]:
    """Walk the bid side to simulate selling a target base amount."""
    if base_amount <= 0:
        return None

    book = _normalize_book(order_book)
    bids = book["bids"]
    if not bids:
        return None

    best_price = bids[0][0]
    remaining_base = base_amount
    sold_base = 0.0
    quote_value = 0.0
    levels_consumed = 0

    for price, amount in bids:
        if remaining_base <= 0:
            break

        levels_consumed += 1

        if remaining_base >= amount:
            sold_base += amount
            quote_value += price * amount
            remaining_base -= amount
        else:
            sold_base += remaining_base
            quote_value += remaining_base * price
            remaining_base = 0.0

    if remaining_base > 0 or sold_base <= 0:
        return None

    average_price = quote_value / sold_base
    slippage_bps = ((best_price - average_price) / best_price) * 10_000

    return SellExecution(
        average_price=average_price,
        base_amount=sold_base,
        quote_value=quote_value,
        best_price=best_price,
        slippage_bps=max(0.0, slippage_bps),
        levels_consumed=levels_consumed,
    )


def _resolve_cross_leg(
    hold_coin: str,
    target_coin: str,
    available: set[str],
) -> Optional[tuple[str, Side]]:
    forward = f"{target_coin}/{hold_coin}"
    reverse = f"{hold_coin}/{target_coin}"
    if forward in available:
        return forward, "buy"
    if reverse in available:
        return reverse, "sell"
    return None


def _build_triangle_paths(available: set[str]) -> list[tuple[str, list[tuple[str, Side]]]]:
    anchor = config.TRIANGLE_ANCHOR
    paths: list[tuple[str, list[tuple[str, Side]]]] = []

    for coin_a in config.CORE_COINS:
        for coin_b in config.CORE_COINS:
            if coin_a == coin_b:
                continue

            leg1 = f"{coin_a}/{anchor}"
            leg3 = f"{coin_b}/{anchor}"
            if leg1 not in available or leg3 not in available:
                continue

            cross = _resolve_cross_leg(coin_a, coin_b, available)
            if cross is None:
                continue

            leg2_symbol, leg2_side = cross
            path_label = f"{anchor}->{coin_a}->{coin_b}->{anchor}"
            paths.append(
                (
                    path_label,
                    [
                        (leg1, "buy"),
                        (leg2_symbol, leg2_side),
                        (leg3, "sell"),
                    ],
                )
            )

    return paths


def _walk_triangle_legs(
    legs: list[tuple[str, Side]],
    books: dict[str, dict[str, Any]],
    start_amount: float,
    taker_fee: float,
    apply_fees: bool,
) -> tuple[Optional[float], float]:
    holding_coin = config.TRIANGLE_ANCHOR
    holding_amount = start_amount
    fee_mult = (1.0 - taker_fee) if apply_fees else 1.0
    total_slippage_bps = 0.0

    for symbol, side in legs:
        raw_book = books.get(symbol)
        if raw_book is None:
            return None, total_slippage_bps

        base_coin, quote_coin = _parse_symbol(symbol)

        if side == "buy":
            if holding_coin != quote_coin:
                return None, total_slippage_bps
            execution = walk_asks(raw_book, holding_amount)
            if execution is None:
                return None, total_slippage_bps
            total_slippage_bps += execution.slippage_bps
            holding_coin = base_coin
            holding_amount = execution.base_amount * fee_mult
        else:
            if holding_coin != base_coin:
                return None, total_slippage_bps
            execution = walk_bids(raw_book, holding_amount)
            if execution is None:
                return None, total_slippage_bps
            total_slippage_bps += execution.slippage_bps
            holding_coin = quote_coin
            holding_amount = execution.quote_value * fee_mult

    if holding_coin != config.TRIANGLE_ANCHOR:
        return None, total_slippage_bps

    return holding_amount, total_slippage_bps


def calculate_cross_exchange_arbitrage(
    order_books: dict[str, dict[str, dict[str, Any]]],
    quote_amount: float | None = None,
    market_context: dict[str, Any] | None = None,
) -> list[CrossExchangeOpportunity]:
    """
    Compare the same asset across all enabled exchanges (7 venues).

    Detects paths where the lowest ask on one venue is below the highest bid
    on another, then depth-walks both books to compute net-of-cost profit.
    """
    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    exchange_ids = list(config.enabled_exchanges())
    opportunities: list[CrossExchangeOpportunity] = []

    for symbol in config.SYMBOLS:
        venue_asks: list[tuple[str, float, dict[str, Any]]] = []
        venue_bids: list[tuple[str, float, dict[str, Any]]] = []

        for exchange_id in exchange_ids:
            book = order_books.get(exchange_id, {}).get(symbol)
            if book is None:
                continue

            ask = _top_ask(book)
            bid = _top_bid(book)
            if ask is None or bid is None:
                continue

            venue_asks.append((exchange_id, ask, book))
            venue_bids.append((exchange_id, bid, book))

        if len(venue_asks) < 1 or len(venue_bids) < 1:
            continue

        lowest_ask_exchange, lowest_ask, _ = min(venue_asks, key=lambda row: row[1])
        highest_bid_exchange, highest_bid, _ = max(venue_bids, key=lambda row: row[1])

        if lowest_ask_exchange == highest_bid_exchange:
            continue
        if highest_bid <= lowest_ask:
            continue

        for buy_exchange, _, buy_book in venue_asks:
            for sell_exchange, _, sell_book in venue_bids:
                if buy_exchange == sell_exchange:
                    continue

                buy_top = _top_ask(buy_book)
                sell_top = _top_bid(sell_book)
                if buy_top is None or sell_top is None or sell_top <= buy_top:
                    continue

                buy_execution = walk_asks(buy_book, notional)
                if buy_execution is None:
                    continue

                sell_execution = walk_bids(sell_book, buy_execution.base_amount)
                if sell_execution is None:
                    continue

                buy_fee = buy_execution.quote_cost * config.DEFAULT_TAKER_FEE
                sell_fee = sell_execution.quote_value * config.DEFAULT_TAKER_FEE
                trading_fees = buy_fee + sell_fee
                withdrawal_fee = _withdrawal_fee_usdt(buy_exchange, symbol)
                total_slippage_bps = (
                    buy_execution.slippage_bps + sell_execution.slippage_bps
                )
                slippage_buffer = _slippage_buffer_usdt(
                    notional,
                    total_slippage_bps,
                    market_context,
                )

                total_cost = (
                    buy_execution.quote_cost
                    + buy_fee
                    + withdrawal_fee
                    + slippage_buffer
                )
                net_profit = sell_execution.quote_value - sell_fee - total_cost
                net_profit_percent = (net_profit / notional) * 100 if notional else 0.0

                opportunities.append(
                    CrossExchangeOpportunity(
                        symbol=symbol,
                        buy_exchange=buy_exchange,
                        sell_exchange=sell_exchange,
                        quote_amount=notional,
                        buy_ask=buy_top,
                        sell_bid=sell_top,
                        gross_spread_bps=_gross_spread_bps(buy_top, sell_top),
                        buy_slippage_bps=buy_execution.slippage_bps,
                        sell_slippage_bps=sell_execution.slippage_bps,
                        total_slippage_bps=total_slippage_bps,
                        trading_fees_usdt=trading_fees,
                        withdrawal_fee_usdt=withdrawal_fee,
                        slippage_buffer_usdt=slippage_buffer,
                        net_profit_usdt=net_profit,
                        net_profit_percent=net_profit_percent,
                    )
                )

    opportunities.sort(key=lambda item: item.net_profit_usdt, reverse=True)
    return opportunities


def calculate_triangular_arbitrage(
    order_books: dict[str, dict[str, dict[str, Any]]],
    quote_amount: float | None = None,
    market_context: dict[str, Any] | None = None,
) -> list[TriangularOpportunity]:
    """
    Scan single-exchange 3-leg loops using ingested spot and cross-pair books.

    Example path: USDT -> BTC -> ETH/BTC -> ETH/USDT.
    """
    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    opportunities: list[TriangularOpportunity] = []
    triangle_books = _spot_triangle_books(order_books)

    for exchange_id in config.enabled_exchanges():
        books = triangle_books.get(exchange_id, {})
        available = set(books.keys())

        for path_label, legs in _build_triangle_paths(available):
            if any(symbol not in books for symbol, _ in legs):
                continue

            gross_final, slippage_bps = _walk_triangle_legs(
                legs,
                books,
                start_amount=notional,
                taker_fee=config.DEFAULT_TAKER_FEE,
                apply_fees=False,
            )
            net_final, _ = _walk_triangle_legs(
                legs,
                books,
                start_amount=notional,
                taker_fee=config.DEFAULT_TAKER_FEE,
                apply_fees=True,
            )

            if gross_final is None or net_final is None:
                continue

            gross_spread_bps = ((gross_final - notional) / notional) * 10_000
            trading_fees = max(0.0, gross_final - net_final)
            slippage_buffer = _slippage_buffer_usdt(notional, slippage_bps, market_context)
            net_profit = net_final - notional - slippage_buffer
            net_profit_percent = (net_profit / notional) * 100 if notional else 0.0

            opportunities.append(
                TriangularOpportunity(
                    exchange=exchange_id,
                    path=path_label,
                    quote_amount=notional,
                    legs=legs,
                    gross_spread_bps=gross_spread_bps,
                    total_slippage_bps=slippage_bps,
                    trading_fees_usdt=trading_fees,
                    slippage_buffer_usdt=slippage_buffer,
                    net_profit_usdt=net_profit,
                    net_profit_percent=net_profit_percent,
                )
            )

    opportunities.sort(key=lambda item: item.net_profit_usdt, reverse=True)
    return opportunities


def calculate_spot_futures_premium(
    order_books: dict[str, dict[str, dict[str, Any]]],
    quote_amount: float | None = None,
    market_context: dict[str, Any] | None = None,
) -> list[SpotFuturesPremiumOpportunity]:
    """
    Detect executable spot-perpetual basis dislocations on each exchange.

    Positive basis: futures rich -> long spot, short perp.
    Negative basis: futures cheap -> short spot, long perp.
    """
    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    opportunities: list[SpotFuturesPremiumOpportunity] = []

    for exchange_id in config.enabled_exchanges():
        books = order_books.get(exchange_id, {})
        for symbol in config.SYMBOLS:
            spot_book = books.get(symbol)
            perp_book = books.get(_perpetual_book_key(symbol))
            if spot_book is None or perp_book is None:
                continue
            if spot_book.get("market_type", "spot") != "spot":
                continue

            spot_ask = _top_ask(spot_book)
            spot_bid = _top_bid(spot_book)
            perp_ask = _top_ask(perp_book)
            perp_bid = _top_bid(perp_book)
            if None in (spot_ask, spot_bid, perp_ask, perp_bid):
                continue

            spot_mid = (spot_ask + spot_bid) / 2
            perp_mid = (perp_ask + perp_bid) / 2
            basis_bps = ((perp_mid - spot_mid) / spot_mid) * 10_000

            if basis_bps >= 0:
                direction: Literal["long_spot_short_perp", "short_spot_long_perp"] = (
                    "long_spot_short_perp"
                )
                buy_execution = walk_asks(spot_book, notional)
                if buy_execution is None:
                    continue
                sell_execution = walk_bids(perp_book, buy_execution.base_amount)
            else:
                direction = "short_spot_long_perp"
                buy_execution = walk_asks(perp_book, notional)
                if buy_execution is None:
                    continue
                sell_execution = walk_bids(spot_book, buy_execution.base_amount)

            if sell_execution is None:
                continue

            total_slippage_bps = buy_execution.slippage_bps + sell_execution.slippage_bps
            trading_fees = _open_leg_fees_usdt(notional)
            slippage_buffer = _slippage_buffer_usdt(
                notional,
                total_slippage_bps,
                market_context,
            )
            gross_edge = sell_execution.quote_value - buy_execution.quote_cost
            net_profit = gross_edge - trading_fees - slippage_buffer
            net_profit_percent = (net_profit / notional) * 100 if notional else 0.0

            opportunities.append(
                SpotFuturesPremiumOpportunity(
                    exchange=exchange_id,
                    symbol=symbol,
                    quote_amount=notional,
                    spot_price=spot_mid,
                    futures_price=perp_mid,
                    basis_bps=basis_bps,
                    total_slippage_bps=total_slippage_bps,
                    trading_fees_usdt=trading_fees,
                    slippage_buffer_usdt=slippage_buffer,
                    net_profit_usdt=net_profit,
                    net_profit_percent=net_profit_percent,
                    direction=direction,
                )
            )

    opportunities.sort(key=lambda item: item.net_profit_usdt, reverse=True)
    return opportunities


def calculate_funding_arbitrage(
    funding_rates: dict[str, dict[str, dict[str, Any]]],
    quote_amount: float | None = None,
    market_context: dict[str, Any] | None = None,
) -> list[FundingArbitrageOpportunity]:
    """
    Find cross-venue funding spreads suitable for delta-neutral convergence trades.

    Short the highest funding venue and long the lowest funding venue to harvest
    the differential after fees and slippage buffer.
    """
    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    opportunities: list[FundingArbitrageOpportunity] = []

    for symbol in config.perpetual_symbols():
        venue_rates: list[tuple[str, float]] = []

        for exchange_id in config.enabled_exchanges():
            row = funding_rates.get(exchange_id, {}).get(symbol)
            if row is None:
                continue
            venue_rates.append((exchange_id, float(row["funding_rate"])))

        if len(venue_rates) < 2:
            continue

        short_exchange, short_rate = max(venue_rates, key=lambda item: item[1])
        long_exchange, long_rate = min(venue_rates, key=lambda item: item[1])

        if short_exchange == long_exchange:
            continue

        funding_spread = short_rate - long_rate
        funding_spread_bps = funding_spread * 10_000

        if funding_spread_bps < config.MIN_FUNDING_SPREAD_BPS:
            continue

        gross_yield = notional * funding_spread
        trading_fees = _funding_open_leg_fees_usdt(notional)
        slippage_buffer = _slippage_buffer_usdt(notional, 0.0, market_context)
        net_yield = gross_yield - trading_fees - slippage_buffer
        net_yield_percent = (net_yield / notional) * 100 if notional else 0.0

        opportunities.append(
            FundingArbitrageOpportunity(
                symbol=symbol,
                long_exchange=long_exchange,
                short_exchange=short_exchange,
                long_funding_rate=long_rate,
                short_funding_rate=short_rate,
                funding_spread_bps=funding_spread_bps,
                quote_amount=notional,
                gross_yield_usdt=gross_yield,
                trading_fees_usdt=trading_fees,
                slippage_buffer_usdt=slippage_buffer,
                net_yield_usdt=net_yield,
                net_yield_percent=net_yield_percent,
                base_net_yield_usdt=net_yield,
            )
        )

    opportunities.sort(key=lambda item: item.net_yield_usdt, reverse=True)
    return opportunities


def _sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset, "Unclassified")


def _safe_parse_metadata(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        if isinstance(raw, dict):
            return raw
        return json.loads(str(raw))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _extract_sector_sii_metrics(
    institutional_context: dict[str, Any],
    sector: str,
) -> tuple[float, float, float]:
    """
    Return (velocity_usd, acceleration_usd, sii_score) for a sector.

    Falls back to neutral zeros when data is missing or malformed.
    """
    sector_rows = institutional_context.get("sector_inflow_index") or institutional_context.get(
        "sector_flows", []
    )
    for row in sector_rows:
        if str(row.get("sector") or "") != sector:
            continue
        meta = _safe_parse_metadata(row.get("metadata_json"))
        velocity = float(meta.get("flow_velocity_usd") or 0.0)
        acceleration = float(meta.get("flow_acceleration_usd") or 0.0)
        sii_score = float(meta.get("sii_score") or row.get("net_flow_usd") or 0.0)
        return velocity, acceleration, sii_score
    return 0.0, 0.0, 0.0


def _collect_cvvd_risk_patterns(
    institutional_context: dict[str, Any],
    *,
    sector: str,
    asset: str,
) -> tuple[list[str], float]:
    """
    Collect high-risk CVVD patterns affecting the target sector or asset.

    Returns matched pattern names and the highest manipulation score observed.
    """
    alerts = institutional_context.get("manipulation_alerts") or institutional_context.get(
        "whale_alerts", []
    )
    high_risk = set(config.FUNDING_CVVD_HIGH_RISK_PATTERNS)
    patterns: list[str] = []
    max_score = 0.0

    for alert in alerts:
        alert_sector = str(alert.get("sector") or "")
        alert_asset = str(alert.get("asset") or "")
        if alert_sector != sector and alert_asset != asset:
            continue

        meta = _safe_parse_metadata(alert.get("metadata_json"))
        pattern = str(meta.get("pattern") or "")
        if pattern not in high_risk:
            continue

        score = float(meta.get("manipulation_score") or alert.get("notional_usd") or 0.0)
        if score < config.CVVD_MIN_MANIPULATION_SCORE:
            continue

        if pattern not in patterns:
            patterns.append(pattern)
        max_score = max(max_score, score)

    return patterns, max_score


def _compute_predictive_funding_convergence(
    *,
    sii_velocity_usd: float,
    sii_acceleration_usd: float,
    funding_spread_bps: float,
    notional: float,
) -> tuple[float, float]:
    """
    Predictive funding convergence model driven by sector capital acceleration.

    Positive sector velocity/acceleration boosts expected convergence capture;
    negative readings penalize the opportunity.
    """
    if notional <= 0 or funding_spread_bps < config.MIN_FUNDING_SPREAD_BPS:
        return 0.0, 0.0

    velocity_signal = math.tanh(sii_velocity_usd / config.SII_VELOCITY_SCALE_USD)
    acceleration_signal = math.tanh(sii_acceleration_usd / config.SII_ACCELERATION_SCALE_USD)
    combined_signal = (
        velocity_signal * config.FUNDING_SII_VELOCITY_WEIGHT
        + acceleration_signal * config.FUNDING_SII_ACCELERATION_WEIGHT
    )

    usd_adjustment = notional * (combined_signal * config.FUNDING_SII_CONVERGENCE_BPS) / 10_000
    score_delta = combined_signal * config.FUNDING_SII_SCORE_BOOST_MAX
    return round(usd_adjustment, 6), round(score_delta, 4)


def _compute_cvvd_risk_buffer_usdt(
    *,
    notional: float,
    max_manipulation_score: float,
) -> float:
    """Institutional capital protection buffer scaled by CVVD severity."""
    if notional <= 0 or max_manipulation_score <= 0:
        return 0.0

    severity_ratio = min(1.0, max_manipulation_score / 100.0)
    buffer_bps = min(
        config.FUNDING_CVVD_RISK_BUFFER_MAX_BPS,
        config.FUNDING_CVVD_RISK_BUFFER_BPS
        + severity_ratio * config.FUNDING_CVVD_RISK_BUFFER_MAX_BPS,
    )
    return round(notional * buffer_bps / 10_000, 6)


def _enrich_funding_opportunity_with_institutional_context(
    opportunity: FundingArbitrageOpportunity,
    institutional_context: dict[str, Any] | None,
) -> FundingArbitrageOpportunity:
    """
    Apply SII convergence adjustments and CVVD risk buffers to one funding opp.

    Pure function with safe defaults when institutional context is unavailable.
    """
    if institutional_context is None:
        return opportunity.model_copy(update={"base_net_yield_usdt": opportunity.net_yield_usdt})

    asset = _parse_symbol(opportunity.symbol)[0]
    sector = _sector_for_asset(asset)

    sii_velocity, sii_acceleration, _ = _extract_sector_sii_metrics(institutional_context, sector)
    sii_adjustment_usd, score_delta = _compute_predictive_funding_convergence(
        sii_velocity_usd=sii_velocity,
        sii_acceleration_usd=sii_acceleration,
        funding_spread_bps=opportunity.funding_spread_bps,
        notional=opportunity.quote_amount,
    )

    cvvd_patterns, max_cvvd_score = _collect_cvvd_risk_patterns(
        institutional_context,
        sector=sector,
        asset=asset,
    )
    risk_buffer = _compute_cvvd_risk_buffer_usdt(
        notional=opportunity.quote_amount,
        max_manipulation_score=max_cvvd_score,
    )

    adjusted_net = opportunity.net_yield_usdt + sii_adjustment_usd - risk_buffer
    adjusted_pct = (adjusted_net / opportunity.quote_amount) * 100 if opportunity.quote_amount else 0.0

    return opportunity.model_copy(
        update={
            "base_net_yield_usdt": opportunity.net_yield_usdt,
            "sii_velocity_usd": round(sii_velocity, 2),
            "sii_acceleration_usd": round(sii_acceleration, 2),
            "sii_convergence_adjustment_usdt": sii_adjustment_usd,
            "predictive_convergence_score_delta": score_delta,
            "institutional_risk_buffer_usdt": risk_buffer,
            "cvvd_risk_patterns": cvvd_patterns,
            "net_yield_usdt": round(adjusted_net, 6),
            "net_yield_percent": round(adjusted_pct, 6),
        }
    )


def enrich_funding_opportunities_with_institutional_context(
    opportunities: list[FundingArbitrageOpportunity],
    institutional_context: dict[str, Any] | None,
) -> list[FundingArbitrageOpportunity]:
    """
    Enrich funding opportunities with CVVD/SII analytics.

    Each opportunity is isolated in its own exception boundary so analytical
    edge cases never interrupt the main arbitrage execution loop.
    """
    if not opportunities:
        return opportunities

    enriched: list[FundingArbitrageOpportunity] = []
    for opportunity in opportunities:
        try:
            enriched.append(
                _enrich_funding_opportunity_with_institutional_context(
                    opportunity,
                    institutional_context,
                )
            )
        except Exception:
            logger.exception(
                "Funding institutional enrichment failed | symbol=%s long=%s short=%s",
                opportunity.symbol,
                opportunity.long_exchange,
                opportunity.short_exchange,
            )
            enriched.append(opportunity)
    return enriched


def calculate_funding_arbitrage_with_institutional_context(
    funding_rates: dict[str, dict[str, dict[str, Any]]],
    quote_amount: float | None = None,
    institutional_context: dict[str, Any] | None = None,
    market_context: dict[str, Any] | None = None,
) -> list[FundingArbitrageOpportunity]:
    """Funding scan plus CVVD/SII enrichment with top-level exception isolation."""
    try:
        opportunities = calculate_funding_arbitrage(
            funding_rates,
            quote_amount,
            market_context,
        )
        return enrich_funding_opportunities_with_institutional_context(
            opportunities,
            institutional_context,
        )
    except Exception:
        logger.exception("Funding arbitrage module failed; returning empty result set.")
        return []


def _log_cross_opportunity(opportunity: CrossExchangeOpportunity) -> None:
    logger.info(
        "Cross-exchange opportunity | %s | buy=%s sell=%s | "
        "gross=%.2f bps | net=$%.4f (%.4f%%) | fees=$%.4f | "
        "withdraw=$%.4f | slippage=%.2f bps",
        opportunity.symbol,
        opportunity.buy_exchange,
        opportunity.sell_exchange,
        opportunity.gross_spread_bps,
        opportunity.net_profit_usdt,
        opportunity.net_profit_percent,
        opportunity.trading_fees_usdt,
        opportunity.withdrawal_fee_usdt,
        opportunity.total_slippage_bps,
    )


def _log_triangular_opportunity(opportunity: TriangularOpportunity) -> None:
    logger.info(
        "Triangular opportunity | %s @ %s | gross=%.2f bps | "
        "net=$%.4f (%.4f%%) | fees=$%.4f | slippage=%.2f bps",
        opportunity.path,
        opportunity.exchange,
        opportunity.gross_spread_bps,
        opportunity.net_profit_usdt,
        opportunity.net_profit_percent,
        opportunity.trading_fees_usdt,
        opportunity.total_slippage_bps,
    )


def _log_spot_futures_opportunity(opportunity: SpotFuturesPremiumOpportunity) -> None:
    logger.info(
        "Spot-futures premium | %s @ %s | direction=%s | basis=%.2f bps | "
        "net=$%.4f (%.4f%%) | fees=$%.4f | slippage=%.2f bps",
        opportunity.symbol,
        opportunity.exchange,
        opportunity.direction,
        opportunity.basis_bps,
        opportunity.net_profit_usdt,
        opportunity.net_profit_percent,
        opportunity.trading_fees_usdt,
        opportunity.total_slippage_bps,
    )


def _log_funding_opportunity(opportunity: FundingArbitrageOpportunity) -> None:
    logger.info(
        "Funding convergence | %s | long=%s (%.5f) short=%s (%.5f) | "
        "spread=%.2f bps | base_net=$%.4f | sii_adj=$%.4f | cvvd_buffer=$%.4f | "
        "net=$%.4f (%.4f%%) | score_delta=%+.2f | cvvd=%s",
        opportunity.symbol,
        opportunity.long_exchange,
        opportunity.long_funding_rate,
        opportunity.short_exchange,
        opportunity.short_funding_rate,
        opportunity.funding_spread_bps,
        opportunity.base_net_yield_usdt or opportunity.net_yield_usdt,
        opportunity.sii_convergence_adjustment_usdt,
        opportunity.institutional_risk_buffer_usdt,
        opportunity.net_yield_usdt,
        opportunity.net_yield_percent,
        opportunity.predictive_convergence_score_delta,
        ",".join(opportunity.cvvd_risk_patterns) or "none",
    )


async def _evaluate_positive_opportunities(
    opportunities: list[Any],
    kind: OpportunityKind,
    institutional_context: dict[str, Any] | None = None,
) -> None:
    for opportunity in opportunities:
        net_value = float(
            getattr(opportunity, "net_profit_usdt", getattr(opportunity, "net_yield_usdt", 0.0))
        )
        if net_value <= 0:
            continue
        try:
            evaluated = await evaluate_and_store(opportunity, kind, institutional_context)
            log_evaluated_opportunity(evaluated)
        except Exception:
            logger.exception("AI evaluation failed | kind=%s", kind)
            if kind == "cross_exchange":
                _log_cross_opportunity(opportunity)
            elif kind == "triangular":
                _log_triangular_opportunity(opportunity)
            elif kind == "spot_futures":
                _log_spot_futures_opportunity(opportunity)
            else:
                _log_funding_opportunity(opportunity)


class ArbitrageEngine:
    """Reads latest database snapshots and evaluates arbitrage paths."""

    def __init__(self, quote_amount: float | None = None) -> None:
        self.quote_amount = quote_amount or config.DEFAULT_QUOTE_AMOUNT
        self._shutdown = asyncio.Event()
        self._whale_tracker = WhaleTracker()
        self._sentiment_engine = SentimentEngine()
        self._macro_engine = MacroCorrelationsEngine()

    async def close(self) -> None:
        await self._whale_tracker.close()
        await self._sentiment_engine.close()
        await self._macro_engine.close()

    async def process_snapshot(
        self,
        order_books: dict[str, dict[str, dict[str, Any]]],
        funding_rates: dict[str, dict[str, dict[str, Any]]],
        institutional_context: dict[str, Any] | None = None,
    ) -> tuple[
        list[CrossExchangeOpportunity],
        list[TriangularOpportunity],
        list[SpotFuturesPremiumOpportunity],
        list[FundingArbitrageOpportunity],
    ]:
        cross = calculate_cross_exchange_arbitrage(
            order_books,
            self.quote_amount,
            institutional_context,
        )
        triangular = calculate_triangular_arbitrage(
            order_books,
            self.quote_amount,
            institutional_context,
        )
        basis = calculate_spot_futures_premium(
            order_books,
            self.quote_amount,
            institutional_context,
        )
        funding = calculate_funding_arbitrage_with_institutional_context(
            funding_rates,
            self.quote_amount,
            institutional_context,
            institutional_context,
        )

        await _evaluate_positive_opportunities(cross, "cross_exchange", institutional_context)
        await _evaluate_positive_opportunities(triangular, "triangular", institutional_context)
        await _evaluate_positive_opportunities(basis, "spot_futures", institutional_context)
        await _evaluate_positive_opportunities(funding, "funding", institutional_context)

        return cross, triangular, basis, funding

    async def run_once(
        self,
    ) -> tuple[
        list[CrossExchangeOpportunity],
        list[TriangularOpportunity],
        list[SpotFuturesPremiumOpportunity],
        list[FundingArbitrageOpportunity],
    ]:
        order_books = await fetch_latest_order_books()
        funding_rates = await fetch_latest_funding_rates()
        if not order_books:
            logger.warning("No order-book snapshots available; skipping cycle.")
            return [], [], [], []

        institutional_context: dict[str, Any] | None = None
        try:
            whale_cycle = await self._whale_tracker.run_cycle()
            institutional_context = build_institutional_context(
                whale_cycle.get("whale_alerts", []),
                whale_cycle.get("sector_flows", []),
            )
        except Exception:
            logger.exception("Whale tracker cycle failed; continuing without institutional context.")

        obi_context = await build_obi_context_safe(order_books)
        onchain_context = await build_onchain_context_safe()
        market_context = merge_onchain_context(
            merge_market_context(institutional_context, obi_context),
            onchain_context,
        )

        try:
            await self._sentiment_engine.run_cycle()
        except Exception:
            logger.exception("Sentiment cycle failed; continuing without fresh sentiment context.")

        try:
            sentiment_context = await load_active_sentiment_indices_for_valuation_safe()
            market_context = merge_sentiment_context(market_context, sentiment_context)
            panic_assets = sentiment_context.get("sentiment_panic_assets") or {}
            if sentiment_context.get("sentiment_compound_index"):
                logger.info(
                    "Sentiment indices loaded for valuation | assets=%d panic=%d",
                    len(sentiment_context.get("sentiment_compound_index", {})),
                    len(panic_assets),
                )
            if panic_assets:
                logger.warning(
                    "Extreme negative sentiment detected | assets=%s",
                    ", ".join(
                        f"{asset}:{score:+.2f}" for asset, score in panic_assets.items()
                    ),
                )
        except Exception:
            logger.exception(
                "Sentiment valuation index load failed; continuing without sentiment context."
            )

        try:
            macro_context = await self._macro_engine.run_cycle()
            market_context = merge_macro_context(market_context, macro_context)
            logger.info(
                "Macro regime loaded | regime=%s dxy=%+.3f spx=%+.3f buffer=%.1fbps",
                macro_context.get("macro_regime"),
                float(macro_context.get("macro_dxy_score", 0.0)),
                float(macro_context.get("macro_spx_score", 0.0)),
                float(macro_context.get("macro_volatility_buffer", 0.0)),
            )
        except Exception:
            logger.exception(
                "Macro regime load failed; continuing without macro context."
            )

        try:
            from oracle_data_hub import build_hub_context_safe, merge_hub_context

            hub_context = await build_hub_context_safe("BTC")
            market_context = merge_hub_context(market_context, hub_context)
            if hub_context.get("enabled"):
                logger.info(
                    "Oracle data hub loaded | pillars=%d fg=%s geo=%s",
                    len(hub_context.get("pillars") or []),
                    (hub_context.get("sentiment") or {}).get("fear_greed_index"),
                    (hub_context.get("geo_news") or {}).get("geopolitical_headline_count"),
                )
        except Exception:
            logger.exception("Oracle data hub load failed; continuing without hub context.")

        if obi_context.get("obi_warnings"):
            logger.info(
                "OBI warnings active | count=%d",
                len(obi_context.get("obi_warnings", [])),
            )
        if onchain_context.get("onchain_signals"):
            logger.info(
                "On-chain signals active | count=%d",
                len(onchain_context.get("onchain_signals", [])),
            )

        return await self.process_snapshot(
            order_books,
            funding_rates,
            market_context,
        )

    async def run_loop(self) -> None:
        await init_db()
        self._register_signal_handlers()

        if config.PARQUET_COMPACTION_ENABLED:
            try:
                await start_midnight_compaction_scheduler()
                logger.info(
                    "Midnight parquet compaction scheduler enabled | output=%s",
                    config.HISTORICAL_PARQUET_DIR,
                )
            except Exception:
                logger.exception(
                    "Failed to start parquet compaction scheduler; engine loop continues."
                )

        logger.info(
            "Arbitrage engine started | quote_amount=$%.2f interval=%ss",
            self.quote_amount,
            config.POLL_INTERVAL_SECONDS,
        )

        try:
            while not self._shutdown.is_set():
                try:
                    await self.run_once()
                except Exception:
                    logger.exception("Arbitrage cycle failed; continuing.")

                if config.SQLITE_HISTORICAL_COMPACTION_ENABLED:
                    try:
                        trigger_historical_compaction_background()
                    except Exception:
                        logger.exception(
                            "Background historical compaction trigger failed; continuing."
                        )

                try:
                    await asyncio.wait_for(
                        self._shutdown.wait(),
                        timeout=config.POLL_INTERVAL_SECONDS,
                    )
                except asyncio.TimeoutError:
                    continue
        finally:
            if config.PARQUET_COMPACTION_ENABLED:
                try:
                    await stop_midnight_compaction_scheduler()
                except Exception:
                    logger.exception("Failed to stop parquet compaction scheduler.")

        logger.info("Arbitrage engine shutdown complete.")
        await self.close()

    def _register_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()

        def _request_shutdown() -> None:
            if not self._shutdown.is_set():
                logger.info("Shutdown signal received.")
                self._shutdown.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _request_shutdown)
            except NotImplementedError:
                signal.signal(sig, lambda _signum, _frame: _request_shutdown())


async def run_arbitrage_engine(quote_amount: float | None = None) -> None:
    engine = ArbitrageEngine(quote_amount=quote_amount)
    await engine.run_loop()


def main() -> None:
    try:
        asyncio.run(run_arbitrage_engine())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received; exiting.")


if __name__ == "__main__":
    main()
