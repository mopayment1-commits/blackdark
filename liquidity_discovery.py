"""
BLACKDARK — Dynamic Liquidity Discovery & Operational Manifest Builder.

Discovers CCXT markets and CoinGecko trust/volume baselines, merges them with
immutable whitelist guards, and writes a human-review manifest before ingestion.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.LiquidityDiscovery")

COINGECKO_EXCHANGES_URL = "https://api.coingecko.com/api/v3/exchanges"
COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

CMC_TO_CCXT: dict[str, str] = {
    "binance": "binance",
    "okx": "okx",
    "bybit": "bybit",
    "coinbase-exchange": "coinbase",
    "kraken": "kraken",
    "kucoin": "kucoin",
    "gate-io": "gateio",
    "crypto-com-exchange": "cryptocom",
    "bitfinex": "bitfinex",
    "bitstamp": "bitstamp",
    "htx": "huobi",
    "mexc": "mexc",
    "bitget": "bitget",
}

COINGECKO_TO_CCXT: dict[str, str] = {
    "binance": "binance",
    "okx": "okx",
    "bybit": "bybit",
    "bybit_spot": "bybit",
    "coinbase-exchange": "coinbase",
    "kraken": "kraken",
    "kucoin": "kucoin",
    "gate": "gateio",
    "gate-io": "gateio",
    "crypto-com-exchange": "cryptocom",
    "bitfinex": "bitfinex",
    "bitstamp": "bitstamp",
    "htx": "huobi",
    "huobi": "huobi",
    "mexc": "mexc",
    "bitget": "bitget",
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_exchange_id(exchange_id: str) -> str:
    return exchange_id.strip().lower().replace(" ", "_")


def _normalize_asset(asset: str) -> str:
    return asset.strip().upper()


def apply_whitelist_guards(
    exchanges: list[str],
    assets: list[str],
) -> tuple[list[str], list[str]]:
    """
    Ensure whitelist baseline entries are always present and cannot be removed.
    """
    exchange_set = {_normalize_exchange_id(item) for item in exchanges}
    asset_set = {_normalize_asset(item) for item in assets}

    for required in config.WHITELIST_EXCHANGES:
        exchange_set.add(_normalize_exchange_id(required))
    for required in config.WHITELIST_ASSETS:
        asset_set.add(_normalize_asset(required))

    return sorted(exchange_set), sorted(asset_set)


def symbols_for_assets(assets: list[str]) -> list[str]:
    symbols: set[str] = set()
    for quote in config.LIQUIDITY_QUOTE_CURRENCIES:
        for asset in assets:
            if asset in config.LIQUIDITY_QUOTE_CURRENCIES:
                continue
            symbols.add(f"{asset}/{quote}")
    return sorted(symbols)


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    async with session.get(url, params=params, headers=headers) as response:
        response.raise_for_status()
        return await response.json()


async def fetch_coingecko_trusted_exchanges(
    session: aiohttp.ClientSession,
) -> list[dict[str, Any]]:
    try:
        payload = await _fetch_json(
            session,
            COINGECKO_EXCHANGES_URL,
            params={"per_page": 250, "page": 1},
        )
        trusted: list[dict[str, Any]] = []
        for row in payload:
            trust_score = row.get("trust_score")
            if trust_score is None:
                continue
            if int(trust_score) < config.LIQUIDITY_MIN_TRUST_SCORE:
                continue
            coingecko_id = str(row.get("id") or "")
            ccxt_id = COINGECKO_TO_CCXT.get(coingecko_id)
            if not ccxt_id:
                continue
            trusted.append(
                {
                    "coingecko_id": coingecko_id,
                    "ccxt_id": ccxt_id,
                    "name": row.get("name"),
                    "trust_score": int(trust_score),
                    "trade_volume_24h_btc": float(row.get("trade_volume_24h_btc") or 0.0),
                }
            )
        trusted.sort(key=lambda item: item["trade_volume_24h_btc"], reverse=True)
        return trusted[: config.LIQUIDITY_MAX_DYNAMIC_EXCHANGES]
    except Exception:
        logger.exception("CoinGecko exchange discovery failed safely.")
        return []


async def fetch_coingecko_liquid_assets(
    session: aiohttp.ClientSession,
) -> list[dict[str, Any]]:
    try:
        payload = await _fetch_json(
            session,
            COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd",
                "order": "volume_desc",
                "per_page": 250,
                "page": 1,
                "sparkline": "false",
            },
        )
        assets: list[dict[str, Any]] = []
        for row in payload:
            symbol = _normalize_asset(str(row.get("symbol") or ""))
            volume_usd = float(row.get("total_volume") or 0.0)
            if not symbol or volume_usd < config.LIQUIDITY_MIN_24H_VOLUME_USD:
                continue
            assets.append(
                {
                    "asset": symbol,
                    "name": row.get("name"),
                    "volume_24h_usd": round(volume_usd, 2),
                    "market_cap_usd": float(row.get("market_cap") or 0.0),
                    "source": "coingecko",
                }
            )
        return assets[: config.LIQUIDITY_MAX_DYNAMIC_ASSETS]
    except Exception:
        logger.exception("CoinGecko asset discovery failed safely.")
        return []


async def fetch_coinmarketcap_liquid_assets(
    session: aiohttp.ClientSession,
) -> list[dict[str, Any]]:
    if not config.COINMARKETCAP_ENABLED:
        return []
    try:
        headers = {"X-CMC_PRO_API_KEY": config.COINMARKETCAP_API_KEY}
        payload = await _fetch_json(
            session,
            config.COINMARKETCAP_LISTINGS_URL,
            params={"limit": 200, "sort": "volume_24h", "sort_dir": "desc"},
            headers=headers,
        )
        assets: list[dict[str, Any]] = []
        for row in payload.get("data") or []:
            symbol = _normalize_asset(str(row.get("symbol") or ""))
            quote = row.get("quote") or {}
            usd = quote.get("USD") or {}
            volume_usd = float(usd.get("volume_24h") or 0.0)
            if not symbol or volume_usd < config.LIQUIDITY_MIN_24H_VOLUME_USD:
                continue
            assets.append(
                {
                    "asset": symbol,
                    "name": row.get("name"),
                    "volume_24h_usd": round(volume_usd, 2),
                    "market_cap_usd": float(usd.get("market_cap") or 0.0),
                    "source": "coinmarketcap",
                }
            )
        return assets[: config.LIQUIDITY_MAX_DYNAMIC_ASSETS]
    except Exception:
        logger.exception("CoinMarketCap asset discovery failed safely.")
        return []


async def fetch_coinmarketcap_trusted_exchanges(
    session: aiohttp.ClientSession,
) -> list[dict[str, Any]]:
    if not config.COINMARKETCAP_ENABLED:
        return []
    try:
        headers = {"X-CMC_PRO_API_KEY": config.COINMARKETCAP_API_KEY}
        async with session.get(
            config.COINMARKETCAP_EXCHANGES_URL,
            params={"limit": 200, "sort": "volume_24h", "sort_dir": "desc"},
            headers=headers,
        ) as response:
            response.raise_for_status()
            payload = await response.json()

        trusted: list[dict[str, Any]] = []
        for row in payload.get("data") or []:
            slug = str(row.get("slug") or "")
            ccxt_id = CMC_TO_CCXT.get(slug)
            if not ccxt_id:
                continue
            quote = row.get("quote") or {}
            usd = quote.get("USD") or {}
            volume_usd = float(usd.get("volume_24h") or 0.0)
            if volume_usd < config.LIQUIDITY_MIN_24H_VOLUME_USD:
                continue
            trusted.append(
                {
                    "coinmarketcap_slug": slug,
                    "ccxt_id": ccxt_id,
                    "name": row.get("name"),
                    "volume_24h_usd": round(volume_usd, 2),
                    "source": "coinmarketcap",
                }
            )
        trusted.sort(key=lambda item: item["volume_24h_usd"], reverse=True)
        return trusted[: config.LIQUIDITY_MAX_DYNAMIC_EXCHANGES]
    except Exception:
        logger.exception("CoinMarketCap exchange discovery failed safely.")
        return []


def merge_asset_candidates(
    *candidate_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in candidate_groups:
        for row in group:
            asset = _normalize_asset(str(row.get("asset") or ""))
            if not asset:
                continue
            existing = merged.get(asset)
            if existing is None or float(row.get("volume_24h_usd") or 0.0) > float(
                existing.get("volume_24h_usd") or 0.0
            ):
                merged[asset] = row
    ranked = sorted(
        merged.values(),
        key=lambda item: float(item.get("volume_24h_usd") or 0.0),
        reverse=True,
    )
    return ranked[: config.LIQUIDITY_MAX_DYNAMIC_ASSETS]


def merge_exchange_candidates(
    coingecko_rows: list[dict[str, Any]],
    cmc_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in coingecko_rows:
        ccxt_id = _normalize_exchange_id(str(row.get("ccxt_id") or ""))
        if ccxt_id:
            merged[ccxt_id] = {**row, "verification": ["coingecko"]}
    for row in cmc_rows:
        ccxt_id = _normalize_exchange_id(str(row.get("ccxt_id") or ""))
        if not ccxt_id:
            continue
        if ccxt_id in merged:
            verification = list(merged[ccxt_id].get("verification") or [])
            if "coinmarketcap" not in verification:
                verification.append("coinmarketcap")
            merged[ccxt_id]["verification"] = verification
        else:
            merged[ccxt_id] = {**row, "verification": ["coinmarketcap"]}
    ranked = sorted(
        merged.values(),
        key=lambda item: float(
            item.get("trade_volume_24h_btc")
            or item.get("volume_24h_usd")
            or 0.0
        ),
        reverse=True,
    )
    return ranked[: config.LIQUIDITY_MAX_DYNAMIC_EXCHANGES]


async def _discover_ccxt_exchange_pairs(
    exchange_id: str,
    candidate_set: set[str],
    quote_set: set[str],
) -> list[dict[str, Any]]:
    try:
        import ccxt.async_support as ccxt_async
    except ImportError:
        return []

    if exchange_id not in ccxt_async.exchanges:
        return []

    exchange = None
    discovered: list[dict[str, Any]] = []
    try:
        exchange_class = getattr(ccxt_async, exchange_id)
        exchange = exchange_class({"enableRateLimit": True, "timeout": 15000})

        async def _load_and_scan() -> list[dict[str, Any]]:
            assert exchange is not None
            await exchange.load_markets()
            rows: list[dict[str, Any]] = []
            for symbol, market in exchange.markets.items():
                if not market.get("active", True):
                    continue
                if str(market.get("type") or "spot") != "spot":
                    continue
                base = _normalize_asset(str(market.get("base") or ""))
                quote = _normalize_asset(str(market.get("quote") or ""))
                if quote not in quote_set:
                    continue
                if base not in candidate_set and base not in config.WHITELIST_ASSETS:
                    continue
                rows.append(
                    {
                        "exchange": exchange_id,
                        "symbol": symbol.replace(":", "/") if ":" in symbol else symbol,
                        "base": base,
                        "quote": quote,
                        "source": "ccxt",
                    }
                )
            return rows

        discovered = await asyncio.wait_for(
            _load_and_scan(),
            timeout=config.LIQUIDITY_DISCOVERY_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.warning("CCXT market discovery failed safely | exchange=%s", exchange_id)
    finally:
        if exchange is not None:
            try:
                await exchange.close()
            except Exception:
                logger.exception("Failed closing CCXT exchange | exchange=%s", exchange_id)

    return discovered


async def discover_ccxt_market_pairs(
    exchange_ids: list[str],
    candidate_assets: list[str],
) -> list[dict[str, Any]]:
    """
    Probe CCXT exchange registries for active USDT/USDC spot pairs.
    """
    try:
        import ccxt.async_support as ccxt_async  # noqa: F401
    except ImportError as exc:
        logger.warning("CCXT not installed; skipping dynamic market discovery.")
        raise RuntimeError(
            "CCXT is required for dynamic liquidity discovery. Install with: pip install ccxt"
        ) from exc

    candidate_set = {_normalize_asset(asset) for asset in candidate_assets}
    quote_set = set(config.LIQUIDITY_QUOTE_CURRENCIES)
    semaphore = asyncio.Semaphore(5)

    async def _guarded_probe(exchange_id: str) -> list[dict[str, Any]]:
        async with semaphore:
            return await _discover_ccxt_exchange_pairs(
                exchange_id,
                candidate_set,
                quote_set,
            )

    probe_results = await asyncio.gather(
        *(_guarded_probe(exchange_id) for exchange_id in exchange_ids),
        return_exceptions=True,
    )

    discovered: list[dict[str, Any]] = []
    for exchange_id, result in zip(exchange_ids, probe_results):
        if isinstance(result, Exception):
            logger.warning(
                "CCXT market discovery failed safely | exchange=%s error=%s",
                exchange_id,
                result,
            )
            continue
        discovered.extend(result)

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for row in discovered:
        unique[(row["exchange"], row["symbol"])] = row
    return sorted(unique.values(), key=lambda item: (item["exchange"], item["symbol"]))


async def build_operational_inventory() -> dict[str, Any]:
    """
    Combine immutable whitelist baseline with dynamically filtered candidates.
    """
    whitelist_exchanges = sorted(config.WHITELIST_EXCHANGES)
    whitelist_assets = sorted(config.WHITELIST_ASSETS)

    dynamic_exchange_rows: list[dict[str, Any]] = []
    dynamic_asset_rows: list[dict[str, Any]] = []
    ccxt_pairs: list[dict[str, Any]] = []

    timeout = aiohttp.ClientTimeout(total=config.LIQUIDITY_DISCOVERY_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        coingecko_exchange_rows = await fetch_coingecko_trusted_exchanges(session)
        coingecko_asset_rows = await fetch_coingecko_liquid_assets(session)
        cmc_exchange_rows = await fetch_coinmarketcap_trusted_exchanges(session)
        cmc_asset_rows = await fetch_coinmarketcap_liquid_assets(session)

    dynamic_exchange_rows = merge_exchange_candidates(
        coingecko_exchange_rows,
        cmc_exchange_rows,
    )
    dynamic_asset_rows = merge_asset_candidates(
        coingecko_asset_rows,
        cmc_asset_rows,
    )

    dynamic_exchange_ids = [
        _normalize_exchange_id(row["ccxt_id"]) for row in dynamic_exchange_rows
    ]
    dynamic_assets = [_normalize_asset(row["asset"]) for row in dynamic_asset_rows]

    operational_exchanges, operational_assets = apply_whitelist_guards(
        dynamic_exchange_ids,
        dynamic_assets,
    )

    try:
        ccxt_pairs = await discover_ccxt_market_pairs(
            operational_exchanges,
            operational_assets,
        )
    except Exception:
        logger.exception("CCXT pair discovery skipped due to error; whitelist baseline retained.")
        ccxt_pairs = []

    operational_symbols = symbols_for_assets(operational_assets)
    for pair in ccxt_pairs:
        symbol = str(pair.get("symbol") or "")
        if symbol and symbol not in operational_symbols:
            operational_symbols.append(symbol)
    operational_symbols = sorted(set(operational_symbols))

    manifest = {
        "generated_at": _utcnow_iso(),
        "status": "pending_review",
        "guards": {
            "whitelist_exchanges_locked": True,
            "whitelist_assets_locked": True,
            "whitelist_exchanges": whitelist_exchanges,
            "whitelist_assets": whitelist_assets,
        },
        "filters": {
            "min_trust_score": config.LIQUIDITY_MIN_TRUST_SCORE,
            "min_24h_volume_usd": config.LIQUIDITY_MIN_24H_VOLUME_USD,
            "quote_currencies": list(config.LIQUIDITY_QUOTE_CURRENCIES),
            "max_dynamic_exchanges": config.LIQUIDITY_MAX_DYNAMIC_EXCHANGES,
            "max_dynamic_assets": config.LIQUIDITY_MAX_DYNAMIC_ASSETS,
            "coinmarketcap_enabled": config.COINMARKETCAP_ENABLED,
        },
        "dynamic_candidates": {
            "exchanges": dynamic_exchange_rows,
            "assets": dynamic_asset_rows,
            "coingecko_exchanges": coingecko_exchange_rows,
            "coingecko_assets": coingecko_asset_rows,
            "coinmarketcap_exchanges": cmc_exchange_rows,
            "coinmarketcap_assets": cmc_asset_rows,
            "ccxt_pairs_sample_count": len(ccxt_pairs),
        },
        "operational": {
            "exchanges": operational_exchanges,
            "assets": operational_assets,
            "symbols": operational_symbols,
            "ingestion_ready_exchanges": sorted(
                set(operational_exchanges) & set(config.INGESTION_READY_EXCHANGES)
            ),
        },
        "review": {
            "approved": False,
            "approved_at": None,
            "instruction": (
                "Review this manifest before enabling live ingestion. "
                "Whitelist entries cannot be removed by filtering errors."
            ),
        },
    }
    return manifest


def save_operational_manifest(manifest: dict[str, Any]) -> str:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = config.OPERATIONAL_MANIFEST_PATH
    path.write_text(json.dumps(manifest, indent=2, sort_keys=False), encoding="utf-8")
    return str(path)


def load_operational_manifest() -> dict[str, Any] | None:
    path = config.OPERATIONAL_MANIFEST_PATH
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to load operational manifest from %s", path)
        return None


def print_manifest_summary(manifest: dict[str, Any], *, manifest_path: str) -> None:
    operational = manifest.get("operational") or {}
    guards = manifest.get("guards") or {}
    dynamic = manifest.get("dynamic_candidates") or {}

    lines = [
        "",
        "=" * 72,
        "BLACKDARK OPERATIONAL MANIFEST SUMMARY",
        "=" * 72,
        f"Generated At          : {manifest.get('generated_at')}",
        f"Manifest Path         : {manifest_path}",
        f"Review Status         : {manifest.get('status')}",
        "",
        "WHITELIST GUARDS (IMMUTABLE)",
        f"  Exchanges           : {', '.join(guards.get('whitelist_exchanges') or [])}",
        f"  Assets              : {', '.join(guards.get('whitelist_assets') or [])}",
        "",
        "OPERATIONAL INVENTORY",
        f"  Exchanges           : {len(operational.get('exchanges') or [])}",
        f"  Assets              : {len(operational.get('assets') or [])}",
        f"  Symbols             : {len(operational.get('symbols') or [])}",
        f"  Ingestion-Ready Exchanges: {', '.join(operational.get('ingestion_ready_exchanges') or [])}",
        "",
        "DYNAMIC DISCOVERY",
        f"  Trusted Exchanges   : {len(dynamic.get('exchanges') or [])}",
        f"  Liquid Assets       : {len(dynamic.get('assets') or [])}",
        f"  CoinGecko Exchanges : {len(dynamic.get('coingecko_exchanges') or [])}",
        f"  CoinGecko Assets    : {len(dynamic.get('coingecko_assets') or [])}",
        f"  CMC Exchanges       : {len(dynamic.get('coinmarketcap_exchanges') or [])}",
        f"  CMC Assets          : {len(dynamic.get('coinmarketcap_assets') or [])}",
        f"  CCXT Pair Probes    : {dynamic.get('ccxt_pairs_sample_count', 0)}",
        "",
        "NEXT STEP",
        "  Review data/operational_manifest.json",
        "  Press ENTER to approve manifest and start ingestion",
        "  Or set MANIFEST_AUTO_APPROVE=true for non-interactive environments",
        "=" * 72,
        "",
    ]
    print("\n".join(lines))


async def initialize_operational_manifest() -> dict[str, Any]:
    """
    Build, persist, and summarize the operational manifest.

    Does not start ingestion loops.
    """
    manifest = await build_operational_inventory()
    manifest_path = save_operational_manifest(manifest)
    print_manifest_summary(manifest, manifest_path=manifest_path)
    logger.info("Operational manifest saved | path=%s", manifest_path)
    return manifest


async def wait_for_manifest_review(manifest: dict[str, Any]) -> dict[str, Any]:
    """
    Pause until a human approves the manifest or auto-approve is enabled.
    """
    if config.MANIFEST_AUTO_APPROVE:
        manifest["status"] = "approved"
        manifest["review"] = {
            **(manifest.get("review") or {}),
            "approved": True,
            "approved_at": _utcnow_iso(),
            "approval_mode": "auto",
        }
        save_operational_manifest(manifest)
        logger.info("Operational manifest auto-approved via MANIFEST_AUTO_APPROVE.")
        return manifest

    loop = asyncio.get_running_loop()
    print(
        "Ingestion paused pending human review. "
        f"Open {config.OPERATIONAL_MANIFEST_PATH} and press ENTER to continue..."
    )
    try:
        await loop.run_in_executor(None, input)
    except EOFError:
        logger.warning("Non-interactive stdin detected; manifest remains pending review.")
        return manifest

    manifest["status"] = "approved"
    manifest["review"] = {
        **(manifest.get("review") or {}),
        "approved": True,
        "approved_at": _utcnow_iso(),
        "approval_mode": "manual",
    }
    save_operational_manifest(manifest)
    logger.info("Operational manifest approved manually.")
    return manifest


def manifest_approved(manifest: dict[str, Any] | None) -> bool:
    if manifest is None:
        return False
    review = manifest.get("review") or {}
    return bool(review.get("approved")) or manifest.get("status") == "approved"


def operational_exchanges_from_manifest(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return sorted(config.WHITELIST_EXCHANGES)
    operational = manifest.get("operational") or {}
    exchanges, _ = apply_whitelist_guards(
        list(operational.get("exchanges") or []),
        list((manifest.get("guards") or {}).get("whitelist_assets") or config.WHITELIST_ASSETS),
    )
    return exchanges


def build_whitelist_fallback_manifest() -> dict[str, Any]:
    """Minimal manifest using only immutable whitelist guards."""
    operational_exchanges, operational_assets = apply_whitelist_guards([], [])
    operational_symbols = symbols_for_assets(operational_assets)
    return {
        "generated_at": _utcnow_iso(),
        "status": "pending_review",
        "guards": {
            "whitelist_exchanges_locked": True,
            "whitelist_assets_locked": True,
            "whitelist_exchanges": sorted(config.WHITELIST_EXCHANGES),
            "whitelist_assets": sorted(config.WHITELIST_ASSETS),
        },
        "filters": {
            "min_trust_score": config.LIQUIDITY_MIN_TRUST_SCORE,
            "min_24h_volume_usd": config.LIQUIDITY_MIN_24H_VOLUME_USD,
            "quote_currencies": list(config.LIQUIDITY_QUOTE_CURRENCIES),
            "max_dynamic_exchanges": config.LIQUIDITY_MAX_DYNAMIC_EXCHANGES,
            "max_dynamic_assets": config.LIQUIDITY_MAX_DYNAMIC_ASSETS,
            "coinmarketcap_enabled": config.COINMARKETCAP_ENABLED,
            "fallback_mode": True,
        },
        "dynamic_candidates": {
            "exchanges": [],
            "assets": [],
            "coingecko_exchanges": [],
            "coingecko_assets": [],
            "coinmarketcap_exchanges": [],
            "coinmarketcap_assets": [],
            "ccxt_pairs_sample_count": 0,
        },
        "operational": {
            "exchanges": operational_exchanges,
            "assets": operational_assets,
            "symbols": operational_symbols,
            "ingestion_ready_exchanges": sorted(
                set(operational_exchanges) & set(config.INGESTION_READY_EXCHANGES)
            ),
        },
        "review": {
            "approved": False,
            "approved_at": None,
            "instruction": (
                "Fallback manifest generated after discovery failure. "
                "Whitelist entries are locked and cannot be removed."
            ),
        },
    }


def cross_pairs_for_assets(assets: list[str]) -> list[str]:
    pairs: set[str] = set()
    asset_set = { _normalize_asset(item) for item in assets }

    if "BTC" in asset_set and "ETH" in asset_set:
        pairs.add("ETH/BTC")

    for coin in sorted(asset_set):
        if coin in config.CROSS_QUOTES:
            continue
        if "BTC" in asset_set:
            pairs.add(f"{coin}/BTC")
        if "ETH" in asset_set and coin != "ETH":
            pairs.add(f"{coin}/ETH")

    return sorted(pairs)


def polling_symbols_from_manifest(
    manifest: dict[str, Any] | None,
) -> tuple[list[str], list[str], list[str]]:
    """
    Derive spot, cross, and perpetual symbol lists from the operational manifest.
    """
    if manifest is None:
        spot_symbols = config.all_spot_symbols()
        cross_symbols = config.cross_pairs()
        perp_symbols = config.perpetual_symbols()
        return spot_symbols, cross_symbols, perp_symbols

    operational = manifest.get("operational") or {}
    assets = operational_assets_from_manifest(manifest)
    quote_currencies = set(config.LIQUIDITY_QUOTE_CURRENCIES)
    manifest_symbols = list(operational.get("symbols") or symbols_for_assets(assets))

    spot_symbols: set[str] = set()
    cross_symbols: set[str] = set()
    for symbol in manifest_symbols:
        if "/" not in symbol:
            continue
        _, quote = symbol.split("/", 1)
        normalized_quote = _normalize_asset(quote)
        if normalized_quote in quote_currencies:
            spot_symbols.add(symbol)
        else:
            cross_symbols.add(symbol)

    for pair in cross_pairs_for_assets(assets):
        if pair.split("/", 1)[1] in quote_currencies:
            spot_symbols.add(pair)
        else:
            cross_symbols.add(pair)

    all_spot = sorted(spot_symbols | cross_symbols)
    perp_symbols = sorted(
        symbol for symbol in spot_symbols if symbol.endswith(f"/{config.QUOTE_BASE}")
    )
    return all_spot, sorted(cross_symbols), perp_symbols


def operational_assets_from_manifest(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return sorted(config.WHITELIST_ASSETS)
    operational = manifest.get("operational") or {}
    _, assets = apply_whitelist_guards(
        list((manifest.get("guards") or {}).get("whitelist_exchanges") or config.WHITELIST_EXCHANGES),
        list(operational.get("assets") or []),
    )
    return assets
