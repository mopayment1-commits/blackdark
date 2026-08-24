"""
Cross-chain transaction index (#101) — flexible append-only store with cursor pagination.

Designed to add chains without restructuring. Pagination uses stable sort keys:
(timestamp DESC, chain ASC, tx_hash ASC).
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.TransactionIndex")

INDEX_PATH = Path("data/cross_chain_tx_index.jsonl")


def _sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    return (
        -int(row.get("timestamp") or 0),
        str(row.get("chain") or ""),
        str(row.get("tx_hash") or ""),
    )


def append_transactions(rows: list[dict[str, Any]], *, path: Path | None = None) -> int:
    """Append normalized transactions to index (idempotent by chain+hash)."""
    target = path or INDEX_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    existing: set[str] = set()
    if target.exists():
        try:
            for line in target.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                existing.add(f"{row.get('chain')}:{row.get('tx_hash')}")
        except (OSError, json.JSONDecodeError):
            logger.debug("index read partial failure")

    written = 0
    with target.open("a", encoding="utf-8") as fh:
        for row in rows:
            key = f"{row.get('chain')}:{row.get('tx_hash')}"
            if key in existing:
                continue
            fh.write(json.dumps(row, default=str) + "\n")
            existing.add(key)
            written += 1
    return written


def load_index(*, path: Path | None = None) -> list[dict[str, Any]]:
    target = path or INDEX_PATH
    rows: list[dict[str, Any]] = []
    if not target.exists():
        return rows
    try:
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        logger.debug("index load failed")
    return rows


def encode_cursor(timestamp: int, chain: str, tx_hash: str) -> str:
    payload = {"timestamp": timestamp, "chain": chain, "tx_hash": tx_hash}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(cursor: str | None) -> dict[str, Any] | None:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode())
        data = json.loads(raw.decode())
        if not isinstance(data, dict):
            return None
        return data
    except (ValueError, json.JSONDecodeError):
        return None


def _after_cursor(row: dict[str, Any], cursor: dict[str, Any]) -> bool:
    """True if row sorts strictly after cursor position (for DESC timestamp paging)."""
    ts = int(row.get("timestamp") or 0)
    c_ts = int(cursor.get("timestamp") or 0)
    if ts < c_ts:
        return True
    if ts > c_ts:
        return False
    chain = str(row.get("chain") or "")
    c_chain = str(cursor.get("chain") or "")
    if chain > c_chain:
        return True
    if chain < c_chain:
        return False
    tx_hash = str(row.get("tx_hash") or "")
    c_hash = str(cursor.get("tx_hash") or "")
    return tx_hash > c_hash


def query_index(
    *,
    address: str | None = None,
    chains: list[str] | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    cursor: str | None = None,
    limit: int = 50,
    path: Path | None = None,
) -> dict[str, Any]:
    """Indexed filter/sort with cursor pagination — query correctness + chain/time semantics."""
    limit = max(1, min(100, limit))
    rows = load_index(path=path)
    addr_l = (address or "").lower()
    chain_set = {c.lower() for c in chains} if chains else None
    cur = decode_cursor(cursor)

    filtered: list[dict[str, Any]] = []
    for row in rows:
        if addr_l:
            from_a = str(row.get("from_address") or "").lower()
            to_a = str(row.get("to_address") or "").lower()
            if addr_l not in {from_a, to_a} and addr_l != str(row.get("address") or "").lower():
                continue
        if chain_set and str(row.get("chain") or "").lower() not in chain_set:
            continue
        ts = int(row.get("timestamp") or 0)
        if start_time is not None and ts < start_time:
            continue
        if end_time is not None and ts > end_time:
            continue
        if cur and not _after_cursor(row, cur):
            continue
        filtered.append(row)

    filtered.sort(key=_sort_key)
    page = filtered[: limit + 1]
    has_more = len(page) > limit
    results = page[:limit]

    next_cursor = None
    if has_more and results:
        last = results[-1]
        next_cursor = encode_cursor(
            int(last.get("timestamp") or 0),
            str(last.get("chain") or ""),
            str(last.get("tx_hash") or ""),
        )

    return {
        "ok": True,
        "results": results,
        "count": len(results),
        "has_more": has_more,
        "next_cursor": next_cursor,
        "query_semantics": {
            "sort": "timestamp_desc_chain_asc_hash_asc",
            "chain_filter": sorted(chain_set) if chain_set else None,
            "start_time": start_time,
            "end_time": end_time,
            "address": address,
        },
    }
