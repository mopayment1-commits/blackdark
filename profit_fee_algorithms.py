"""
BLACKDARK — Profit/fee core algorithms (Due Diligence coverage module).

Pure functions for depth walk, spread, and fee-adjusted profit — no I/O, no engine loop.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

import config
from macro_correlations import macro_slippage_multiplier, macro_volatility_buffer_bps


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


def normalize_book(order_book: dict[str, Any]) -> dict[str, list[list[float]]]:
    bids = [[float(p), float(a)] for p, a in (order_book.get("bids") or []) if float(p) > 0 and float(a) > 0]
    asks = [[float(p), float(a)] for p, a in (order_book.get("asks") or []) if float(p) > 0 and float(a) > 0]
    return {"bids": bids, "asks": asks}


def top_ask(order_book: dict[str, Any]) -> float | None:
    asks = normalize_book(order_book)["asks"]
    return asks[0][0] if asks else None


def top_bid(order_book: dict[str, Any]) -> float | None:
    bids = normalize_book(order_book)["bids"]
    return bids[0][0] if bids else None


def gross_spread_bps(buy_ask: float, sell_bid: float) -> float:
    if buy_ask <= 0:
        return 0.0
    return (sell_bid - buy_ask) / buy_ask * 10_000


def withdrawal_fee_usdt(exchange_id: str, symbol: str) -> float | None:
    from fee_matrix import withdrawal_fee_usdt as _w

    return _w(exchange_id, symbol)


def deposit_fee_usdt(exchange_id: str, symbol: str) -> float:
    from fee_matrix import deposit_fee_usdt as _d

    return _d(exchange_id, symbol)


def slippage_buffer_usdt(
    notional: float,
    slippage_bps: float,
    market_context: dict[str, Any] | None = None,
) -> float:
    buffer_bps = macro_volatility_buffer_bps(market_context)
    multiplier = macro_slippage_multiplier(market_context)
    total_bps = (slippage_bps + buffer_bps) * multiplier
    return notional * (total_bps / 10_000)


def open_leg_fees_usdt(notional: float, exchange_id: str = "binance") -> float | None:
    from fee_matrix import trading_fees_usdt

    spot = trading_fees_usdt(exchange_id, notional, market="spot")
    perp = trading_fees_usdt(exchange_id, notional, market="perpetual")
    if spot is None or perp is None:
        return None
    return spot + perp


def funding_open_leg_fees_usdt(notional: float, exchange_id: str = "binance") -> float | None:
    from fee_matrix import trading_fees_usdt

    perp = trading_fees_usdt(exchange_id, notional, market="perpetual")
    if perp is None:
        return None
    return perp * 2


def walk_asks(order_book: dict[str, Any], quote_amount: float) -> BuyExecution | None:
    if quote_amount <= 0:
        return None
    book = normalize_book(order_book)
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
    slip = ((average_price - best_price) / best_price) * 10_000
    return BuyExecution(
        average_price=average_price,
        base_amount=base_amount,
        quote_cost=quote_cost,
        best_price=best_price,
        slippage_bps=max(0.0, slip),
        levels_consumed=levels_consumed,
    )


def walk_bids(order_book: dict[str, Any], base_amount: float) -> SellExecution | None:
    if base_amount <= 0:
        return None
    book = normalize_book(order_book)
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
    slip = ((best_price - average_price) / best_price) * 10_000
    return SellExecution(
        average_price=average_price,
        base_amount=sold_base,
        quote_value=quote_value,
        best_price=best_price,
        slippage_bps=max(0.0, slip),
        levels_consumed=levels_consumed,
    )


def net_cross_exchange_profit(
    buy_book: dict[str, Any],
    sell_book: dict[str, Any],
    *,
    buy_exchange: str,
    sell_exchange: str,
    symbol: str,
    notional: float | None = None,
    market_context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Depth-walk both legs and return net profit after trading + transfer fees."""
    quote = notional or config.DEFAULT_QUOTE_AMOUNT
    buy_exec = walk_asks(buy_book, quote)
    if buy_exec is None:
        return None
    sell_exec = walk_bids(sell_book, buy_exec.base_amount)
    if sell_exec is None:
        return None

    from fee_matrix import taker_fee
    from money_decimal import apply_fee, money_float, net_after_costs

    buy_rate = taker_fee(buy_exchange)
    sell_rate = taker_fee(sell_exchange)
    if buy_rate is None or sell_rate is None:
        return None
    buy_fee = apply_fee(buy_exec.quote_cost, buy_rate)
    sell_fee = apply_fee(sell_exec.quote_value, sell_rate)
    trading_fees = money_float(buy_fee + sell_fee)
    withdraw = withdrawal_fee_usdt(buy_exchange, symbol)
    if withdraw is None:
        # Unknown transfer cost must not invent a zero-fee false profit.
        return None
    deposit = deposit_fee_usdt(sell_exchange, symbol)
    if deposit is None:
        return None
    total_slip = buy_exec.slippage_bps + sell_exec.slippage_bps
    slip_buf = slippage_buffer_usdt(quote, total_slip, market_context)
    net_profit_dec = net_after_costs(
        sell_exec.quote_value,
        costs=[
            buy_exec.quote_cost,
            buy_fee,
            sell_fee,
            withdraw,
            deposit,
            slip_buf,
        ],
    )
    net_profit = money_float(net_profit_dec)

    buy_top = top_ask(buy_book) or buy_exec.best_price
    sell_top = top_bid(sell_book) or sell_exec.best_price

    return {
        "symbol": symbol,
        "buy_exchange": buy_exchange,
        "sell_exchange": sell_exchange,
        "quote_amount": quote,
        "gross_spread_bps": gross_spread_bps(buy_top, sell_top),
        "buy_slippage_bps": buy_exec.slippage_bps,
        "sell_slippage_bps": sell_exec.slippage_bps,
        "total_slippage_bps": total_slip,
        "trading_fees_usdt": trading_fees,
        "withdrawal_fee_usdt": money_float(withdraw),
        "deposit_fee_usdt": money_float(deposit),
        "slippage_buffer_usdt": slip_buf,
        "net_profit_usdt": net_profit,
        "net_profit_percent": (net_profit / quote) * 100 if quote else 0.0,
        "money_model": "decimal_half_even",
    }
