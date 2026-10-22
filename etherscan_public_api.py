"""
Etherscan free-tier API (fallback on-chain address / transaction data).

Free plan: 5 requests/second, 100,000 requests/day (per Etherscan docs).
Requires ETHERSCAN_API_KEY — no subscription fee.
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
    DATA_DIR,
    ETHERSCAN_API_KEY,
    ETHERSCAN_CACHE_TTL_SEC,
    ETHERSCAN_DAILY_LIMIT,
    ETHERSCAN_RPS_LIMIT,
)

logger = logging.getLogger("BLACKDARK.Etherscan")

_BASE_URL = "https://api.etherscan.io/api"
_TIMEOUT = aiohttp.ClientTimeout(total=14)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

_USAGE_PATH = DATA_DIR / "etherscan_api_usage.json"
_CACHE: dict[str, tuple[float, Any]] = {}

_RPS_TIMES: deque[float] = deque(maxlen=ETHERSCAN_RPS_LIMIT * 2)

_EVM_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


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
        logger.debug("etherscan usage persist failed")


def usage_stats() -> dict[str, Any]:
    row = _load_usage()
    day = _utc_day()
    if row.get("day") != day:
        count = 0
    else:
        count = int(row.get("count") or 0)
    return {
        "configured": bool(ETHERSCAN_API_KEY),
        "day_utc": day,
        "calls_today": count,
        "daily_limit": ETHERSCAN_DAILY_LIMIT,
        "rps_limit": ETHERSCAN_RPS_LIMIT,
        "remaining_today": max(0, ETHERSCAN_DAILY_LIMIT - count),
    }


def _try_consume_quota() -> bool:
    if not ETHERSCAN_API_KEY:
        return False
    now = time.time()
    while _RPS_TIMES and now - _RPS_TIMES[0] > 1.0:
        _RPS_TIMES.popleft()
    if len(_RPS_TIMES) >= ETHERSCAN_RPS_LIMIT:
        logger.debug("Etherscan RPS limit reached")
        return False
    row = _load_usage()
    day = _utc_day()
    if row.get("day") != day:
        row = {"day": day, "count": 0}
    count = int(row.get("count") or 0)
    if count >= ETHERSCAN_DAILY_LIMIT:
        logger.warning("Etherscan daily limit reached (%s)", ETHERSCAN_DAILY_LIMIT)
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
    if time.time() - ts > ETHERSCAN_CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


def _valid_evm_address(address: str) -> bool:
    return bool(_EVM_ADDR_RE.match((address or "").strip()))


async def _api_get(params: dict[str, str]) -> dict[str, Any] | None:
    if not _try_consume_quota():
        return None
    q = {**params, "apikey": ETHERSCAN_API_KEY}
    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT, headers=_HEADERS) as session:
            async with session.get(_BASE_URL, params=q) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if not isinstance(data, dict):
                    return None
                msg = str(data.get("message") or "")
                if str(data.get("status")) == "0" and msg not in ("OK", "No transactions found"):
                    logger.debug("Etherscan API message: %s", msg)
                    return None
                return data
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def fetch_eth_balance_wei(address: str) -> dict[str, Any] | None:
    if not _valid_evm_address(address):
        return None
    cache_key = f"bal:{address.lower()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _api_get(
        {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
        }
    )
    if not data:
        return None
    try:
        wei = int(data.get("result") or 0)
    except (TypeError, ValueError):
        return None
    eth = wei / 1e18
    row = {
        "address": address.lower(),
        "balance_wei": wei,
        "balance_eth": round(eth, 8),
        "source": "etherscan_free",
    }
    _cache_set(cache_key, row)
    return row


async def fetch_normal_transactions(
    address: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not _valid_evm_address(address):
        return []
    lim = max(1, min(int(limit), 25))
    cache_key = f"txs:{address.lower()}:{lim}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _api_get(
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": "1",
            "offset": str(lim),
            "sort": "desc",
        }
    )
    if not data:
        return []
    result = data.get("result")
    if not isinstance(result, list):
        return []
    rows: list[dict[str, Any]] = []
    for tx in result[:lim]:
        if not isinstance(tx, dict):
            continue
        rows.append(
            {
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "value_wei": tx.get("value"),
                "block_number": tx.get("blockNumber"),
                "time_stamp": tx.get("timeStamp"),
                "is_error": tx.get("isError"),
            }
        )
    _cache_set(cache_key, rows)
    return rows


async def fetch_transaction_by_hash(tx_hash: str) -> dict[str, Any] | None:
    h = (tx_hash or "").strip().lower()
    if not h.startswith("0x") or len(h) != 66:
        return None
    cache_key = f"tx:{h}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = await _api_get(
        {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": h,
        }
    )
    if not data or not isinstance(data.get("result"), dict):
        receipt = await _api_get(
            {
                "module": "transaction",
                "action": "gettxreceiptstatus",
                "txhash": h,
            }
        )
        if receipt:
            row = {
                "hash": h,
                "status": receipt.get("result"),
                "source": "etherscan_free",
            }
            _cache_set(cache_key, row)
            return row
        return None
    tx = data["result"]
    row = {
        "hash": h,
        "from": tx.get("from"),
        "to": tx.get("to"),
        "value_wei": tx.get("value"),
        "block_number": tx.get("blockNumber"),
        "source": "etherscan_free",
    }
    _cache_set(cache_key, row)
    return row


async def fetch_address_onchain_fallback(
    address: str,
    *,
    include_transactions: bool = True,
    tx_limit: int = 5,
) -> dict[str, Any]:
    """Bundle used when primary wallet aggregators are unavailable."""
    stats = usage_stats()
    if not stats["configured"]:
        return {"ok": False, "error": "not_configured", "usage": stats}
    if stats["remaining_today"] <= 0:
        return {"ok": False, "error": "daily_limit_exceeded", "usage": stats}
    bal = await fetch_eth_balance_wei(address)
    txs: list[dict[str, Any]] = []
    if include_transactions and bal is not None:
        txs = await fetch_normal_transactions(address, limit=tx_limit)
    return {
        "ok": bool(bal or txs),
        "source": "etherscan_free",
        "attribution": "Data: Etherscan",
        "balance": bal,
        "recent_transactions": txs,
        "usage": usage_stats(),
    }
