"""
BLACKDARK — Institutional Manipulation & Sector Rotation Algorithm.

Proprietary cross-venue volume discrepancy detection (CVVD), Sector Inflow
Index (SII), SQLite persistence, and a secure B2B data exporter for external
trading desk proposals.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import math
import os
import statistics
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp
from pydantic import BaseModel, Field

import config
from database import (
    fetch_institutional_feed_rows,
    fetch_latest_order_books,
    fetch_latest_sector_flows,
    fetch_latest_whale_alerts,
    init_db,
    insert_institutional_flows,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("BLACKDARK.WhaleTracker")

REQUEST_TIMEOUT_SECONDS = 15
Side = Literal["buy", "sell"]
ManipulationPattern = Literal[
    "cross_venue_manipulation",
    "liquidity_spoof",
    "iceberg_cluster",
]

TRADE_ENDPOINTS: dict[str, dict[str, str]] = {
    "binance": {
        "base_url": "https://api.binance.com",
        "path": "/api/v3/trades",
    },
    "okx": {
        "base_url": "https://www.okx.com",
        "path": "/api/v5/market/trades",
    },
    "bybit": {
        "base_url": "https://api.bybit.com",
        "path": "/v5/market/recent-trade",
    },
}


class NormalizedTrade(BaseModel):
    exchange: str
    symbol: str
    asset: str
    sector: str
    side: Side
    price: float = Field(gt=0)
    quantity: float = Field(gt=0)
    notional_usd: float = Field(gt=0)
    trade_time_ms: int


class ManipulationAlert(BaseModel):
    pattern: ManipulationPattern
    sector: str
    volume_exchange: str
    liquidity_exchange: str
    symbol: str
    asset: str
    side: Side | None = None
    manipulation_score: float = Field(ge=0, le=100)
    volume_spike_ratio: float
    liquidity_drop_ratio: float
    volume_usd: float
    liquidity_usd: float
    iceberg_trade_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SectorInflowIndex(BaseModel):
    sector: str
    sii_score: float = Field(ge=-100, le=100)
    net_flow_usd: float
    flow_velocity_usd: float
    flow_acceleration_usd: float
    buy_notional_usd: float
    sell_notional_usd: float
    trade_count: int
    window_seconds: int


# Backward-compatible aliases consumed by dashboard / engine integrations.
WhaleAlert = ManipulationAlert
SectorFlowSnapshot = SectorInflowIndex


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _asset_from_symbol(symbol: str) -> str:
    return symbol.split("/")[0]


def _sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset, "Unclassified")


def _enabled_exchange_ids() -> list[str]:
    return list(config.enabled_exchanges().keys())


def _to_native_symbol(exchange_id: str, symbol: str) -> str:
    base, quote = symbol.split("/")
    if exchange_id == "okx":
        return f"{base}-{quote}"
    return f"{base}{quote}"


def _tanh_scale(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return math.tanh(value / scale)


def compute_order_book_liquidity_usd(
    bids: list[list[float]],
    asks: list[list[float]],
    depth_levels: int | None = None,
) -> float:
    levels = depth_levels or config.CVVD_BOOK_DEPTH_LEVELS
    bid_liq = sum(float(level[0]) * float(level[1]) for level in bids[:levels])
    ask_liq = sum(float(level[0]) * float(level[1]) for level in asks[:levels])
    return bid_liq + ask_liq


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any] | None = None,
) -> Any:
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()


def _parse_binance_trades(exchange_id: str, symbol: str, payload: list[Any]) -> list[NormalizedTrade]:
    asset = _asset_from_symbol(symbol)
    sector = _sector_for_asset(asset)
    trades: list[NormalizedTrade] = []

    for row in payload:
        price = float(row["price"])
        quantity = float(row["qty"])
        side: Side = "sell" if row.get("isBuyerMaker") else "buy"
        trades.append(
            NormalizedTrade(
                exchange=exchange_id,
                symbol=symbol,
                asset=asset,
                sector=sector,
                side=side,
                price=price,
                quantity=quantity,
                notional_usd=price * quantity,
                trade_time_ms=int(row["time"]),
            )
        )
    return trades


def _parse_okx_trades(exchange_id: str, symbol: str, payload: dict[str, Any]) -> list[NormalizedTrade]:
    asset = _asset_from_symbol(symbol)
    sector = _sector_for_asset(asset)
    trades: list[NormalizedTrade] = []

    for row in payload.get("data", []):
        price = float(row["px"])
        quantity = float(row["sz"])
        side: Side = "buy" if str(row.get("side", "")).lower() == "buy" else "sell"
        trades.append(
            NormalizedTrade(
                exchange=exchange_id,
                symbol=symbol,
                asset=asset,
                sector=sector,
                side=side,
                price=price,
                quantity=quantity,
                notional_usd=price * quantity,
                trade_time_ms=int(row["ts"]),
            )
        )
    return trades


def _parse_bybit_trades(exchange_id: str, symbol: str, payload: dict[str, Any]) -> list[NormalizedTrade]:
    asset = _asset_from_symbol(symbol)
    sector = _sector_for_asset(asset)
    trades: list[NormalizedTrade] = []

    for row in payload.get("result", {}).get("list", []):
        price = float(row["price"])
        quantity = float(row["size"])
        side: Side = "buy" if str(row.get("side", "")).lower() == "buy" else "sell"
        trades.append(
            NormalizedTrade(
                exchange=exchange_id,
                symbol=symbol,
                asset=asset,
                sector=sector,
                side=side,
                price=price,
                quantity=quantity,
                notional_usd=price * quantity,
                trade_time_ms=int(row["time"]),
            )
        )
    return trades


async def _fetch_exchange_trades(
    session: aiohttp.ClientSession,
    exchange_id: str,
    symbol: str,
) -> list[NormalizedTrade]:
    native = _to_native_symbol(exchange_id, symbol)
    endpoints = TRADE_ENDPOINTS[exchange_id]

    if exchange_id == "binance":
        payload = await _fetch_json(
            session,
            f"{endpoints['base_url']}{endpoints['path']}",
            {"symbol": native, "limit": 1000},
        )
        return _parse_binance_trades(exchange_id, symbol, payload)

    if exchange_id == "okx":
        payload = await _fetch_json(
            session,
            f"{endpoints['base_url']}{endpoints['path']}",
            {"instId": native, "limit": 100},
        )
        return _parse_okx_trades(exchange_id, symbol, payload)

    payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['path']}",
        {"category": "spot", "symbol": native, "limit": 100},
    )
    return _parse_bybit_trades(exchange_id, symbol, payload)


async def fetch_all_recent_trades(
    session: aiohttp.ClientSession,
) -> list[NormalizedTrade]:
    tasks = [
        _fetch_exchange_trades(session, exchange_id, symbol)
        for exchange_id in _enabled_exchange_ids()
        for symbol in config.SYMBOLS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    trades: list[NormalizedTrade] = []
    idx = 0
    for exchange_id in _enabled_exchange_ids():
        for symbol in config.SYMBOLS:
            result = results[idx]
            idx += 1
            if isinstance(result, Exception):
                logger.warning(
                    "Trade fetch failed | exchange=%s symbol=%s error=%s",
                    exchange_id,
                    symbol,
                    result,
                )
                continue
            trades.extend(result)
    return trades


def _aggregate_sector_volume(
    trades: list[NormalizedTrade],
    window_seconds: int,
    *,
    end_ms: int | None = None,
) -> dict[str, dict[str, float]]:
    end = end_ms or int(time.time() * 1000)
    start = end - (window_seconds * 1000)
    prior_start = start - (window_seconds * 1000)

    current: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    prior: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for trade in trades:
        if prior_start <= trade.trade_time_ms < start:
            prior[trade.sector][trade.exchange] += trade.notional_usd
        elif start <= trade.trade_time_ms <= end:
            current[trade.sector][trade.exchange] += trade.notional_usd

    return {
        sector: {
            exchange: {
                "current": current[sector].get(exchange, 0.0),
                "prior": prior[sector].get(exchange, 0.0),
            }
            for exchange in _enabled_exchange_ids()
        }
        for sector in set(config.SECTOR_MAP.values())
    }


def _aggregate_sector_liquidity(
    order_books: dict[str, dict[str, dict[str, Any]]],
    prior_liquidity: dict[str, dict[str, float]] | None = None,
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    current: dict[str, dict[str, float]] = defaultdict(dict)
    prior = prior_liquidity or {}

    for exchange_id in _enabled_exchange_ids():
        books = order_books.get(exchange_id, {})
        for symbol in config.SYMBOLS:
            book = books.get(symbol)
            if not book:
                continue
            asset = _asset_from_symbol(symbol)
            sector = _sector_for_asset(asset)
            liquidity = compute_order_book_liquidity_usd(book["bids"], book["asks"])
            current[sector][exchange_id] = current[sector].get(exchange_id, 0.0) + liquidity

    return current, prior


def _detect_iceberg_cluster(trades: list[NormalizedTrade]) -> tuple[bool, int, float]:
    if len(trades) < config.CVVD_ICEBERG_TRADE_COUNT:
        return False, len(trades), 1.0

    notionals = [trade.notional_usd for trade in trades]
    mean = statistics.fmean(notionals)
    if mean <= 0:
        return False, len(trades), 1.0

    stdev = statistics.pstdev(notionals)
    cv = stdev / mean
    is_cluster = cv <= config.CVVD_ICEBERG_SIZE_CV_MAX
    return is_cluster, len(trades), cv


def detect_cross_venue_manipulation(
    trades: list[NormalizedTrade],
    order_books: dict[str, dict[str, dict[str, Any]]],
    prior_liquidity: dict[str, dict[str, float]] | None = None,
    *,
    window_seconds: int | None = None,
) -> list[ManipulationAlert]:
    """
    Cross-Venue Volume Discrepancy Algorithm (CVVD).

    Flags institutional spoofing / iceberg activity when volume spikes on one
    venue while visible liquidity simultaneously collapses on another venue
    within the same thematic sector.
    """
    window = window_seconds or config.SECTOR_FLOW_WINDOW_SECONDS
    volume_profile = _aggregate_sector_volume(trades, window)
    current_liquidity, prior_liquidity = _aggregate_sector_liquidity(
        order_books,
        prior_liquidity,
    )

    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - (window * 1000)
    recent_trades = [trade for trade in trades if trade.trade_time_ms >= cutoff_ms]

    alerts: list[ManipulationAlert] = []

    for sector in sorted(set(config.SECTOR_MAP.values())):
        sector_trades = [trade for trade in recent_trades if trade.sector == sector]
        exchanges = _enabled_exchange_ids()

        for volume_exchange in exchanges:
            current_volume = volume_profile.get(sector, {}).get(volume_exchange, {}).get("current", 0.0)
            prior_volume = volume_profile.get(sector, {}).get(volume_exchange, {}).get("prior", 0.0)
            volume_baseline = max(prior_volume, 1.0)
            volume_spike_ratio = current_volume / volume_baseline

            if volume_spike_ratio < config.CVVD_VOLUME_SPIKE_RATIO:
                continue

            for liquidity_exchange in exchanges:
                if liquidity_exchange == volume_exchange:
                    continue

                current_liq = current_liquidity.get(sector, {}).get(liquidity_exchange, 0.0)
                previous_liq = prior_liquidity.get(sector, {}).get(liquidity_exchange, current_liq)
                liquidity_baseline = max(previous_liq, 1.0)
                liquidity_drop_ratio = (current_liq - previous_liq) / liquidity_baseline

                if liquidity_drop_ratio > config.CVVD_LIQUIDITY_DROP_RATIO:
                    continue

                symbol_trades = [
                    trade
                    for trade in sector_trades
                    if trade.exchange == volume_exchange
                ]
                iceberg, iceberg_count, iceberg_cv = _detect_iceberg_cluster(symbol_trades)

                dominant_side: Side | None = None
                if symbol_trades:
                    buy_total = sum(t.notional_usd for t in symbol_trades if t.side == "buy")
                    sell_total = sum(t.notional_usd for t in symbol_trades if t.side == "sell")
                    dominant_side = "buy" if buy_total >= sell_total else "sell"

                pattern: ManipulationPattern = "cross_venue_manipulation"
                if iceberg:
                    pattern = "iceberg_cluster"
                elif volume_spike_ratio >= config.CVVD_VOLUME_SPIKE_RATIO * 1.5:
                    pattern = "liquidity_spoof"

                manipulation_score = min(
                    100.0,
                    (volume_spike_ratio * abs(liquidity_drop_ratio) * 100.0)
                    + (10.0 if iceberg else 0.0),
                )

                if manipulation_score < config.CVVD_MIN_MANIPULATION_SCORE:
                    continue

                top_trade = max(symbol_trades, key=lambda item: item.notional_usd, default=None)
                symbol = top_trade.symbol if top_trade else config.SYMBOLS[0]
                asset = top_trade.asset if top_trade else _asset_from_symbol(symbol)

                alerts.append(
                    ManipulationAlert(
                        pattern=pattern,
                        sector=sector,
                        volume_exchange=volume_exchange,
                        liquidity_exchange=liquidity_exchange,
                        symbol=symbol,
                        asset=asset,
                        side=dominant_side,
                        manipulation_score=round(manipulation_score, 2),
                        volume_spike_ratio=round(volume_spike_ratio, 4),
                        liquidity_drop_ratio=round(liquidity_drop_ratio, 4),
                        volume_usd=round(current_volume, 2),
                        liquidity_usd=round(current_liq, 2),
                        iceberg_trade_count=iceberg_count,
                        metadata={
                            "prior_volume_usd": round(prior_volume, 2),
                            "prior_liquidity_usd": round(previous_liq, 2),
                            "iceberg_size_cv": round(iceberg_cv, 4),
                            "window_seconds": window,
                        },
                    )
                )

    alerts.sort(key=lambda item: item.manipulation_score, reverse=True)
    return alerts


def compute_sector_inflow_index(
    trades: list[NormalizedTrade],
    *,
    window_seconds: int | None = None,
    bucket_count: int | None = None,
) -> list[SectorInflowIndex]:
    """
    Proprietary Sector Inflow Index (SII).

    Computes rolling net capital acceleration (rate of change of sector inflow)
    rather than raw volume, producing a -100..100 momentum index per sector.
    """
    window = window_seconds or config.SECTOR_FLOW_WINDOW_SECONDS
    buckets = bucket_count or config.SII_BUCKET_COUNT
    bucket_seconds = max(window // buckets, 1)
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (window * 1000)

    sector_bucket_flows: dict[str, list[float]] = {
        sector: [0.0] * buckets for sector in set(config.SECTOR_MAP.values())
    }
    sector_buy: dict[str, float] = defaultdict(float)
    sector_sell: dict[str, float] = defaultdict(float)
    sector_count: dict[str, int] = defaultdict(int)

    for trade in trades:
        if trade.trade_time_ms < start_ms:
            continue

        sector_count[trade.sector] += 1
        if trade.side == "buy":
            sector_buy[trade.sector] += trade.notional_usd
            signed = trade.notional_usd
        else:
            sector_sell[trade.sector] += trade.notional_usd
            signed = -trade.notional_usd

        elapsed_ms = trade.trade_time_ms - start_ms
        bucket_idx = min(buckets - 1, int(elapsed_ms / (bucket_seconds * 1000)))
        sector_bucket_flows.setdefault(trade.sector, [0.0] * buckets)
        sector_bucket_flows[trade.sector][bucket_idx] += signed

    snapshots: list[SectorInflowIndex] = []

    for sector in sorted(set(config.SECTOR_MAP.values())):
        flows = sector_bucket_flows.get(sector, [0.0] * buckets)
        cumulative = list(flows)
        for idx in range(1, len(cumulative)):
            cumulative[idx] += cumulative[idx - 1]

        net_flow = cumulative[-1] if cumulative else 0.0
        velocity = cumulative[-1] - cumulative[-2] if len(cumulative) >= 2 else net_flow
        acceleration = (
            (cumulative[-1] - cumulative[-2]) - (cumulative[-2] - cumulative[-3])
            if len(cumulative) >= 3
            else velocity
        )

        velocity_component = _tanh_scale(velocity, config.SII_VELOCITY_SCALE_USD) * 50.0
        acceleration_component = _tanh_scale(acceleration, config.SII_ACCELERATION_SCALE_USD) * 50.0
        sii_score = max(-100.0, min(100.0, velocity_component + acceleration_component))

        snapshots.append(
            SectorInflowIndex(
                sector=sector,
                sii_score=round(sii_score, 2),
                net_flow_usd=round(net_flow, 2),
                flow_velocity_usd=round(velocity, 2),
                flow_acceleration_usd=round(acceleration, 2),
                buy_notional_usd=round(sector_buy.get(sector, 0.0), 2),
                sell_notional_usd=round(sector_sell.get(sector, 0.0), 2),
                trade_count=sector_count.get(sector, 0),
                window_seconds=window,
            )
        )

    snapshots.sort(key=lambda item: abs(item.sii_score), reverse=True)
    return snapshots


def compute_sector_liquidity_radar(
    trades: list[NormalizedTrade],
    window_seconds: int | None = None,
) -> list[SectorInflowIndex]:
    """Backward-compatible alias for the SII calculator."""
    return compute_sector_inflow_index(trades, window_seconds=window_seconds)


async def scan_whale_trades(
    session: aiohttp.ClientSession | None = None,
    order_books: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> list[ManipulationAlert]:
    """
    Run the CVVD algorithm against live public trade and order-book snapshots.

    Replaces the legacy fixed-notional threshold with cross-venue discrepancy
    detection tuned for institutional spoofing and iceberg activity.
    """
    owns_session = session is None
    if session is None:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        session = aiohttp.ClientSession(timeout=timeout)

    try:
        trades = await fetch_all_recent_trades(session)
        books = order_books if order_books is not None else await fetch_latest_order_books()
        return detect_cross_venue_manipulation(trades, books)
    finally:
        if owns_session and session is not None:
            await session.close()


async def persist_manipulation_alerts(alerts: list[ManipulationAlert]) -> int:
    if not alerts:
        return 0

    ts = _utcnow_iso()
    rows = [
        (
            ts,
            "manipulation_alert",
            alert.volume_exchange,
            alert.symbol,
            alert.asset,
            alert.sector,
            alert.side,
            None,
            None,
            alert.volume_usd,
            None,
            json.dumps(
                {
                    "pattern": alert.pattern,
                    "liquidity_exchange": alert.liquidity_exchange,
                    "manipulation_score": alert.manipulation_score,
                    "volume_spike_ratio": alert.volume_spike_ratio,
                    "liquidity_drop_ratio": alert.liquidity_drop_ratio,
                    "liquidity_usd": alert.liquidity_usd,
                    "iceberg_trade_count": alert.iceberg_trade_count,
                    **alert.metadata,
                },
                separators=(",", ":"),
            ),
        )
        for alert in alerts
    ]
    await insert_institutional_flows(rows)
    return len(rows)


async def persist_whale_alerts(alerts: list[ManipulationAlert]) -> int:
    return await persist_manipulation_alerts(alerts)


async def persist_sector_inflow_index(snapshots: list[SectorInflowIndex]) -> int:
    if not snapshots:
        return 0

    ts = _utcnow_iso()
    rows = [
        (
            ts,
            "sector_inflow_index",
            None,
            None,
            None,
            snapshot.sector,
            None,
            None,
            None,
            None,
            snapshot.sii_score,
            json.dumps(
                {
                    "sii_score": snapshot.sii_score,
                    "net_flow_usd": snapshot.net_flow_usd,
                    "flow_velocity_usd": snapshot.flow_velocity_usd,
                    "flow_acceleration_usd": snapshot.flow_acceleration_usd,
                    "buy_notional_usd": snapshot.buy_notional_usd,
                    "sell_notional_usd": snapshot.sell_notional_usd,
                    "trade_count": snapshot.trade_count,
                    "window_seconds": snapshot.window_seconds,
                },
                separators=(",", ":"),
            ),
        )
        for snapshot in snapshots
    ]
    await insert_institutional_flows(rows)
    return len(rows)


async def persist_sector_flows(snapshots: list[SectorInflowIndex]) -> int:
    return await persist_sector_inflow_index(snapshots)


def _parse_metadata(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("metadata_json")
    if not raw:
        return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def build_institutional_context(
    whale_alerts: list[dict[str, Any]],
    sector_flows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize manipulation alerts and SII data for scoring consumers."""
    asset_boosts: dict[str, float] = defaultdict(float)
    sector_boosts: dict[str, float] = defaultdict(float)

    for alert in whale_alerts:
        asset = str(alert.get("asset") or "")
        if not asset:
            continue
        meta = _parse_metadata(alert)
        score = float(meta.get("manipulation_score") or alert.get("notional_usd") or 0.0)
        asset_boosts[asset] += min(
            config.MANIPULATION_SCORE_BOOST_MAX,
            score / 10.0,
        )

    for flow in sector_flows:
        sector = str(flow.get("sector") or "")
        if not sector:
            continue
        meta = _parse_metadata(flow)
        sii = float(meta.get("sii_score") or flow.get("net_flow_usd") or 0.0)
        sector_boosts[sector] = min(
            config.MANIPULATION_SCORE_BOOST_MAX,
            abs(sii) / 12.5,
        )

    return {
        "whale_alerts": whale_alerts,
        "sector_flows": sector_flows,
        "manipulation_alerts": whale_alerts,
        "sector_inflow_index": sector_flows,
        "asset_score_boosts": dict(asset_boosts),
        "sector_score_boosts": dict(sector_boosts),
    }


