"""
Futures CVD / Taker Flow metric (#59) — silent Decision Engine input.

CVD from aggressive taker buy/sell volumes with trade-side classification QA.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.FuturesCVD")

FUTURES_BASE = "https://fapi.binance.com"
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_SYMBOL_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT", "BNB": "BNBUSDT"}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _pair(symbol: str) -> str:
    return _SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}USDT")


def _classify_taker_qa(
    *,
    volume: float,
    taker_buy: float,
) -> dict[str, Any]:
    """Trade-side classification QA — misclassified taker data flagged."""
    if volume <= 0:
        return {"ok": False, "reason": "zero_volume", "classification_valid": False}
    taker_sell = volume - taker_buy
    issues: list[str] = []
    if taker_buy < 0:
        issues.append("negative_taker_buy")
    if taker_sell < 0:
        issues.append("negative_taker_sell")
    if taker_buy > volume * 1.0001:
        issues.append("taker_buy_exceeds_volume")
    ratio = taker_buy / volume if volume > 0 else 0
    if ratio < 0 or ratio > 1:
        issues.append("invalid_taker_ratio")
    return {
        "ok": len(issues) == 0,
        "classification_valid": len(issues) == 0,
        "taker_buy_volume": round(taker_buy, 6),
        "taker_sell_volume": round(max(0.0, taker_sell), 6),
        "taker_buy_ratio": round(ratio, 4),
        "issues": issues,
    }


async def compute_futures_cvd(symbol: str = "BTC", *, interval: str = "1h", limit: int = 48) -> dict[str, Any]:
    """Futures CVD + taker imbalance with trade-side QA (#59)."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    pair = _pair(sym)
    url = f"{FUTURES_BASE}/fapi/v1/klines"
    params = {"symbol": pair, "interval": interval, "limit": min(500, limit)}

    timeout = aiohttp.ClientTimeout(total=3.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return {
                        "ok": False,
                        "feature": "#59",
                        "symbol": sym,
                        "data_state": "MISSING",
                        "cvd": None,
                        "missing_not_zero": True,
                        "error": f"http_{resp.status}",
                    }
                rows = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        return {
            "ok": False,
            "feature": "#59",
            "symbol": sym,
            "data_state": "MISSING",
            "cvd": None,
            "missing_not_zero": True,
            "error": str(exc),
        }

    if not isinstance(rows, list) or not rows:
        return {
            "ok": False,
            "feature": "#59",
            "symbol": sym,
            "data_state": "MISSING",
            "cvd": None,
            "missing_not_zero": True,
        }

    cvd = 0.0
    qa_pass = 0
    qa_fail = 0
    series: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 11:
            continue
        volume = float(row[5] or 0)
        taker_buy = float(row[9] or 0)
        qa = _classify_taker_qa(volume=volume, taker_buy=taker_buy)
        if qa["classification_valid"]:
            qa_pass += 1
        else:
            qa_fail += 1
            continue
        delta = qa["taker_buy_volume"] - qa["taker_sell_volume"]
        cvd += delta
        series.append(
            {
                "open_time": int(row[0]),
                "cvd_delta": round(delta, 6),
                "cvd_cumulative": round(cvd, 6),
                "taker_buy_ratio": qa["taker_buy_ratio"],
            }
        )

    total_bars = qa_pass + qa_fail
    qa_score = round(qa_pass / total_bars, 3) if total_bars else None
    imbalance = None
    if series:
        imbalance = series[-1].get("taker_buy_ratio")

    bias = "neutral"
    if cvd > 0 and imbalance and imbalance > 0.55:
        bias = "buy_pressure"
    elif cvd < 0 and imbalance and imbalance < 0.45:
        bias = "sell_pressure"

    headline = None
    if bias == "sell_pressure" and qa_score and qa_score >= 0.9:
        headline = f"Futures taker sell pressure on {sym} — CVD negative, QA passed"
    elif bias == "buy_pressure" and qa_score and qa_score >= 0.9:
        headline = f"Futures taker buy pressure on {sym} — CVD positive, QA passed"

    elapsed = time.perf_counter() - t0
    return {
        "ok": qa_pass > 0,
        "feature": "#59",
        "ingestion_role": "decision_engine_input",
        "symbol": sym,
        "pair": pair,
        "interval": interval,
        "cvd": round(cvd, 6) if qa_pass > 0 else None,
        "taker_imbalance": imbalance,
        "bias": bias,
        "trade_side_qa": {
            "passed_bars": qa_pass,
            "failed_bars": qa_fail,
            "qa_score": qa_score,
            "classification_valid": qa_fail == 0,
        },
        "series_tail": series[-5:],
        "data_state": "LIVE" if qa_pass > 0 else "MISSING",
        "missing_not_zero": True,
        "headline": headline,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
