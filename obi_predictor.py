"""
BLACKDARK — Order Book Imbalance (OBI) & Flash Crash Predictor (Point 41).

Computes weighted depth imbalance from aggregated order books, tracks rate-of-
change dynamics, and emits institutional flash crash / liquidity drought flags.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

import config
logger = logging.getLogger("BLACKDARK.OBIPredictor")

WarningType = Literal["flash_crash_warning", "liquidity_drought"]


class OrderBookImbalance(BaseModel):
    exchange: str
    symbol: str
    asset: str
    market_type: str = "spot"
    depth_levels: int = Field(ge=1)
    weighted_bid_volume: float = Field(ge=0)
    weighted_ask_volume: float = Field(ge=0)
    imbalance_ratio: float = Field(ge=-1.0, le=1.0)
    timestamp: str | None = None


class FlashCrashWarning(BaseModel):
    warning_type: WarningType
    asset: str
    exchange: str
    symbol: str
    current_obi: float
    obi_delta: float
    z_score: float
    severity: float = Field(ge=0.0, le=100.0)
    message: str


class AssetOBISnapshot(BaseModel):
    asset: str
    average_obi: float
    min_obi: float
    max_obi: float
    venue_count: int
    warnings: list[FlashCrashWarning] = Field(default_factory=list)


@dataclass
class _OBIHistoryState:
    values: deque[float] = field(default_factory=lambda: deque(maxlen=config.OBI_HISTORY_WINDOW))


_history_by_key: dict[str, _OBIHistoryState] = defaultdict(_OBIHistoryState)


def _asset_from_symbol(symbol: str) -> str:
    base = symbol.split("/")[0]
    if "@" in base:
        return base.split("@")[0]
    return base


def _safe_levels(raw_levels: Any) -> list[list[float]]:
    levels: list[list[float]] = []
    if not isinstance(raw_levels, list):
        return levels
    for level in raw_levels:
        try:
            if not level or len(level) < 2:
                continue
            price = float(level[0])
            amount = float(level[1])
            if price <= 0 or amount <= 0:
                continue
            levels.append([price, amount])
        except (TypeError, ValueError):
            continue
    return levels


def _weighted_side_volume(
    levels: list[list[float]],
    *,
    depth_levels: int,
    weight_decay: float,
) -> float:
    total = 0.0
    for index, (price, amount) in enumerate(levels[:depth_levels]):
        weight = weight_decay**index
        total += weight * price * amount
    return total


async def calculate_order_book_imbalance(
    order_book: dict[str, Any],
    *,
    exchange: str,
    symbol: str,
    depth_levels: int | None = None,
    weight_decay: float | None = None,
) -> OrderBookImbalance | None:
    """
    Compute weighted order book imbalance from bid/ask depth.

    Formula: (BidVol - AskVol) / (BidVol + AskVol), range [-1, 1].
    """
    try:
        levels = depth_levels or config.OBI_DEPTH_LEVELS
        decay = weight_decay if weight_decay is not None else config.OBI_WEIGHT_DECAY

        bids = _safe_levels(order_book.get("bids"))
        asks = _safe_levels(order_book.get("asks"))
        if not bids or not asks:
            return None

        bid_volume = _weighted_side_volume(bids, depth_levels=levels, weight_decay=decay)
        ask_volume = _weighted_side_volume(asks, depth_levels=levels, weight_decay=decay)
        denominator = bid_volume + ask_volume
        if denominator <= 0:
            return None

        imbalance = (bid_volume - ask_volume) / denominator
        market_type = str(order_book.get("market_type") or "spot")
        resolved_symbol = str(order_book.get("symbol") or symbol)

        return OrderBookImbalance(
            exchange=exchange,
            symbol=resolved_symbol,
            asset=_asset_from_symbol(resolved_symbol),
            market_type=market_type,
            depth_levels=levels,
            weighted_bid_volume=round(bid_volume, 6),
            weighted_ask_volume=round(ask_volume, 6),
            imbalance_ratio=round(max(-1.0, min(1.0, imbalance)), 6),
            timestamp=str(order_book.get("timestamp") or "") or None,
        )
    except Exception:
        logger.exception(
            "OBI calculation failed | exchange=%s symbol=%s",
            str(exchange).replace("\r", " ").replace("\n", " "),
            str(symbol).replace("\r", " ").replace("\n", " "),
        )
        return None


def _history_key(exchange: str, symbol: str) -> str:
    return f"{exchange}:{symbol}"


def _update_history(key: str, obi_value: float) -> list[float]:
    state = _history_by_key[key]
    state.values.append(obi_value)
    return list(state.values)


def forecast_flash_crash(
    *,
    asset: str,
    exchange: str,
    symbol: str,
    current_obi: float,
    history: list[float],
) -> FlashCrashWarning | None:
    """
    Detect sharp negative shifts in OBI beyond a volatility z-score threshold.
    """
    try:
        if len(history) < config.OBI_MIN_HISTORY_POINTS:
            return None

        deltas = [history[idx] - history[idx - 1] for idx in range(1, len(history))]
        if not deltas:
            return None

        mean_delta = statistics.fmean(deltas)
        stdev = statistics.pstdev(deltas) if len(deltas) > 1 else abs(mean_delta) or 1e-6
        stdev = max(stdev, 1e-6)
        obi_delta = current_obi - history[-2]
        z_score = (obi_delta - mean_delta) / stdev

        warning_type: WarningType | None = None
        if z_score <= -config.OBI_FLASH_CRASH_Z_THRESHOLD:
            warning_type = "flash_crash_warning"
        elif (
            current_obi <= config.OBI_LIQUIDITY_DROUGHT_THRESHOLD
            and obi_delta <= -config.OBI_LIQUIDITY_DROUGHT_DELTA
        ):
            warning_type = "liquidity_drought"

        if warning_type is None:
            return None

        severity = min(
            100.0,
            abs(z_score) * 12.0 + abs(min(0.0, current_obi)) * 40.0,
        )
        label = (
            "Flash Crash Warning"
            if warning_type == "flash_crash_warning"
            else "Liquidity Drought"
        )
        return FlashCrashWarning(
            warning_type=warning_type,
            asset=asset,
            exchange=exchange,
            symbol=symbol,
            current_obi=round(current_obi, 6),
            obi_delta=round(obi_delta, 6),
            z_score=round(z_score, 4),
            severity=round(severity, 2),
            message=(
                f"{label} on {asset} | OBI {current_obi:.3f} "
                f"delta {obi_delta:+.3f} z={z_score:.2f}"
            ),
        )
    except Exception:
        logger.exception(
            "Flash crash forecast failed | asset=%s exchange=%s symbol=%s",
            str(asset).replace("\r", " ").replace("\n", " "),
            str(exchange).replace("\r", " ").replace("\n", " "),
            str(symbol).replace("\r", " ").replace("\n", " "),
        )
        return None


async def analyze_order_book_snapshot(
    order_books: dict[str, dict[str, dict[str, Any]]],
) -> tuple[list[OrderBookImbalance], list[FlashCrashWarning]]:
    imbalances: list[OrderBookImbalance] = []
    warnings: list[FlashCrashWarning] = []

    for exchange_id, books in order_books.items():
        for storage_key, book in books.items():
            try:
                symbol = str(book.get("symbol") or storage_key.split("@")[0])
                obi = await calculate_order_book_imbalance(
                    book,
                    exchange=exchange_id,
                    symbol=symbol,
                )
                if obi is None:
                    continue

                imbalances.append(obi)
                history = _update_history(_history_key(exchange_id, symbol), obi.imbalance_ratio)
                warning = forecast_flash_crash(
                    asset=obi.asset,
                    exchange=exchange_id,
                    symbol=symbol,
                    current_obi=obi.imbalance_ratio,
                    history=history,
                )
                if warning is not None:
                    warnings.append(warning)
            except Exception:
                logger.exception(
                    "OBI snapshot analysis failed | exchange=%s key=%s",
                    str(exchange_id).replace("\r", " ").replace("\n", " "),
                    str(storage_key).replace("\r", " ").replace("\n", " "),
                )
                continue

    return imbalances, warnings


def _aggregate_asset_snapshots(
    imbalances: list[OrderBookImbalance],
    warnings: list[FlashCrashWarning],
) -> dict[str, AssetOBISnapshot]:
    grouped: dict[str, list[OrderBookImbalance]] = defaultdict(list)
    warning_map: dict[str, list[FlashCrashWarning]] = defaultdict(list)

    for item in imbalances:
        grouped[item.asset].append(item)
    for warning in warnings:
        warning_map[warning.asset].append(warning)

    snapshots: dict[str, AssetOBISnapshot] = {}
    for asset, rows in grouped.items():
        ratios = [row.imbalance_ratio for row in rows]
        snapshots[asset] = AssetOBISnapshot(
            asset=asset,
            average_obi=round(statistics.fmean(ratios), 6),
            min_obi=round(min(ratios), 6),
            max_obi=round(max(ratios), 6),
            venue_count=len(rows),
            warnings=warning_map.get(asset, []),
        )
    return snapshots


def obi_score_adjustment_for_asset(asset: str, context: dict[str, Any]) -> float:
    """
    Convert OBI posture into an Opportunity Score boost or penalty.

    Positive OBI adds a modest boost; active warnings apply penalties.
    """
    try:
        adjustments = context.get("obi_score_adjustments") or {}
        if asset in adjustments:
            return float(adjustments[asset])

        asset_snapshots = context.get("obi_by_asset") or {}
        snapshot = asset_snapshots.get(asset)
        if not snapshot:
            return 0.0

        if isinstance(snapshot, dict):
            average_obi = float(snapshot.get("average_obi") or 0.0)
            warnings = snapshot.get("warnings") or []
        else:
            average_obi = float(getattr(snapshot, "average_obi", 0.0))
            warnings = getattr(snapshot, "warnings", [])

        boost = max(0.0, average_obi) * config.OBI_SCORE_BOOST_MAX
        penalty = 0.0
        for warning in warnings:
            if isinstance(warning, dict):
                severity = float(warning.get("severity") or 0.0)
                warning_type = str(warning.get("warning_type") or "")
            else:
                severity = float(getattr(warning, "severity", 0.0))
                warning_type = str(getattr(warning, "warning_type", ""))
            weight = 1.0 if warning_type == "flash_crash_warning" else 0.75
            penalty += (severity / 100.0) * config.OBI_FLASH_PENALTY_MAX * weight

        return round(
            max(-config.OBI_FLASH_PENALTY_MAX, min(config.OBI_SCORE_BOOST_MAX, boost - penalty)),
            2,
        )
    except Exception:
        logger.exception("OBI score adjustment failed | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))
        return 0.0


def get_obi_for_asset(asset: str, context: dict[str, Any]) -> float | None:
    """Return the current average OBI for an asset from a built context."""
    try:
        asset_snapshots = context.get("obi_by_asset") or {}
        snapshot = asset_snapshots.get(asset)
        if snapshot is None:
            return None
        if isinstance(snapshot, dict):
            return float(snapshot.get("average_obi"))
        return float(snapshot.average_obi)
    except Exception:
        return None


async def build_obi_context(
    order_books: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    imbalances, warnings = await analyze_order_book_snapshot(order_books)
    snapshots = _aggregate_asset_snapshots(imbalances, warnings)

    score_adjustments = {
        asset: obi_score_adjustment_for_asset(
            asset,
            {
                "obi_by_asset": {
                    key: value.model_dump() for key, value in snapshots.items()
                },
                "obi_warnings": [warning.model_dump() for warning in warnings],
            },
        )
        for asset in snapshots
    }

    return {
        "obi_metrics": [item.model_dump() for item in imbalances],
        "obi_by_asset": {key: value.model_dump() for key, value in snapshots.items()},
        "obi_warnings": [warning.model_dump() for warning in warnings],
        "obi_score_adjustments": score_adjustments,
    }


async def build_obi_context_safe(
    order_books: dict[str, dict[str, dict[str, Any]]] | None,
) -> dict[str, Any]:
    """Build OBI context without ever raising to protect engine loops."""
    if not order_books:
        return {
            "obi_metrics": [],
            "obi_by_asset": {},
            "obi_warnings": [],
            "obi_score_adjustments": {},
        }
    try:
        return await build_obi_context(order_books)
    except Exception:
        logger.exception("OBI context build failed safely; returning empty context.")
        return {
            "obi_metrics": [],
            "obi_by_asset": {},
            "obi_warnings": [],
            "obi_score_adjustments": {},
        }


def merge_market_context(
    base_context: dict[str, Any] | None,
    obi_context: dict[str, Any] | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base_context or {})
    if obi_context:
        merged.update(obi_context)
    return merged


async def get_current_obi_context_for_books(
    order_books: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Convenience helper for engine/oracle consumers."""
    return await build_obi_context_safe(order_books)
