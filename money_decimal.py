"""Canonical money math helpers (Decimal) for financial decision boundaries.

Binary float remains acceptable for market-data display and intermediate
heuristics. Settlement, fee, and net-executable-profit math that gates
execution should prefer these helpers.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any

# USDT-style quote precision for executable profit decisions.
MONEY_QUANT = Decimal("0.0001")
# Fee rates are stored as fractions (0.001 = 10 bps).
RATE_QUANT = Decimal("0.0000001")


def d(value: Any) -> Decimal:
    """Convert int/float/str/Decimal to Decimal without binary float artifacts."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        raise InvalidOperation("cannot convert None to Decimal")
    if isinstance(value, bool):
        raise InvalidOperation("bool is not a money value")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # Round-trip via str to avoid binary float expansion.
        return Decimal(str(value))
    return Decimal(str(value))


def money(value: Any) -> Decimal:
    return d(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_EVEN)


def rate(value: Any) -> Decimal:
    return d(value).quantize(RATE_QUANT, rounding=ROUND_HALF_EVEN)


def money_float(value: Any) -> float:
    return float(money(value))


def apply_fee(notional: Any, fee_rate: Any) -> Decimal:
    return money(d(notional) * rate(fee_rate))


def net_after_costs(
    proceeds: Any,
    *,
    costs: list[Any],
) -> Decimal:
    total = d(proceeds)
    for c in costs:
        total -= d(c)
    return money(total)
