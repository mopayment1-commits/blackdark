"""
Exchange Internal Flow Filter (BLACKDARK_CONTEXT D-09).

Classifies on-chain / exchange flows:
  INTERNAL_CONFIRMED | INTERNAL_LIKELY | ECONOMIC_FLOW | UNKNOWN
"""

from __future__ import annotations

from enum import Enum
from typing import Any

# Labeled hot-wallet clusters (expand via migration 017 + admin API)
EXCHANGE_HOT_WALLETS: dict[str, set[str]] = {
    "binance": {
        "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "34xp4vrocguyur2jqrvxduq6c9kzq387j",
    },
    "kraken": {
        "3q2s1cz2x3x5x6x7x8x9x0x1x2x3x4x5x6",
    },
    "coinbase": {
        "3kzh9qhs9fq8x4x5x6x7x8x9x0x1x2x3x4x5x6",
    },
}

# Known internal rebalance patterns (same-entity transfers)
INTERNAL_COUNTERPARTY_PAIRS: set[frozenset[str]] = {
    frozenset({"binance_hot", "binance_cold"}),
    frozenset({"kraken_hot", "kraken_cold"}),
}


class FlowClassification(str, Enum):
    INTERNAL_CONFIRMED = "INTERNAL_CONFIRMED"
    INTERNAL_LIKELY = "INTERNAL_LIKELY"
    ECONOMIC_FLOW = "ECONOMIC_FLOW"
    UNKNOWN = "UNKNOWN"


def _normalize(addr: str) -> str:
    return (addr or "").strip().lower()


def _exchange_for_address(address: str) -> str | None:
    addr = _normalize(address)
    for exchange, wallets in EXCHANGE_HOT_WALLETS.items():
        if addr in {_normalize(w) for w in wallets}:
            return exchange
    return None


def classify_flow(
    *,
    from_address: str,
    to_address: str,
    exchange: str | None = None,
    amount_usd: float | None = None,
    is_deposit: bool = False,
    is_withdrawal: bool = False,
    graph_hops: int = 0,
) -> dict[str, Any]:
    """
    Classify a transfer between addresses.

    Rules (conservative — prefer UNKNOWN over false ECONOMIC):
    - Both ends same exchange hot/cold cluster → INTERNAL_CONFIRMED
    - One end exchange hot wallet, low graph hops → INTERNAL_LIKELY
    - Clear deposit/withdrawal to user wallet → ECONOMIC_FLOW
    - Otherwise → UNKNOWN
    """
    src_ex = _exchange_for_address(from_address) or (exchange.lower() if exchange else None)
    dst_ex = _exchange_for_address(to_address)

    if src_ex and dst_ex and src_ex == dst_ex:
        return _result(
            FlowClassification.INTERNAL_CONFIRMED,
            f"both endpoints labeled {src_ex} cluster",
            confidence=0.95,
        )

    pair = frozenset({f"{src_ex}_hot" if src_ex else "unknown_src", f"{dst_ex}_hot" if dst_ex else "unknown_dst"})
    if pair in INTERNAL_COUNTERPARTY_PAIRS:
        return _result(FlowClassification.INTERNAL_CONFIRMED, "known internal counterparty pair", 0.92)

    if (src_ex or dst_ex) and graph_hops <= 1 and not is_deposit and not is_withdrawal:
        return _result(
            FlowClassification.INTERNAL_LIKELY,
            "exchange-labeled endpoint with shallow graph depth",
            0.7,
        )

    if is_deposit or is_withdrawal:
        if amount_usd is None or amount_usd > 0:
            return _result(
                FlowClassification.ECONOMIC_FLOW,
                "deposit/withdrawal path to external wallet",
                0.85,
            )

    if src_ex and not dst_ex and is_withdrawal:
        return _result(FlowClassification.ECONOMIC_FLOW, "exchange withdrawal", 0.8)
    if dst_ex and not src_ex and is_deposit:
        return _result(FlowClassification.ECONOMIC_FLOW, "exchange deposit", 0.8)

    return _result(FlowClassification.UNKNOWN, "insufficient labeling for classification", 0.0)


def _result(cls: FlowClassification, reason: str, confidence: float) -> dict[str, Any]:
    return {
        "classification": cls.value,
        "reason": reason,
        "confidence": confidence,
        "defect": "D-09",
    }
