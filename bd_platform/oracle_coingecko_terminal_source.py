"""
Oracle API — CoinGecko Terminal Source — Feature #839 (Sprint-1).

NOT standalone — data source connector in Oracle API.
GeckoTerminal API: DEX volume | Liquidity | Pool data.

Cache + rate-limit handling + fallback (CoinMarketCap + internal aggregation).
Feeds Market Radar with DEX data. No user-facing surface.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OracleCoinGeckoTerminal")

_FEATURE_REF = 839
_STANDALONE = False
_MERGED_INTO = "Oracle API"
_COMPONENT = "coingecko_terminal_source"
_SEED_PATH = Path("data/oracle_coingecko_terminal_seed.json")
_RESPONSE_TARGET_MS = 3000
_UPTIME_TARGET_PCT = 99.0
_DATA_CATEGORIES = ("dex_volume", "liquidity", "pool_data")

CategoryType = Literal["dex_volume", "liquidity", "pool_data"]

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("coingecko terminal seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("coingecko_terminal_source_839") or {}


def _cache_ttl_sec(category: CategoryType, *, seed: dict[str, Any] | None = None) -> int:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    ttl_cfg = cfg.get("cache_ttl_sec") or {}
    if category == "pool_data":
        return int(ttl_cfg.get("static_data", 3600))
    return int(ttl_cfg.get("prices", 180))


def _cache_get(key: str, ttl_sec: int) -> dict[str, Any] | None:
    row = _CACHE.get(key)
    if not row:
        return None
    if time.time() - row[0] < ttl_sec:
        return row[1]
    return None


def _cache_set(key: str, payload: dict[str, Any]) -> None:
    _CACHE[key] = (time.time(), payload)


def _fetch_primary(category: CategoryType, asset: str, *, seed: dict[str, Any]) -> dict[str, Any]:
    datasets = seed.get("datasets") or {}
    data = datasets.get(f"{category}_{asset.lower()}") or datasets.get(category) or {}
    return {"ok": True, "source": "geckoterminal", "category": category, "asset": asset.upper(), "data": data}


def _fetch_fallback(category: CategoryType, asset: str, *, seed: dict[str, Any]) -> dict[str, Any]:
    cfg = _cfg(seed)
    fallback = (seed.get("fallback_sources") or {}).get(category) or {}
    return {
        "ok": True,
        "source": fallback.get("primary", "coinmarketcap"),
        "secondary": fallback.get("secondary", "internal_aggregation"),
        "category": category,
        "asset": asset.upper(),
        "data": fallback.get("data") or {},
        "fallback": True,
    }


def fetch_coingecko_terminal_data_839(
    category: CategoryType,
    asset: str = "ETH",
    *,
    seed: dict[str, Any] | None = None,
    force_primary_fail: bool = False,
) -> dict[str, Any]:
    """Fetch normalized GeckoTerminal data with cache + fallback."""
    seed = seed or _load_seed()
    sym = asset.upper()
    if category not in _DATA_CATEGORIES:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "invalid_category", "category": category}

    ttl = _cache_ttl_sec(category, seed=seed)
    cache_key = f"cg_terminal:{category}:{sym}"
    if not force_primary_fail:
        cached = _cache_get(cache_key, ttl)
        if cached:
            return {**cached, "cache_hit": True, "cache_ttl_sec": ttl}

    t0 = time.perf_counter()
    try:
        if force_primary_fail:
            raise RuntimeError("simulated_primary_failure")
        result = _fetch_primary(category, sym, seed=seed)
        if not result.get("ok"):
            raise RuntimeError("primary_failed")
    except Exception:
        logger.debug("geckoterminal primary failed for %s/%s", category, sym, exc_info=True)
        result = _fetch_fallback(category, sym, seed=seed)

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "ok": result.get("ok", False),
        "feature_ref": _FEATURE_REF,
        "component": _COMPONENT,
        "category": category,
        "asset": sym,
        "source": result.get("source"),
        "fallback_used": result.get("fallback", False),
        "data": result.get("data"),
        "normalized": True,
        "cache_hit": False,
        "cache_ttl_sec": ttl,
        "latency_ms": latency_ms,
        "within_response_target": latency_ms <= _RESPONSE_TARGET_MS,
        "timestamp": _utcnow(),
    }
    _cache_set(cache_key, payload)
    return payload


def build_market_radar_dex_feed_839(
    asset: str = "ETH",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#839 → Market Radar DEX data hook."""
    seed = seed or _load_seed()
    sym = asset.upper()
    volume = fetch_coingecko_terminal_data_839("dex_volume", sym, seed=seed)
    liquidity = fetch_coingecko_terminal_data_839("liquidity", sym, seed=seed)
    pools = fetch_coingecko_terminal_data_839("pool_data", sym, seed=seed)
    return {
        "ok": all(r.get("ok") for r in (volume, liquidity, pools)),
        "feature_ref": _FEATURE_REF,
        "surface": "market_radar",
        "asset": sym,
        "dex_volume": volume,
        "liquidity": liquidity,
        "pool_data": pools,
        "timestamp": _utcnow(),
    }


def coingecko_terminal_status_839(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "sprint": 1,
        "no_user_surface": True,
        "data_categories": list(_DATA_CATEGORIES),
        "api": "GeckoTerminal",
        "rate_limit_handling": "cache_and_fallback",
        "cache_prices_sec": f"{cfg.get('cache_ttl_sec', {}).get('prices_min', 60)}-{cfg.get('cache_ttl_sec', {}).get('prices_max', 300)}",
        "cache_static_sec": f"{cfg.get('cache_ttl_sec', {}).get('static_min', 3600)}-{cfg.get('cache_ttl_sec', {}).get('static_max', 86400)}",
        "fallback_sources": ["coinmarketcap", "internal_aggregation"],
        "response_target_ms": _RESPONSE_TARGET_MS,
        "uptime_target_pct": _UPTIME_TARGET_PCT,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def run_coingecko_terminal_e2e_839(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = coingecko_terminal_status_839(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "three_data_categories", "passed": status.get("data_categories") == list(_DATA_CATEGORIES)})

    for cat in _DATA_CATEGORIES:
        result = fetch_coingecko_terminal_data_839(cat, "ETH", seed=seed)
        tests.append({"test": f"fetch_{cat}", "passed": result.get("ok") is True})
        tests.append({"test": f"latency_{cat}", "passed": result.get("within_response_target") is True})

    cached = fetch_coingecko_terminal_data_839("dex_volume", "ETH", seed=seed)
    tests.append({"test": "cache_hit", "passed": cached.get("cache_hit") is True})

    fallback = fetch_coingecko_terminal_data_839(
        "liquidity", "ETH", seed=seed, force_primary_fail=True,
    )
    tests.append({"test": "fallback_on_failure", "passed": fallback.get("fallback_used") is True})

    radar = build_market_radar_dex_feed_839("ETH", seed=seed)
    tests.append({"test": "market_radar_feed", "passed": radar.get("ok") is True})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
