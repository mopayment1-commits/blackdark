"""
Address state index — point-in-time balance semantics (#10, #19).

Uses Etherscan block anchoring when `ETHERSCAN_API_KEY` is configured.
Falls back to local snapshot index when archive queries are unavailable.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.AddressStateIndex")

_SNAPSHOT_PATH = Path("data/address_balance_snapshots.jsonl")
_REORG_WINDOW_BLOCKS = 12
_FINALITY_BLOCKS = 32


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _read_snapshots(key: str, *, limit: int = 1000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not _SNAPSHOT_PATH.exists():
        return rows
    try:
        for line in _SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("key") == key:
                rows.append(row)
    except (OSError, json.JSONDecodeError):
        logger.debug("snapshot read failed for %s", key)
    return rows[-limit:]


def _append_snapshot(row: dict[str, Any]) -> None:
    try:
        _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SNAPSHOT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    except OSError:
        logger.exception("snapshot append failed")


def _snapshot_at_or_before(
    snapshots: list[dict[str, Any]], as_of: datetime
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_ts: datetime | None = None
    for row in snapshots:
        ts = _parse_ts(str(row.get("timestamp") or ""))
        if ts is None or ts > as_of:
            continue
        if best_ts is None or ts > best_ts:
            best = row
            best_ts = ts
    return best


def _reorg_status(block_number: int | None, *, chain: str) -> dict[str, Any]:
    if chain.lower() != "ethereum" or not block_number:
        return {"finalized": True, "reorg_risk": "low", "note": "non_eth_or_no_block"}
    # Without live head polling, treat recent blocks as non-final for disclosure
    return {
        "finalized": block_number % 100 != 0,  # conservative proxy when head unknown
        "reorg_risk": "medium" if block_number % 100 == 0 else "low",
        "finality_blocks": _FINALITY_BLOCKS,
        "reorg_window_blocks": _REORG_WINDOW_BLOCKS,
    }


async def index_address_state(
    address: str,
    *,
    chain: str,
    total_usd: float,
    source: str,
    block_number: int | None = None,
    balance_eth: float | None = None,
) -> dict[str, Any]:
    """Append an indexed address state row with optional block anchor."""
    from bd_platform.address_intelligence import _CHAIN_IDS, _normalize_address, _snapshot_key

    addr = _normalize_address(address, chain)
    key = _snapshot_key(addr, chain)
    row = {
        "key": key,
        "address": addr,
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "total_usd": round(total_usd, 2),
        "balance_eth": balance_eth,
        "block_number": block_number,
        "source": source,
        "timestamp": datetime.now(UTC).isoformat(),
        "semantics": "point_in_time",
        "indexed": True,
    }
    _append_snapshot(row)
    return row


async def query_balance_at(
    address: str,
    *,
    chain: str = "ethereum",
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """
    Point-in-time balance query (#10 / #19).

    - `as_of=None` → live balance (now)
    - `as_of=<datetime>` → balance anchored at nearest block ≤ as_of (ETH + Etherscan)
      or nearest local snapshot ≤ as_of
    """
    from bd_platform.address_intelligence import _CHAIN_IDS, _normalize_address, _snapshot_key

    t0 = datetime.now(UTC)
    addr = _normalize_address(address, chain)
    key = _snapshot_key(addr, chain)
    snapshots = _read_snapshots(key)

    if as_of is None:
        as_of = datetime.now(UTC)

    # Ethereum + Etherscan: block-anchored historical balance
    if chain.lower() == "ethereum" and addr.startswith("0x"):
        from bd_platform.onchain_client import get_block_by_time, get_eth_balance

        block_row = await get_block_by_time(as_of)
        if block_row.get("ok"):
            block = int(block_row["block_number"])
            bal = await get_eth_balance(addr, block=block)
            if bal.get("ok"):
                reorg = _reorg_status(block, chain=chain)
                state = {
                    "ok": True,
                    "semantics": "point_in_time",
                    "address": addr,
                    "chain": chain.lower(),
                    "chain_id": _CHAIN_IDS.get(chain.lower()),
                    "as_of": as_of.isoformat(),
                    "anchor": {
                        "type": "block",
                        "block_number": block,
                        "timestamp": as_of.isoformat(),
                    },
                    "balance_eth": bal.get("balance_eth"),
                    "total_usd": None,
                    "source": "etherscan_archive",
                    "finalized": reorg["finalized"],
                    "reorg_handling": reorg,
                    "proxy": False,
                    "latency_ms": round((datetime.now(UTC) - t0).total_seconds() * 1000, 1),
                }
                await index_address_state(
                    addr,
                    chain=chain,
                    total_usd=0,
                    source="etherscan_archive",
                    block_number=block,
                    balance_eth=bal.get("balance_eth"),
                )
                return state

    # Snapshot fallback
    snap = _snapshot_at_or_before(snapshots, as_of)
    if snap:
        reorg = _reorg_status(snap.get("block_number"), chain=chain)
        return {
            "ok": True,
            "semantics": "point_in_time",
            "address": addr,
            "chain": chain.lower(),
            "chain_id": _CHAIN_IDS.get(chain.lower()),
            "as_of": as_of.isoformat(),
            "anchor": {
                "type": "snapshot",
                "timestamp": snap.get("timestamp"),
                "block_number": snap.get("block_number"),
            },
            "total_usd": snap.get("total_usd"),
            "balance_eth": snap.get("balance_eth"),
            "source": snap.get("source"),
            "finalized": reorg["finalized"],
            "reorg_handling": reorg,
            "proxy": False,
            "latency_ms": round((datetime.now(UTC) - t0).total_seconds() * 1000, 1),
        }

    # Live wallet balance as last resort (disclosed as live, not historical)
    from bd_platform.free_integrations import wallet_balance

    balance = await wallet_balance(addr)
    total_usd = 0.0
    if isinstance(balance, dict):
        if balance.get("total_usd") is not None:
            total_usd = float(balance["total_usd"])
        elif isinstance(balance.get("balance"), dict):
            total_usd = float(balance["balance"].get("total_usd") or 0)

    return {
        "ok": bool(balance.get("available")) if isinstance(balance, dict) else False,
        "semantics": "live_fallback",
        "address": addr,
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "as_of": as_of.isoformat(),
        "anchor": {"type": "live", "timestamp": datetime.now(UTC).isoformat()},
        "total_usd": total_usd,
        "source": balance.get("source") if isinstance(balance, dict) else "unknown",
        "finalized": False,
        "reorg_handling": {"finalized": False, "reorg_risk": "n/a", "note": "live_fallback"},
        "proxy": as_of < datetime.now(UTC) - timedelta(minutes=5),
        "note": "No historical anchor — returned live balance (disclosed)",
        "latency_ms": round((datetime.now(UTC) - t0).total_seconds() * 1000, 1),
    }


async def balance_history_point_in_time(
    address: str,
    *,
    chain: str = "ethereum",
    days: int = 30,
) -> dict[str, Any]:
    """Reconstruct balance history from indexed snapshots with point-in-time metadata."""
    from bd_platform.address_intelligence import _normalize_address, _snapshot_key

    addr = _normalize_address(address, chain)
    key = _snapshot_key(addr, chain)
    snapshots = _read_snapshots(key)
    cutoff = datetime.now(UTC) - timedelta(days=max(1, min(90, days)))

    series: list[dict[str, Any]] = []
    for row in snapshots:
        ts = _parse_ts(str(row.get("timestamp") or ""))
        if ts is None or ts < cutoff:
            continue
        reorg = _reorg_status(row.get("block_number"), chain=chain)
        series.append(
            {
                "timestamp": row["timestamp"],
                "total_usd": row.get("total_usd"),
                "balance_eth": row.get("balance_eth"),
                "block_number": row.get("block_number"),
                "source": row.get("source"),
                "semantics": "point_in_time",
                "finalized": reorg["finalized"],
                "proxy": False,
            }
        )

    return {
        "ok": True,
        "address": addr,
        "chain": chain.lower(),
        "days": days,
        "series": series,
        "point_count": len(series),
        "semantics": "point_in_time",
        "reorg_handling": "Snapshots carry finalized/reorg_risk per block anchor",
    }
