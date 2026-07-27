"""
BLACKDARK — Redis top-of-book + OHLC cache for sub-ms cross-venue comparison.

Supports standalone Redis or Redis Cluster (REDIS_CLUSTER_NODES).
Strict mode (PRICE_FEED_WS_ONLY): Redis connection required — no silent local fallback.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.RedisPriceCache")

_client: Any = None
_cluster_mode = False
_local_mirror: dict[str, dict[str, dict[str, Any]]] = {}
_local_ohlc: dict[str, list[float]] = {}
_ttl_sec = int(getattr(config, "REDIS_PRICE_TTL_SEC", 5))
_connected = False


def _cluster_nodes() -> list[str]:
    raw = getattr(config, "REDIS_CLUSTER_NODES", "") or ""
    return [n.strip() for n in raw.split(",") if n.strip()]


def enabled() -> bool:
    return getattr(config, "REDIS_PRICE_CACHE_ENABLED", True) and (
        bool(config.REDIS_URL) or bool(_cluster_nodes())
    )


def strict_mode() -> bool:
    return getattr(config, "PRICE_FEED_WS_ONLY", True) and getattr(config, "REDIS_REQUIRED", True)


async def ensure_redis_ready(*, retries: int = 8, delay_sec: float = 1.5) -> bool:
    """Connect to Redis/Cluster with retries — required in strict WS-only mode."""
    global _connected
    for attempt in range(1, retries + 1):
        client = await _redis(force=True)
        if client is not None:
            _connected = True
            return True
        if attempt < retries:
            logger.warning("Redis not ready (attempt %d/%d) — retry in %.1fs", attempt, retries, delay_sec)
            import asyncio

            await asyncio.sleep(delay_sec)
    if strict_mode():
        raise RuntimeError(
            "Redis required for WS-only price feed. Start: docker compose up -d redis "
            "and set REDIS_URL=redis://localhost:6379/0"
        )
    return False


async def _redis(*, force: bool = False) -> Any | None:
    global _client, _cluster_mode, _connected
    if not enabled():
        return None
    if _client is not None and not force:
        return _client
    nodes = _cluster_nodes()
    try:
        if nodes:
            from redis.asyncio.cluster import RedisCluster

            startup_nodes = [{"host": n.split(":")[0], "port": int(n.split(":")[1])} for n in nodes]
            _client = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)
            _cluster_mode = True
        else:
            import redis.asyncio as redis

            _client = redis.from_url(
                config.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            _cluster_mode = False
        await _client.ping()
        _connected = True
        logger.info("Redis price cache connected | cluster=%s", _cluster_mode)
        return _client
    except Exception as exc:
        logger.warning("Redis price cache unavailable: %s", exc)
        _client = None
        _connected = False
        return None


async def set_top_of_book(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    ask: float,
    bid_qty: float = 0.0,
    ask_qty: float = 0.0,
) -> bool:
    ex = exchange.strip().lower()
    sym = symbol.strip().upper()
    payload = {
        "bid": bid,
        "ask": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,
        "mid": (bid + ask) / 2.0,
        "ts_ms": int(time.time() * 1000),
    }

    client = await _redis()
    if client is None:
        if strict_mode():
            return False
        _local_mirror.setdefault(ex, {})[sym] = payload
        return False

    try:
        key = f"bd:book:{ex}"
        await client.hset(key, sym, json.dumps(payload, separators=(",", ":")))
        await client.expire(key, _ttl_sec)
        return True
    except Exception:
        logger.debug("Redis HSET failed", exc_info=True)
        if not strict_mode():
            _local_mirror.setdefault(ex, {})[sym] = payload
        return False


async def get_best_price(exchange: str, symbol: str) -> dict[str, float] | None:
    ex = exchange.strip().lower()
    sym = symbol.strip().upper()

    client = await _redis()
    if client is not None:
        try:
            raw = await client.hget(f"bd:book:{ex}", sym)
            if raw:
                row = json.loads(raw)
                return {"bid": float(row["bid"]), "ask": float(row["ask"]), "mid": float(row["mid"])}
        except Exception:
            pass

    if not strict_mode():
        local = (_local_mirror.get(ex) or {}).get(sym)
        if local:
            return {"bid": local["bid"], "ask": local["ask"], "mid": local["mid"]}
    return None


async def get_all_books() -> dict[str, dict[str, dict[str, Any]]]:
    client = await _redis()
    if client is None:
        return dict(_local_mirror) if not strict_mode() else {}

    out: dict[str, dict[str, dict[str, Any]]] = {}
    try:
        async for key in client.scan_iter("bd:book:*", count=50):
            ex = str(key).replace("bd:book:", "", 1)
            rows = await client.hgetall(key)
            out[ex] = {sym: json.loads(raw) for sym, raw in rows.items()}
    except Exception:
        logger.debug("Redis scan books failed", exc_info=True)
    return out


def _bucket_ms(interval: str) -> int:
    mapping = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}
    return mapping.get(interval, 3_600_000)


async def record_ohlc_tick(symbol: str, *, mid: float, ts_ms: int, interval: str = "1h") -> None:
    sym = symbol.strip().upper()
    bucket = (ts_ms // _bucket_ms(interval)) * _bucket_ms(interval)
    key = f"bd:ohlc:{interval}:{sym}"

    client = await _redis()
    if client is None:
        if not strict_mode():
            closes = _local_ohlc.setdefault(key, [])
            closes.append(mid)
            if len(closes) > 500:
                _local_ohlc[key] = closes[-500:]
        return

    try:
        raw = await client.hget(key, str(bucket))
        if raw:
            candle = json.loads(raw)
            candle["h"] = max(float(candle["h"]), mid)
            candle["l"] = min(float(candle["l"]), mid)
            candle["c"] = mid
        else:
            candle = {"o": mid, "h": mid, "l": mid, "c": mid, "t": bucket}
        await client.hset(key, str(bucket), json.dumps(candle, separators=(",", ":")))
        await client.expire(key, 86_400)
    except Exception:
        logger.debug("Redis OHLC write failed", exc_info=True)


async def get_ohlc_closes(symbol: str, *, interval: str = "1h", limit: int = 200) -> list[float]:
    sym = symbol.strip().upper()
    key = f"bd:ohlc:{interval}:{sym}"

    client = await _redis()
    if client is not None:
        try:
            rows = await client.hgetall(key)
            if rows:
                buckets = sorted(int(k) for k in rows.keys())
                closes = [float(json.loads(rows[str(b)])["c"]) for b in buckets[-limit:]]
                if closes:
                    return closes
        except Exception:
            logger.debug("Redis OHLC read failed", exc_info=True)

    if not strict_mode():
        return _local_ohlc.get(key, [])[-limit:]
    return []


def cache_stats() -> dict[str, Any]:
    return {
        "enabled": enabled(),
        "connected": _connected,
        "cluster_mode": _cluster_mode,
        "redis_configured": bool(config.REDIS_URL),
        "cluster_nodes": _cluster_nodes(),
        "strict_mode": strict_mode(),
        "local_symbols": sum(len(v) for v in _local_mirror.values()),
        "exchanges": sorted(_local_mirror.keys()),
        "ttl_sec": _ttl_sec,
    }
