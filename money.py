"""
BLACKDARK — Decimal money helpers (engineering precision).

Use for profit / fee / MRR arithmetic to avoid binary float drift.
This is NOT an IFRS 13 certification claim.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

TWOPLACES = Decimal("0.01")
FOURPLACES = Decimal("0.0001")
EIGHTPLACES = Decimal("0.00000001")


def D(value: Any) -> Decimal:
    """Parse int/float/str/Decimal into Decimal safely."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def money_round(value: Any, *, places: Decimal = TWOPLACES) -> Decimal:
    return D(value).quantize(places, rounding=ROUND_HALF_UP)


def money_str(value: Any, *, places: Decimal = TWOPLACES) -> str:
    return format(money_round(value, places=places), "f")


def money_float(value: Any, *, places: Decimal = TWOPLACES) -> float:
    """Serialize for JSON APIs that expect float."""
    return float(money_round(value, places=places))


def pct_of(amount: Any, pct: Any, *, places: Decimal = FOURPLACES) -> Decimal:
    return money_round(D(amount) * D(pct) / Decimal("100"), places=places)


def net_after_fees(gross: Any, fee_rate_pct: Any, *, places: Decimal = FOURPLACES) -> Decimal:
    """gross * (1 - fee_rate_pct/100)."""
    factor = Decimal("1") - (D(fee_rate_pct) / Decimal("100"))
    return money_round(D(gross) * factor, places=places)


def cents_to_usd(cents: Any) -> Decimal:
    return money_round(D(cents) / Decimal("100"), places=TWOPLACES)


def usd_to_cents(usd: Any) -> int:
    return int(money_round(D(usd) * Decimal("100"), places=Decimal("1")))
