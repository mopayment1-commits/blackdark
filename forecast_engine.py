"""
BLACKDARK — Time-Series Forecast Engine (Priority 2).

Reads from local data lake + pricing_logs + Binance klines (never random API at oracle time).
Uses EMA + linear trend — no heavy ML deps required for v1.
"""

from __future__ import annotations

import logging
import statistics
from datetime import UTC, datetime
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.ForecastEngine")

HORIZONS_HOURS = (1, 4, 24)


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_asset(symbol: str) -> str:
    cleaned = symbol.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4]
    return cleaned


_ALLOWED_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"}


async def _fetch_binance_closes(pair: str, interval: str = "1h", limit: int = 168) -> list[float]:
    """Klines with Vision/US failover — api.binance.com is often blocked on Railway."""
    if not pair.isalnum():
        return []
    if interval not in _ALLOWED_INTERVALS:
        interval = "1h"
    hosts = (
        "https://data-api.binance.vision",
        "https://api.binance.us",
        "https://api.binance.com",
    )
    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for host in hosts:
                url = f"{host}/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        rows = await resp.json()
                    closes = [float(row[4]) for row in rows if isinstance(row, list) and len(row) > 4]
                    if closes:
                        return closes
                except (aiohttp.ClientError, TypeError, ValueError):
                    continue
    except (aiohttp.ClientError, TypeError, ValueError):
        return []
    return []


