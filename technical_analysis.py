"""
BLACKDARK — Classic TA Engine (Plan Point 42).

RSI, MACD, and EMA structure computed from local/Binance closes.
"""

from __future__ import annotations

from typing import Any

import config


def compute_ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for value in values[period:]:
        ema = value * multiplier + ema * (1 - multiplier)
    return ema


def compute_rsi(closes: list[float], period: int | None = None) -> float | None:
    period = period or config.TA_RSI_PERIOD
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for idx in range(1, len(closes)):
        delta = closes[idx] - closes[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def rsi_signal_label(rsi: float) -> str:
    if rsi >= config.TA_RSI_OVERBOUGHT:
        return "Overbought"
    if rsi >= 55:
        return "Bullish momentum"
    if rsi >= 45:
        return "Neutral"
    if rsi >= config.TA_RSI_OVERSOLD:
        return "Bearish momentum"
    return "Oversold"


def macd_trend_label(closes: list[float]) -> str:
    if len(closes) < config.TA_MACD_SLOW:
        return "Insufficient candle data"
    ema_fast = compute_ema(closes, config.TA_MACD_FAST)
    ema_slow = compute_ema(closes, config.TA_MACD_SLOW)
    if ema_fast is None or ema_slow is None:
        return "Insufficient candle data"
    macd = ema_fast - ema_slow
    prev_closes = closes[:-1]
    prev_fast = compute_ema(prev_closes, config.TA_MACD_FAST)
    prev_slow = compute_ema(prev_closes, config.TA_MACD_SLOW)
    if prev_fast is None or prev_slow is None:
        return "MACD consolidating"
    prev_macd = prev_fast - prev_slow
    if macd > 0 and macd > prev_macd:
        return "Bullish crossover — momentum rising"
    if macd < 0 and macd < prev_macd:
        return "Bearish crossover — momentum falling"
    if macd > prev_macd:
        return "MACD turning up — early bullish shift"
    if macd < prev_macd:
        return "MACD turning down — early bearish shift"
    return "MACD flat — consolidation phase"


def ema_position_label(price: float, closes: list[float]) -> str:
    ema50 = compute_ema(closes, 50) if len(closes) >= 50 else None
    ema200 = compute_ema(closes, 200) if len(closes) >= 200 else compute_ema(closes, min(len(closes), 100))
    if ema50 is None:
        return "Insufficient EMA data"
    above50 = price >= ema50
    if ema200 is None:
        return "Price above 50 EMA" if above50 else "Price below 50 EMA"
    above200 = price >= ema200
    if above50 and above200:
        return "Price trading above 50 & 200 EMA — bullish structure"
    if above50 and not above200:
        return "Price above 50 EMA, below 200 EMA — recovery attempt"
    if not above50 and above200:
        return "Price below 50 EMA, holding 200 EMA — pullback zone"
    return "Price below key EMAs — downtrend structure"


def ta_score_adjustment(rsi: float | None, macd_label: str, ema_label: str) -> float:
    """Small deterministic oracle score nudge from TA alignment."""
    adj = 0.0
    if rsi is not None:
        if rsi <= config.TA_RSI_OVERSOLD:
            adj += 2.5
        elif rsi >= config.TA_RSI_OVERBOUGHT:
            adj -= 2.5
    lower_macd = macd_label.lower()
    if "bullish crossover" in lower_macd:
        adj += 2.0
    elif "bearish crossover" in lower_macd:
        adj -= 2.0
    lower_ema = ema_label.lower()
    if "bullish structure" in lower_ema:
        adj += 1.5
    elif "downtrend structure" in lower_ema:
        adj -= 1.5
    return adj


async def build_ta_bundle(asset: str, price: float | None = None) -> dict[str, Any]:
    from forecast_engine import load_price_series

    closes, source = await load_price_series(asset, limit=220)
    if not closes:
        return {"asset": asset, "available": False, "source": source}

    current_price = price if price is not None else closes[-1]
    rsi = compute_rsi(closes)
    macd_label = macd_trend_label(closes)
    ema_label = ema_position_label(current_price, closes)
    return {
        "asset": asset,
        "available": True,
        "source": source,
        "price": round(current_price, 6),
        "rsi": rsi,
        "rsi_signal": rsi_signal_label(rsi) if rsi is not None else "N/A",
        "macd": macd_label,
        "ema": ema_label,
        "score_adjustment": ta_score_adjustment(rsi, macd_label, ema_label),
    }
