"""
On-chain live indexer — free public blockchain APIs for #577 metrics library.

Sources (no paid API keys required):
  BTC: mempool.space (hash rate), blockchain.info (active addresses), Blockchair (tx count)
  ETH: Blockchair (tx count), Blockscout (transactions today)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

from bd_platform.institutional_standards import missing_value

logger = logging.getLogger("BLACKDARK.OnchainLiveIndexer")

_ASSET_CHAIN: dict[str, dict[str, str]] = {
    "BTC": {"blockchair": "bitcoin", "coingecko": "bitcoin", "blockchain_chart": "BTC"},
    "ETH": {"blockchair": "ethereum", "coingecko": "ethereum", "blockscout": "eth"},
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _get_json(url: str, *, params: dict | None = None) -> Any:
    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception as exc:
        logger.warning("onchain live fetch failed for %s: %s", url, exc)
        return None


def _metric(
    value: Any,
    *,
    available: bool,
    source: str,
    as_of: str | None = None,
) -> dict[str, Any]:
    return {
        "value": value if available and value is not None else missing_value(numeric=True),
        "available": available and value is not None,
        "as_of": as_of or _utcnow(),
        "live_source": source,
        "evidence_class": "PRODUCTION_VERIFIED" if available and value is not None else "BACKTESTED",
    }


async def _fetch_btc_hashrate() -> dict[str, Any]:
    data = await _get_json("https://mempool.space/api/v1/mining/hashrate/1m")
    if not isinstance(data, dict) or not data.get("hashrates"):
        blockchair = await _get_json("https://api.blockchair.com/bitcoin/stats")
        hr_raw = ((blockchair or {}).get("data") or {}).get("hashrate_24h")
        if hr_raw is None:
            return _metric(None, available=False, source="mempool.space+blockchair")
        eh_s = float(hr_raw) / 1e18
        return _metric(round(eh_s, 2), available=True, source="blockchair_public")

    latest = data["hashrates"][-1]
    hs = latest.get("avgHashrate")
    if hs is None:
        return _metric(None, available=False, source="mempool.space")
    eh_s = float(hs) / 1e18
    return _metric(round(eh_s, 2), available=True, source="mempool.space")


async def _fetch_btc_active_addresses() -> dict[str, Any]:
    data = await _get_json(
        "https://api.blockchain.info/charts/n-unique-addresses",
        params={"timespan": "1days", "format": "json", "sampled": "false"},
    )
    values = (data or {}).get("values") or []
    if not values:
        return _metric(None, available=False, source="blockchain.info")
    latest = values[-1].get("y")
    if latest is None:
        return _metric(None, available=False, source="blockchain.info")
    return _metric(int(latest), available=True, source="blockchain.info")


async def _fetch_blockchair_tx_count(chain: str) -> dict[str, Any]:
    data = await _get_json(f"https://api.blockchair.com/{chain}/stats")
    tx = ((data or {}).get("data") or {}).get("transactions_24h")
    if tx is None:
        return _metric(None, available=False, source=f"blockchair_{chain}")
    return _metric(int(tx), available=True, source=f"blockchair_{chain}")


async def _fetch_eth_transactions_today() -> dict[str, Any]:
    data = await _get_json("https://eth.blockscout.com/api/v2/stats")
    tx = (data or {}).get("transactions_today")
    if tx is None:
        return await _fetch_blockchair_tx_count("ethereum")
    return _metric(int(tx), available=True, source="blockscout_public")


async def _fetch_eth_active_addresses() -> dict[str, Any]:
    """ETH active addresses — not available on free tier without Etherscan key."""
    return _metric(None, available=False, source="unavailable_free_tier")


async def _fetch_exchange_netflow(asset: str) -> dict[str, Any]:
    """Derived from exchange intelligence layer — not a blockchain indexer metric."""
    try:
        from bd_platform.exchange_intelligence_layer import compute_netflow, _load_seed

        seed = _load_seed()
        transfers = seed.get("transfers") or []
        netflow = compute_netflow(transfers, asset=asset)
        net_usd = netflow.get("netflow_usd")
        if net_usd is None:
            return _metric(None, available=False, source="exchange_intelligence_layer")
        return {
            "value": net_usd,
            "available": True,
            "as_of": _utcnow(),
            "live_source": "exchange_intelligence_layer",
            "evidence_class": "BACKTESTED",
            "derived_not_indexer": True,
        }
    except Exception as exc:
        logger.warning("exchange netflow derive failed: %s", exc)
        return _metric(None, available=False, source="exchange_intelligence_layer")


async def fetch_live_onchain_metrics(asset: str = "BTC") -> dict[str, Any]:
    """Fetch live on-chain metrics for asset — fail-closed per metric."""
    sym = asset.upper()
    if sym not in _ASSET_CHAIN:
        return {
            "ok": False,
            "asset": sym,
            "error": "asset_not_supported",
            "metrics": {},
            "live_fetch_attempted": True,
        }

    metrics: dict[str, dict[str, Any]] = {}
    if sym == "BTC":
        hashrate, active, tx_count, netflow = await _gather(
            _fetch_btc_hashrate(),
            _fetch_btc_active_addresses(),
            _fetch_blockchair_tx_count("bitcoin"),
            _fetch_exchange_netflow(sym),
        )
        metrics = {
            "hash_rate": hashrate,
            "active_addresses": active,
            "transaction_count": tx_count,
            "exchange_netflow": netflow,
        }
    elif sym == "ETH":
        active, tx_count, netflow = await _gather(
            _fetch_eth_active_addresses(),
            _fetch_eth_transactions_today(),
            _fetch_exchange_netflow(sym),
        )
        metrics = {
            "active_addresses": active,
            "transaction_count": tx_count,
            "hash_rate": _metric(None, available=False, source="not_applicable_eth"),
            "exchange_netflow": netflow,
        }

    live_count = sum(1 for m in metrics.values() if m.get("available"))
    return {
        "ok": live_count > 0,
        "asset": sym,
        "metrics": metrics,
        "live_metric_count": live_count,
        "live_fetch_attempted": True,
        "data_source": "live_indexer",
        "timestamp": _utcnow(),
    }


async def _gather(*coros):  # type: ignore[no-untyped-def]
    import asyncio

    return await asyncio.gather(*coros)
