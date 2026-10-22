"""
Blockscout public REST API v2 (no API key) — multi-chain address & transactions.

Rate-limited client; use as fallback after Etherscan on supported EVM chains.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

from config import (
    BLOCKSCOUT_CACHE_TTL_SEC,
    BLOCKSCOUT_DAILY_LIMIT,
    BLOCKSCOUT_RPS_LIMIT,
    DATA_DIR,
)

logger = logging.getLogger("BLACKDARK.Blockscout")

_TIMEOUT = aiohttp.ClientTimeout(total=14)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

_USAGE_PATH = DATA_DIR / "blockscout_api_usage.json"
_CACHE: dict[str, tuple[float, Any]] = {}
_RPS_TIMES: deque[float] = deque(maxlen=BLOCKSCOUT_RPS_LIMIT * 2)

_EVM_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Public Blockscout instances (free REST v2).
_CHAIN_BASES: dict[str, str] = {
    "ethereum": "https://eth.blockscout.com",
    "polygon": "https://polygon.blockscout.com",
    "arbitrum": "https://arbitrum.blockscout.com",
    "optimism": "https://optimism.blockscout.com",
    "base": "https://base.blockscout.com",
    "bsc": "https://bsc.blockscout.com",
}


def supported_chains() -> tuple[str, ...]:
    return tuple(_CHAIN_BASES.keys())


def _utc_day() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _load_usage() -> dict[str, Any]:
    try:
        if _USAGE_PATH.exists():
            raw = json.loads(_USAGE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"day": _utc_day(), "count": 0}


def _save_usage(row: dict[str, Any]) -> None:
    try:
        _USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _USAGE_PATH.write_text(json.dumps(row), encoding="utf-8")
    except OSError:
        logger.debug("blockscout usage persist failed")


def usage_stats() -> dict[str, Any]:
    row = _load_usage()
    day = _utc_day()
    count = int(row.get("count") or 0) if row.get("day") == day else 0
    return {
        "configured": True,
        "no_api_key": True,
        "day_utc": day,
        "calls_today": count,
        "daily_limit": BLOCKSCOUT_DAILY_LIMIT,
        "rps_limit": BLOCKSCOUT_RPS_LIMIT,
        "remaining_today": max(0, BLOCKSCOUT_DAILY_LIMIT - count),
        "chains": list(_CHAIN_BASES.keys()),
    }


def _try_consume_quota() -> bool:
    now = time.time()
    while _RPS_TIMES and now - _RPS_TIMES[0] > 1.0:
        _RPS_TIMES.popleft()
    if len(_RPS_TIMES) >= BLOCKSCOUT_RPS_LIMIT:
        logger.debug("Blockscout RPS limit reached")
        return False
    row = _load_usage()
    day = _utc_day()
    if row.get("day") != day:
        row = {"day": day, "count": 0}
    count = int(row.get("count") or 0)
    if count >= BLOCKSCOUT_DAILY_LIMIT:
        logger.warning("Blockscout daily limit reached (%s)", BLOCKSCOUT_DAILY_LIMIT)
        return False
    row["count"] = count + 1
    row["day"] = day
    _save_usage(row)
    _RPS_TIMES.append(now)
    return True


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > BLOCKSCOUT_CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


def _norm_chain(chain: str) -> str:
    c = (chain or "ethereum").lower().strip()
    if c in {"eth", "mainnet"}:
        return "ethereum"
    if c == "bnb":
        return "bsc"
    return c


def _base_for_chain(chain: str) -> str | None:
    return _CHAIN_BASES.get(_norm_chain(chain))


def _valid_address(address: str) -> bool:
    return bool(_EVM_ADDR_RE.match((address or "").strip()))


async def _get_json(base: str, path: str) -> Any | None:
    if not _try_consume_quota():
        return None
    url = f"{base.rstrip('/')}{path}"
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=_HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.debug("Blockscout HTTP %s %s", resp.status, path)
                    return None
                return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def fetch_address_summary(address: str, *, chain: str = "ethereum") -> dict[str, Any] | None:
    if not _valid_address(address):
        return None
    base = _base_for_chain(chain)
    if not base:
        return None
    addr = address.lower()
    cache_key = f"addr:{_norm_chain(chain)}:{addr}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _get_json(base, f"/api/v2/addresses/{addr}")
    if not isinstance(data, dict):
        return None
    try:
        wei = int(data.get("coin_balance") or 0)
    except (TypeError, ValueError):
        wei = 0
    native = wei / 1e18
    row: dict[str, Any] = {
        "address": addr,
        "chain": _norm_chain(chain),
        "balance_wei": wei,
        "balance_native": round(native, 8),
        "ens_domain_name": data.get("ens_domain_name"),
        "source": "blockscout",
    }
    rate = data.get("exchange_rate")
    if rate is not None:
        try:
            row["native_usd_estimate"] = round(native * float(rate), 2)
            row["exchange_rate_usd"] = float(rate)
        except (TypeError, ValueError):
            pass
    _cache_set(cache_key, row)
    return row


async def fetch_address_transactions(
    address: str,
    *,
    chain: str = "ethereum",
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not _valid_address(address):
        return []
    base = _base_for_chain(chain)
    if not base:
        return []
    lim = max(1, min(int(limit), 20))
    addr = address.lower()
    cache_key = f"txs:{_norm_chain(chain)}:{addr}:{lim}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _get_json(base, f"/api/v2/addresses/{addr}/transactions")
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    rows: list[dict[str, Any]] = []
    for tx in items[:lim]:
        if not isinstance(tx, dict):
            continue
        from_obj = tx.get("from") if isinstance(tx.get("from"), dict) else {}
        to_obj = tx.get("to") if isinstance(tx.get("to"), dict) else {}
        rows.append(
            {
                "hash": tx.get("hash"),
                "from": from_obj.get("hash") if isinstance(from_obj, dict) else tx.get("from"),
                "to": to_obj.get("hash") if isinstance(to_obj, dict) else tx.get("to"),
                "value_wei": tx.get("value"),
                "block_number": tx.get("block_number"),
                "timestamp": tx.get("timestamp"),
                "result": tx.get("result"),
            }
        )
    _cache_set(cache_key, rows)
    return rows


async def fetch_transaction_by_hash(tx_hash: str, *, chain: str = "ethereum") -> dict[str, Any] | None:
    h = (tx_hash or "").strip().lower()
    if not h.startswith("0x") or len(h) != 66:
        return None
    base = _base_for_chain(chain)
    if not base:
        return None
    cache_key = f"tx:{_norm_chain(chain)}:{h}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _get_json(base, f"/api/v2/transactions/{h}")
    if not isinstance(data, dict):
        return None
    from_obj = data.get("from") if isinstance(data.get("from"), dict) else {}
    to_obj = data.get("to") if isinstance(data.get("to"), dict) else {}
    row = {
        "hash": h,
        "from": from_obj.get("hash") if isinstance(from_obj, dict) else None,
        "to": to_obj.get("hash") if isinstance(to_obj, dict) else None,
        "value_wei": data.get("value"),
        "block_number": data.get("block_number"),
        "result": data.get("result"),
        "source": "blockscout",
        "chain": _norm_chain(chain),
    }
    _cache_set(cache_key, row)
    return row


async def fetch_explorer_fallback(
    address: str,
    *,
    chain: str = "ethereum",
    include_transactions: bool = True,
    tx_limit: int = 5,
) -> dict[str, Any]:
    stats = usage_stats()
    if stats["remaining_today"] <= 0:
        return {"ok": False, "error": "daily_limit_exceeded", "usage": stats}
    ch = _norm_chain(chain)
    if ch not in _CHAIN_BASES:
        return {"ok": False, "error": "unsupported_chain", "chain": ch, "usage": stats}
    bal = await fetch_address_summary(address, chain=ch)
    txs: list[dict[str, Any]] = []
    if include_transactions:
        txs = await fetch_address_transactions(address, chain=ch, limit=tx_limit)
    row = {
        "ok": bool(bal or txs),
        "source": "blockscout",
        "attribution": f"Data: Blockscout ({ch})",
        "chain": ch,
        "balance": bal,
        "recent_transactions": txs,
        "usage": usage_stats(),
        "no_api_key": True,
    }
    if not row["ok"]:
        return row
    from thegraph_public_api import maybe_enrich_explorer_row

    return await maybe_enrich_explorer_row(row, address, chain=ch)
