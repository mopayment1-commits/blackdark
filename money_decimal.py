"""Canonical money math helpers (Decimal) for financial decision boundaries.

Binary float remains acceptable for market-data display and intermediate
heuristics. Settlement, fee, and net-executable-profit math that gates
execution should prefer these helpers.

Financial Precision Policy (#1032): crypto=8dp · fiat=2dp · round-half-up.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Literal

# USDT-style quote precision for executable profit decisions (legacy half-even).
MONEY_QUANT = Decimal("0.0001")
# Fee rates are stored as fractions (0.001 = 10 bps).
RATE_QUANT = Decimal("0.0000001")
# Policy #1032 — per asset type (round-half-up).
CRYPTO_QUANT = Decimal("0.00000001")  # 8 decimal places
FIAT_QUANT = Decimal("0.01")  # 2 decimal places
METHODOLOGY_VERSION = "1.0.0"

AssetType = Literal["crypto", "fiat", "rate"]


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


def crypto_money(value: Any) -> Decimal:
    """Crypto settlement — 8 decimal places, round-half-up (#1032)."""
    return d(value).quantize(CRYPTO_QUANT, rounding=ROUND_HALF_UP)


def fiat_money(value: Any) -> Decimal:
    """Fiat settlement — 2 decimal places, round-half-up (#1032)."""
    return d(value).quantize(FIAT_QUANT, rounding=ROUND_HALF_UP)


def quantize_asset(value: Any, asset_type: AssetType = "crypto") -> Decimal:
    if asset_type == "fiat":
        return fiat_money(value)
    if asset_type == "rate":
        return rate(value)
    return crypto_money(value)


def financial_audit_metadata(
    *,
    asset_type: AssetType = "crypto",
    rounding_method: str = "round_half_up",
) -> dict[str, Any]:
    """Provenance #945 — type + precision + rounding for financial calculations."""
    precision = 8 if asset_type == "crypto" else 2 if asset_type == "fiat" else 7
    return {
        "type_used": "Decimal",
        "precision": precision,
        "rounding_method": rounding_method,
        "methodology_version": METHODOLOGY_VERSION,
        "financial_precision_ref": 1032,
    }


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
