"""Canonical cross-chain transaction/balance schema — add chains without restructuring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedTransaction:
    tx_hash: str
    chain: str
    chain_id: int | str
    from_address: str
    to_address: str
    value_native: float
    value_usd: float | None
    token_symbol: str | None
    timestamp: int
    block_number: int | None
    direction: str | None
    action_type: str
    source: str
    semantics: str = "point_in_time"
    raw_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedAssetBalance:
    chain: str
    chain_id: int | str
    address: str
    symbol: str
    balance: float
    balance_usd: float | None
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_evm_tx(row: dict[str, Any], *, chain: str, chain_id: int, source: str) -> NormalizedTransaction | None:
    tx_hash = str(row.get("hash") or row.get("transactionHash") or "").strip()
    if not tx_hash:
        return None
    try:
        ts = int(row.get("timeStamp") or row.get("timestamp") or 0)
    except (TypeError, ValueError):
        ts = 0
    try:
        value_wei = float(row.get("value") or 0)
    except (TypeError, ValueError):
        value_wei = 0.0
    value_native = value_wei / 1e18
    try:
        block_number = int(row.get("blockNumber") or row.get("block") or 0) or None
    except (TypeError, ValueError):
        block_number = None
    from_addr = str(row.get("from") or "").lower()
    to_addr = str(row.get("to") or "").lower()
    return NormalizedTransaction(
        tx_hash=tx_hash,
        chain=chain,
        chain_id=chain_id,
        from_address=from_addr,
        to_address=to_addr,
        value_native=round(value_native, 12),
        value_usd=None,
        token_symbol=row.get("tokenSymbol") or row.get("token_symbol"),
        timestamp=ts,
        block_number=block_number,
        direction=None,
        action_type=str(row.get("action_type") or "transfer"),
        source=source,
        raw_meta={"is_error": str(row.get("isError") or "0") == "1"},
    )


def normalize_tron_tx(row: dict[str, Any], *, source: str) -> NormalizedTransaction | None:
    tx_hash = str(row.get("hash") or row.get("txID") or "").strip()
    if not tx_hash:
        return None
    try:
        ts = int((row.get("timestamp") or 0)) // 1000 if int(row.get("timestamp") or 0) > 10_000_000_000 else int(row.get("timestamp") or 0)
    except (TypeError, ValueError):
        ts = 0
    owner = str(row.get("ownerAddress") or row.get("from") or "")
    to_addr = str(row.get("toAddress") or row.get("to") or "")
    try:
        amount = float(row.get("amount") or row.get("contractData", {}).get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    # Tron amounts often in sun (1e6) for TRX transfers
    value_native = amount / 1e6 if amount > 1_000_000 else amount
    return NormalizedTransaction(
        tx_hash=tx_hash,
        chain="tron",
        chain_id="tron",
        from_address=owner,
        to_address=to_addr,
        value_native=round(value_native, 6),
        value_usd=None,
        token_symbol=row.get("tokenAbbr") or row.get("tokenName") or "TRX",
        timestamp=ts,
        block_number=int(row.get("block") or 0) or None,
        direction=None,
        action_type=str(row.get("contractType") or row.get("action_type") or "transfer"),
        source=source,
        raw_meta={"confirmed": row.get("confirmed")},
    )


def normalize_solana_sig(row: dict[str, Any], *, source: str) -> NormalizedTransaction | None:
    tx_hash = str(row.get("signature") or row.get("tx_hash") or "").strip()
    if not tx_hash:
        return None
    try:
        ts = int(row.get("blockTime") or row.get("timestamp") or 0)
    except (TypeError, ValueError):
        ts = 0
    return NormalizedTransaction(
        tx_hash=tx_hash,
        chain="solana",
        chain_id="solana",
        from_address=str(row.get("from") or row.get("feePayer") or ""),
        to_address=str(row.get("to") or ""),
        value_native=float(row.get("lamports") or 0) / 1e9 if row.get("lamports") else 0.0,
        value_usd=None,
        token_symbol="SOL",
        timestamp=ts,
        block_number=int(row.get("slot") or 0) or None,
        direction=None,
        action_type="solana_transaction",
        source=source,
        raw_meta=row.get("meta") or {},
    )
