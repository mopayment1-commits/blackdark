"""Financial arithmetic — Decimal/minor units only (BILL-031)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

ZERO_DECIMAL_CURRENCIES = frozenset({"jpy", "krw", "vnd", "clp"})


def to_minor_units(amount: Decimal | str | float | int, currency: str = "usd") -> int:
    cur = (currency or "usd").lower()
    dec = Decimal(str(amount))
    if cur in ZERO_DECIMAL_CURRENCIES:
        return int(dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_minor_units(minor: int, currency: str = "usd") -> Decimal:
    cur = (currency or "usd").lower()
    if cur in ZERO_DECIMAL_CURRENCIES:
        return Decimal(minor)
    return (Decimal(minor) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def add_minor(a: int, b: int) -> int:
    return int(a) + int(b)


def subtract_minor(a: int, b: int) -> int:
    return int(a) - int(b)


def proration_credit(
    *,
    old_amount_minor: int,
    new_amount_minor: int,
    period_start_ts: int,
    period_end_ts: int,
    change_ts: int,
) -> int:
    """Independent proration oracle — unused period credit on upgrade."""
    if period_end_ts <= period_start_ts:
        return 0
    total = period_end_ts - period_start_ts
    remaining = max(0, period_end_ts - change_ts)
    unused_fraction = Decimal(remaining) / Decimal(total)
    credit = (Decimal(old_amount_minor) * unused_fraction).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(credit)


def invoice_total_minor(
    *,
    subtotal_minor: int,
    tax_minor: int = 0,
    discount_minor: int = 0,
) -> int:
    return max(0, int(subtotal_minor) + int(tax_minor) - int(discount_minor))


def validate_no_float_amounts(payload: dict[str, Any]) -> list[str]:
    """Scan payload for float financial fields — returns violation paths."""
    violations: list[str] = []
    float_keys = ("amount", "total", "subtotal", "tax", "discount", "price")

    def walk(obj: Any, prefix: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f"{prefix}.{k}" if prefix else k
                if any(fk in k.lower() for fk in float_keys) and isinstance(v, float):
                    violations.append(path)
                else:
                    walk(v, path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{prefix}[{i}]")

    walk(payload, "")
    return violations