def whale_score_boost_for_asset(asset: str, context: dict[str, Any]) -> float:
    boosts = context.get("asset_score_boosts", {})
    sector = _sector_for_asset(asset)
    sector_boost = context.get("sector_score_boosts", {}).get(sector, 0.0)
    asset_boost = boosts.get(asset, 0.0)
    return round(
        min(config.MANIPULATION_SCORE_BOOST_MAX, asset_boost + sector_boost * 0.35),
        2,
    )


async def get_latest_whale_alerts(limit: int = 50) -> list[dict[str, Any]]:
    return await fetch_latest_whale_alerts(limit=limit)


async def get_latest_sector_flows(limit: int = 20) -> list[dict[str, Any]]:
    return await fetch_latest_sector_flows(limit=limit)


async def get_latest_institutional_context() -> dict[str, Any]:
    whale_alerts = await get_latest_whale_alerts(limit=50)
    sector_flows = await get_latest_sector_flows(limit=20)
    return build_institutional_context(whale_alerts, sector_flows)


class InstitutionalDataExporter:
    """
    Secure B2B data exporter for packaging proprietary institutional feeds.

    Designed for sales proposals to external trading companies. Requires an
    API key (env: BLACKDARK_B2B_API_KEY) for authenticated export generation.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv(config.B2B_API_KEY_ENV, "")
        self.feed_version = config.B2B_FEED_VERSION

    def authorize(self, provided_key: str) -> bool:
        if not provided_key:
            return False
        demo_key = config.B2B_DEMO_API_KEY
        if demo_key and hmac.compare_digest(demo_key, provided_key):
            return True
        if not self.api_key:
            logger.warning("B2B exporter has no configured API key.")
            return False
        return hmac.compare_digest(self.api_key, provided_key)

    def is_demo_key(self, provided_key: str) -> bool:
        demo_key = config.B2B_DEMO_API_KEY
        return bool(demo_key and provided_key and hmac.compare_digest(demo_key, provided_key))

    def sign_payload(self, payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hmac.new(
            self.api_key.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest

    async def export_institutional_feed(
        self,
        *,
        provided_key: str,
        limit: int | None = None,
    ) -> dict[str, Any]:
        if not self.authorize(provided_key):
            raise PermissionError("Invalid B2B API key.")

        is_demo = self.is_demo_key(provided_key)
        export_limit = min(limit or config.B2B_DEFAULT_EXPORT_LIMIT, config.B2B_DEMO_EXPORT_LIMIT if is_demo else config.B2B_DEFAULT_EXPORT_LIMIT)
        rows = await fetch_institutional_feed_rows(limit=export_limit)
        payload = {
            "product": "BLACKDARK Institutional Manipulation Feed",
            "feed_version": self.feed_version,
            "generated_at": _utcnow_iso(),
            "record_count": len(rows),
            "methodology": {
                "cvvd": "Cross-Venue Volume Discrepancy Algorithm",
                "sii": "Sector Inflow Index (capital acceleration)",
            },
            "records": rows,
        }
        payload["signature"] = self.sign_payload(
            {key: value for key, value in payload.items() if key != "signature"}
        )
        return payload

    async def generate_sales_proposal_payload(
        self,
        *,
        provided_key: str,
        client_name: str,
        lookback_limit: int = 100,
    ) -> dict[str, Any]:
        feed = await self.export_institutional_feed(
            provided_key=provided_key,
            limit=lookback_limit,
        )
        manipulation = [
            row for row in feed["records"] if row.get("flow_type") == "manipulation_alert"
        ]
        sii_rows = [
            row for row in feed["records"] if row.get("flow_type") == "sector_inflow_index"
        ]

        sectors = sorted({row.get("sector") for row in sii_rows if row.get("sector")})
        proposal = {
            "client": client_name,
            "prepared_at": _utcnow_iso(),
            "feed_version": self.feed_version,
            "executive_summary": {
                "manipulation_alerts": len(manipulation),
                "sectors_monitored": sectors,
                "value_proposition": (
                    "Proprietary cross-venue manipulation radar and sector inflow "
                    "acceleration index for institutional execution desks."
                ),
            },
            "sample_manipulation_alerts": manipulation[:5],
            "sample_sector_inflow_index": sii_rows[:5],
            "delivery": {
                "format": "JSON",
                "refresh_cadence_seconds": config.POLL_INTERVAL_SECONDS,
                "authentication": "HMAC-SHA256 signed API key",
            },
            "raw_feed_reference": {
                "record_count": feed["record_count"],
                "signature": feed["signature"],
            },
        }
        proposal["signature"] = self.sign_payload(
            {key: value for key, value in proposal.items() if key != "signature"}
        )
        return proposal


class WhaleTracker:
    """Runs CVVD scans and SII calculations on a fixed cadence."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._prior_liquidity: dict[str, dict[str, float]] = {}

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def run_cycle(self) -> dict[str, Any]:
        await init_db()
        session = self._ensure_session()
        trades = await fetch_all_recent_trades(session)
        order_books = await fetch_latest_order_books()

        manipulation_alerts = detect_cross_venue_manipulation(
            trades,
            order_books,
            self._prior_liquidity,
        )
        sector_snapshots = compute_sector_inflow_index(trades)

        current_liquidity, _ = _aggregate_sector_liquidity(order_books, self._prior_liquidity)
        self._prior_liquidity = current_liquidity

        saved_alerts = await persist_manipulation_alerts(manipulation_alerts)
        saved_sectors = await persist_sector_inflow_index(sector_snapshots)

        if manipulation_alerts:
            top = manipulation_alerts[0]
            logger.info(
                "CVVD alert | %s | %s vol@%s liq@%s | score=%.1f spike=%.2fx drop=%.1f%%",
                top.pattern.upper(),
                top.sector,
                top.volume_exchange.upper(),
                top.liquidity_exchange.upper(),
                top.manipulation_score,
                top.volume_spike_ratio,
                top.liquidity_drop_ratio * 100.0,
            )

        for snapshot in sector_snapshots[:3]:
            logger.info(
                "SII | %s | index=%.1f | velocity=$%.0f accel=$%.0f | trades=%d",
                snapshot.sector,
                snapshot.sii_score,
                snapshot.flow_velocity_usd,
                snapshot.flow_acceleration_usd,
                snapshot.trade_count,
            )

        alert_payload = [alert.model_dump() for alert in manipulation_alerts]
        sector_payload = [snap.model_dump() for snap in sector_snapshots]

        return {
            "manipulation_alerts": alert_payload,
            "sector_inflow_index": sector_payload,
            "whale_alerts": alert_payload,
            "sector_flows": sector_payload,
            "saved_alerts": saved_alerts,
            "saved_sectors": saved_sectors,
        }


async def run_whale_tracker_loop() -> None:
    await init_db()
    tracker = WhaleTracker()
    logger.info(
        "Institutional tracker started | CVVD + SII | window=%ss",
        config.SECTOR_FLOW_WINDOW_SECONDS,
    )
    try:
        while True:
            try:
                await tracker.run_cycle()
            except Exception:
                logger.exception("Institutional tracker cycle failed; continuing.")
            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
    finally:
        await tracker.close()


def main() -> None:
    try:
        asyncio.run(run_whale_tracker_loop())
    except KeyboardInterrupt:
        logger.info("Institutional tracker shutdown complete.")


if __name__ == "__main__":
    main()
