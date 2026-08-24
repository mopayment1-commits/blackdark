"""
1inch Network API connector — Intelligence Ledger data source (Sprint 2).

NOT a standalone product surface. Feeds execution intelligence with:
- Live 1inch.dev quote when ONEINCH_API_KEY is set
- DexScreener 1inch pool fallback (always available)
- TTL cache (default 1h, max 24h) + rate-limit backoff
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from path_safety import assert_url_path_safe

logger = logging.getLogger("BLACKDARK.OneInch")

_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_DEFAULT_TTL = int(os.getenv("ONEINCH_CACHE_TTL_SEC", "3600"))
_MAX_TTL = 86400
_RATE_LIMIT_UNTIL = 0.0

CHAIN_IDS = {
    "ethereum": 1,
    "polygon": 137,
    "arbitrum": 42161,
    "bsc": 56,
    "optimism": 10,
    "base": 8453,
}

# Mainnet token addresses (ethereum default)
TOKENS: dict[str, str] = {
    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D856Cc7",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cache_ttl() -> int:
    raw = int(os.getenv("ONEINCH_CACHE_TTL_SEC", str(_DEFAULT_TTL)))
    return max(60, min(_MAX_TTL, raw))


def _api_key() -> str | None:
    key = (os.getenv("ONEINCH_API_KEY") or "").strip()
    return key or None


def _token_address(symbol: str) -> str | None:
    return TOKENS.get(symbol.upper().replace("WETH", "ETH"))


async def _dexscreener_oneinch_quote(
    session: aiohttp.ClientSession, asset: str, *, amount_usd: float
) -> dict[str, Any] | None:
    from bd_platform.cex_dex_arbitrage import _oneinch_spot

    try:
        row = await _oneinch_spot(session, asset.upper(), cex_ref=0)
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        return None
    if not row:
        return None
    price = float(row.get("price") or 0)
    if price <= 0:
        return None
    est_out = amount_usd / price if price else 0
    return {
        "source": "dexscreener_1inch_fallback",
        "venue": "1inch",
        "price_usd": price,
        "liquidity_usd": float(row.get("liquidity_usd") or 0),
        "estimated_amount_out": est_out,
        "url": row.get("url"),
        "fallback": True,
    }


async def _oneinch_api_quote(
    *,
    chain: str,
    src_token: str,
    dst_token: str,
    amount_atomic: int,
    slippage_bps: int,
) -> dict[str, Any] | None:
    global _RATE_LIMIT_UNTIL
    if time.time() < _RATE_LIMIT_UNTIL:
        return None
    key = _api_key()
    if not key:
        return None
    chain_id = CHAIN_IDS.get(chain.lower(), 1)
    url = assert_url_path_safe(f"https://api.1inch.dev/swap/v6.0/{chain_id}/quote")
    headers = {**_HEADERS, "Authorization": f"Bearer {key}"}
    params = {
        "src": src_token,
        "dst": dst_token,
        "amount": str(amount_atomic),
        "includeTokensInfo": "true",
        "includeProtocols": "true",
    }
    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 429:
                    _RATE_LIMIT_UNTIL = time.time() + 60
                    return None
                if resp.status != 200:
                    return None
                data = await resp.json()
                dst_amount = int(data.get("dstAmount") or 0)
                return {
                    "source": "1inch_api",
                    "venue": "1inch",
                    "quote": data,
                    "dst_amount_atomic": dst_amount,
                    "protocols": data.get("protocols"),
                    "fallback": False,
                    "slippage_bps_requested": slippage_bps,
                }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        logger.debug("1inch API request failed")
        return None


async def fetch_oneinch_quote(
    *,
    asset: str = "ETH",
    quote_asset: str = "USDC",
    amount_usd: float = 10_000.0,
    chain: str = "ethereum",
    slippage_bps: int = 50,
    price_usd: float | None = None,
) -> dict[str, Any]:
    """
    Normalized 1inch quote for Intelligence Ledger (not a standalone feature).
    """
    t0 = time.perf_counter()
    asset_u = asset.upper()
    cache_key = f"{chain}:{asset_u}:{quote_asset}:{int(amount_usd)}:{slippage_bps}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _cache_ttl():
        out = dict(cached[1])
        out["cache_hit"] = True
        return out

    try:
        return await _fetch_oneinch_quote_inner(
            asset_u=asset_u,
            quote_asset=quote_asset,
            amount_usd=amount_usd,
            chain=chain,
            slippage_bps=slippage_bps,
            price_usd=price_usd,
            cache_key=cache_key,
            t0=t0,
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError) as exc:
        logger.debug("1inch quote failed: %s", exc)
        return {
            "ok": False,
            "data_state": "MISSING",
            "error": "oneinch_fetch_failed",
            "asset": asset_u,
            "chain": chain,
            "timestamp": _utcnow(),
        }


async def _fetch_oneinch_quote_inner(
    *,
    asset_u: str,
    quote_asset: str,
    amount_usd: float,
    chain: str,
    slippage_bps: int,
    price_usd: float | None,
    cache_key: str,
    t0: float,
) -> dict[str, Any]:
    src = _token_address(asset_u)
    dst = _token_address(quote_asset.upper())
    if not src or not dst:
        return {
            "ok": False,
            "data_state": "MISSING",
            "error": "unsupported_token_pair",
            "asset": asset_u,
            "timestamp": _utcnow(),
        }

    px = price_usd
    timeout = aiohttp.ClientTimeout(total=3)
    if not px or px <= 0:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            fb = await _dexscreener_oneinch_quote(session, asset_u, amount_usd=amount_usd)
            px = float((fb or {}).get("price_usd") or 0)
    if px <= 0:
        px = 3000.0 if asset_u == "ETH" else 1.0

    # USDC/USDT 6 decimals; ETH 18 decimals
    if asset_u in {"USDC", "USDT"}:
        amount_atomic = int(amount_usd * 1_000_000)
    else:
        amount_atomic = int((amount_usd / px) * 10**18)

    api_quote = await _oneinch_api_quote(
        chain=chain,
        src_token=src,
        dst_token=dst,
        amount_atomic=max(amount_atomic, 1),
        slippage_bps=slippage_bps,
    )

    fallback_quote = None
    if not api_quote:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            fallback_quote = await _dexscreener_oneinch_quote(session, asset_u, amount_usd=amount_usd)

    quote = api_quote or fallback_quote
    if not quote:
        return {
            "ok": False,
            "data_state": "MISSING",
            "error": "oneinch_and_fallback_unavailable",
            "asset": asset_u,
            "chain": chain,
            "timestamp": _utcnow(),
        }

    result = {
        "ok": True,
        "success": True,
        "data_state": "LIVE",
        "asset": asset_u,
        "quote_asset": quote_asset.upper(),
        "chain": chain,
        "amount_usd": amount_usd,
        "price_usd": px,
        "quote": quote,
        "api_key_configured": bool(_api_key()),
        "cache_ttl_seconds": _cache_ttl(),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "timestamp": _utcnow(),
        "intelligence_ledger_role": "execution_data_source",
    }
    _CACHE[cache_key] = (time.time(), result)
    return result