async def load_price_series(asset: str, *, limit: int = 200) -> tuple[list[float], str]:
    """Load closes: local DB first, then data lake, then Binance klines."""
    asset = _normalize_asset(asset)
    pair = f"{asset}USDT"
    symbol_slash = f"{asset}/USDT"

    from database import fetch_recent_pricing_for_symbol

    local_rows = await fetch_recent_pricing_for_symbol(symbol_slash, limit=limit)
    if len(local_rows) >= 24:
        closes = [float(r["price"]) for r in reversed(local_rows)]
        return closes, "local_pricing_logs"

    try:
        from data_lake import get_category_bundle

        price_items = await get_category_bundle("prices", max_age_seconds=3600)
        lake_prices: list[float] = []
        for row in price_items:
            payload = row.get("payload") or {}
            if payload.get("symbol") == pair or payload.get("asset") == asset:
                p = payload.get("price") or payload.get("mark_price")
                if p:
                    lake_prices.append(float(p))
        if len(lake_prices) >= 5:
            return lake_prices[-limit:], "data_lake_snapshots"
    except Exception:
        logger.warning("Data lake price load failed | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))

    closes = await _fetch_binance_closes(pair, interval="1h", limit=min(limit, 168))
    if closes:
        return closes, "binance_1h_klines"

    return [], "unavailable"


def _ema(values: list[float], alpha: float = 0.25) -> float:
    if not values:
        return 0.0
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema
    return ema


def _linear_slope(values: list[float]) -> float:
    n = len(values)
    if n < 3:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    num = sum((xs[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((xs[i] - x_mean) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return num / den


def _volatility_pct(closes: list[float]) -> float:
    if len(closes) < 5:
        return 2.0
    returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1]]
    if len(returns) < 2:
        return 2.0
    return statistics.pstdev(returns) * 100


def _direction(current: float, target: float, threshold_pct: float = 0.15) -> str:
    if current <= 0:
        return "neutral"
    change = ((target - current) / current) * 100
    if change >= threshold_pct:
        return "up"
    if change <= -threshold_pct:
        return "down"
    return "neutral"


def compute_forecast(closes: list[float], current_price: float | None = None) -> dict[str, Any]:
    if len(closes) < 12:
        return {
            "available": False,
            "reason": "insufficient_history",
            "sample_size": len(closes),
        }

    price_now = current_price if current_price and current_price > 0 else closes[-1]
    ema_val = _ema(closes[-48:] if len(closes) >= 48 else closes)
    slope = _linear_slope(closes[-24:])
    vol_pct = _volatility_pct(closes[-48:] if len(closes) >= 48 else closes)

    horizons: dict[str, Any] = {}
    for hours in HORIZONS_HOURS:
        projected = max(0.0, ema_val + slope * hours)
        change_pct = ((projected - price_now) / price_now) * 100 if price_now else 0.0
        horizons[f"h{hours}"] = {
            "horizon_hours": hours,
            "price_forecast": round(projected, 8 if price_now < 1 else 2),
            "change_pct": round(change_pct, 3),
            "direction": _direction(price_now, projected),
        }

    primary = horizons["h24"]
    base_conf = max(35.0, min(92.0, 72.0 - vol_pct * 4.0 + min(len(closes), 168) * 0.05))
    trend_strength = abs(slope / price_now * 100) if price_now else 0
    confidence = round(min(95.0, base_conf + trend_strength * 2), 1)

    return {
        "available": True,
        "model": "ema_linear_trend_v1",
        "sample_size": len(closes),
        "volatility_pct": round(vol_pct, 3),
        "current_price": round(price_now, 8 if price_now < 1 else 2),
        "direction_24h": primary["direction"],
        "price_forecast_24h": primary["price_forecast"],
        "change_pct_24h": primary["change_pct"],
        "confidence_percent": confidence,
        "horizons": horizons,
        "disclaimer": "Statistical forecast from local price history — not guaranteed.",
    }


async def build_asset_forecast(asset: str, *, current_price: float | None = None) -> dict[str, Any]:
    asset = _normalize_asset(asset)
    closes, source = await load_price_series(asset)
    forecast = compute_forecast(closes, current_price=current_price)
    forecast["asset"] = asset
    forecast["data_source"] = source
    forecast["timestamp"] = _utcnow_iso()

    if forecast.get("available"):
        try:
            from database import insert_forecast_logs

            await insert_forecast_logs(asset, float(forecast["current_price"]), forecast)
        except Exception:
            logger.exception("Failed to persist forecast logs | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))

    return forecast


def blend_oracle_confidence(base_confidence: int, forecast: dict[str, Any], verdict: str) -> int:
    if not forecast.get("available"):
        return base_confidence

    fc = float(forecast.get("confidence_percent") or 50)
    direction = str(forecast.get("direction_24h") or "neutral")
    verdict_upper = verdict.upper()

    aligned = (
        (verdict_upper == "BUY" and direction == "up")
        or (verdict_upper in {"SELL", "CAUTION"} and direction == "down")
        or (verdict_upper == "WAIT" and direction == "neutral")
    )
    penalty = 8 if not aligned and direction != "neutral" else 0
    blended = round(base_confidence * 0.55 + fc * 0.45) - penalty
    return max(20, min(98, blended))


async def enrich_oracle_payload(payload: dict[str, Any]) -> dict[str, Any]:
    asset = str(payload.get("symbol") or "BTC")
    price = float(payload.get("price") or 0)
    forecast = await build_asset_forecast(asset, current_price=price)
    payload["forecast"] = forecast

    if forecast.get("available"):
        payload["confidence"] = blend_oracle_confidence(
            int(payload.get("confidence") or 50),
            forecast,
            str(payload.get("verdict") or "WAIT"),
        )
        h24 = (forecast.get("horizons") or {}).get("h24") or {}
        payload["next_24h_low"] = min(
            float(payload.get("next_24h_low") or price),
            float(h24.get("price_forecast") or price) * 0.98,
        )
        payload["next_24h_high"] = max(
            float(payload.get("next_24h_high") or price),
            float(h24.get("price_forecast") or price) * 1.02,
        )
        payload["forecast_summary"] = (
            f"24h forecast: {forecast.get('direction_24h', 'neutral').upper()} "
            f"→ ${h24.get('price_forecast', price):,.2f} "
            f"({h24.get('change_pct', 0):+.2f}%) · model confidence {forecast.get('confidence_percent')}%"
        )
    else:
        payload["forecast_summary"] = "Forecast warming up — need more local price history."

    return payload


async def _current_binance_price(pair: str) -> float | None:
    ticker_url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(ticker_url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
        actual = float(data.get("price") or 0)
        return actual if actual > 0 else None
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def _resolve_forecast_row(row: dict[str, Any]) -> bool:
    from database import resolve_forecast_log

    asset = str(row.get("asset") or "")
    pair = f"{_normalize_asset(asset)}USDT"
    if not pair.isalnum():
        return False
    actual = await _current_binance_price(pair)
    price_at = float(row.get("price_at") or 0)
    forecast_price = float(row.get("price_forecast") or 0)
    if price_at <= 0 or actual is None:
        return False

    predicted_dir = str(row.get("direction_predicted") or "neutral")
    actual_dir = _direction(price_at, actual, threshold_pct=0.5)
    price_error_pct = abs((actual - forecast_price) / price_at) * 100
    direction_hit = predicted_dir == actual_dir or predicted_dir == "neutral"
    accuracy = round(max(0.0, 100.0 - price_error_pct * 2 + (20 if direction_hit else 0)), 2)

    await resolve_forecast_log(
        int(row["id"]),
        actual,
        actual_dir,
        accuracy,
    )
    return True


async def run_forecast_audit() -> dict[str, Any]:
    """Resolve matured forecasts vs actual Binance price (flywheel)."""
    from database import fetch_unresolved_forecast_logs

    unresolved = await fetch_unresolved_forecast_logs(limit=100)
    resolved = 0
    for row in unresolved:
        if await _resolve_forecast_row(row):
            resolved += 1

    return {"resolved": resolved, "checked": len(unresolved)}
