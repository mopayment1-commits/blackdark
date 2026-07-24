"""
BLACKDARK — Research Lab & Institutional Analytics (Wave 5).

Aggregates multi-modal intelligence, financial model proxies (VaR, NVT, MVRV, SOPR),
and economic moat metrics for B2B / acquisition readiness.
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.ResearchLab")

_SUPPLY_ESTIMATES: dict[str, float] = {
    "BTC": 19_700_000,
    "ETH": 120_000_000,
    "SOL": 580_000_000,
    "BNB": 145_000_000,
    "XRP": 57_000_000_000,
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_asset(symbol: str) -> str:
    cleaned = symbol.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4]
    return cleaned


async def _fetch_klines(pair: str, interval: str = "1d", limit: int = 90) -> list[float]:
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                rows = await resp.json()
        return [float(row[4]) for row in rows if isinstance(row, list) and len(row) > 4]
    except (aiohttp.ClientError, TypeError, ValueError):
        return []


async def _fetch_ticker(pair: str) -> dict | None:
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        return {
            "price": float(data["lastPrice"]),
            "quote_volume": float(data.get("quoteVolume") or 0),
            "change_24h": float(data.get("priceChangePercent") or 0),
        }
    except (aiohttp.ClientError, KeyError, TypeError, ValueError):
        return None


def _compute_var(closes: list[float], notional: float, confidence: float = 0.95) -> dict[str, float]:
    if len(closes) < 10:
        return {"var_usd": 0.0, "var_percent": 0.0, "confidence": confidence, "method": "insufficient_data"}
    returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    sorted_returns = sorted(returns)
    idx = max(0, int((1 - confidence) * len(sorted_returns)) - 1)
    var_return = sorted_returns[idx]
    var_usd = abs(var_return * notional)
    return {
        "var_usd": round(var_usd, 2),
        "var_percent": round(abs(var_return) * 100, 3),
        "confidence": confidence,
        "method": "historical_simulation",
        "sample_days": len(returns),
    }


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


async def compute_financial_models(asset: str, *, notional: float = 10_000) -> dict[str, Any]:
    """VaR, NVT, MVRV and SOPR proxies for institutional research."""
    asset = _normalize_asset(asset)
    pair = f"{asset}USDT"
    ticker = await _fetch_ticker(pair)
    closes = await _fetch_klines(pair, interval="1d", limit=90)

    if ticker is None:
        return {"asset": asset, "error": "Market data unavailable", "timestamp": _utcnow_iso()}

    price = float(ticker["price"])
    quote_volume = float(ticker["quote_volume"])
    supply = _SUPPLY_ESTIMATES.get(asset, 100_000_000)
    market_cap = price * supply

    var_metrics = _compute_var(closes, notional)

    nvt = market_cap / quote_volume if quote_volume > 0 else 0.0
    nvt_signal = (
        "Overheated (high NVT)" if nvt > 120 else "Fair range" if nvt > 40 else "Undervalued zone"
    )

    sma200 = _sma(closes, min(200, len(closes)))
    sma30 = _sma(closes, min(30, len(closes)))
    mvrv_proxy = price / sma200 if sma200 and sma200 > 0 else 1.0
    sopr_proxy = price / sma30 if sma30 and sma30 > 0 else 1.0

    return {
        "asset": asset,
        "price": price,
        "market_cap_estimate_usd": round(market_cap, 0),
        "quote_volume_24h": round(quote_volume, 0),
        "notional_for_var": notional,
        "var": var_metrics,
        "nvt": {
            "ratio": round(nvt, 2),
            "signal": nvt_signal,
            "method": "market_cap / 24h_quote_volume",
        },
        "mvrv_proxy": {
            "ratio": round(mvrv_proxy, 3),
            "signal": "Overbought" if mvrv_proxy > 1.4 else "Accumulation" if mvrv_proxy < 0.9 else "Neutral",
            "method": "price / SMA(200) proxy",
        },
        "sopr_proxy": {
            "ratio": round(sopr_proxy, 3),
            "signal": "Profit taking" if sopr_proxy > 1.05 else "Capitulation" if sopr_proxy < 0.95 else "Neutral",
            "method": "price / SMA(30) proxy",
        },
        "disclaimer": "MVRV/SOPR are SMA-based proxies unless on-chain API is configured.",
        "timestamp": _utcnow_iso(),
    }


def _history_storage_bytes() -> int:
    history_dir = config.DATA_DIR / "history"
    if not history_dir.exists():
        return 0
    return sum(f.stat().st_size for f in history_dir.rglob("*") if f.is_file())


async def compute_economic_moat() -> dict[str, Any]:
    """Quantify proprietary data depth for acquisition / investor decks."""
    from database import fetch_oracle_audit_stats, fetch_system_telemetry

    telemetry = await fetch_system_telemetry()
    audit = await fetch_oracle_audit_stats(limit=50)

    total_records = (
        int(telemetry.get("pricing_count") or 0)
        + int(telemetry.get("orderbook_count") or 0)
        + int(telemetry.get("funding_count") or 0)
        + int(telemetry.get("institutional_flow_count") or 0)
        + int(audit.get("total_predictions") or 0)
    )
    db_mb = float(telemetry.get("database_size_bytes") or 0) / (1024 * 1024)
    history_mb = _history_storage_bytes() / (1024 * 1024)
    accuracy = float(audit.get("average_accuracy_percent") or 0)

    depth_score = min(100, int(
        math.log10(max(total_records, 1)) * 18
        + min(db_mb, 500) * 0.08
        + min(history_mb, 2000) * 0.04
        + accuracy * 0.25
    ))

    replication_years = round(max(1.0, math.log10(max(total_records, 10)) * 1.2), 1)

    return {
        "moat_score": depth_score,
        "moat_label": "Strong" if depth_score >= 70 else "Growing" if depth_score >= 45 else "Emerging",
        "total_data_records": total_records,
        "database_size_mb": round(db_mb, 2),
        "parquet_history_mb": round(history_mb, 2),
        "oracle_predictions": audit.get("total_predictions", 0),
        "oracle_accuracy_percent": accuracy,
        "replication_estimate_years": replication_years,
        "ip_assets": [
            "CVVD Cross-Venue Whale Detection",
            "Sector Inflow Index (SII)",
            "Multi-Modal Opportunity Score",
            "Order Book Imbalance Predictor",
            "Prediction Audit Trail",
        ],
        "telemetry": telemetry,
        "timestamp": _utcnow_iso(),
    }


async def build_research_lab_report() -> dict[str, Any]:
    """Full institutional research snapshot."""
    from database import fetch_latest_macro_market_log, fetch_oracle_audit_stats
    from onchain_tracker import build_onchain_context_safe
    from sentiment_engine import build_sentiment_context_safe
    from whale_tracker import get_latest_institutional_context

    assets = list(config.WHITELIST_ASSETS)
    moat = await compute_economic_moat()
    institutional = await get_latest_institutional_context()
    sentiment = await build_sentiment_context_safe(assets)
    onchain = await build_onchain_context_safe()
    macro = await fetch_latest_macro_market_log()
    audit = await fetch_oracle_audit_stats(limit=10)

    financial_snapshots = []
    for asset in assets[:3]:
        try:
            financial_snapshots.append(await compute_financial_models(asset, notional=10_000))
        except Exception:
            logger.exception("Financial model failed | asset=%s", asset)

    return {
        "report": "BLACKDARK Institutional Research Lab",
        "version": config.B2B_FEED_VERSION,
        "generated_at": _utcnow_iso(),
        "economic_moat": moat,
        "oracle_audit": {
            "total_predictions": audit.get("total_predictions"),
            "average_accuracy_percent": audit.get("average_accuracy_percent"),
            "recent": audit.get("recent", [])[:5],
        },
        "whale_intelligence": {
            "alert_count": len(institutional.get("whale_alerts") or []),
            "sector_flows": len(institutional.get("sector_flows") or []),
            "top_alerts": (institutional.get("whale_alerts") or [])[:3],
        },
        "sentiment": sentiment.get("sentiment_compound_index") or {},
        "onchain": onchain.get("onchain_by_asset") or {},
        "macro_regime": macro,
        "financial_models": financial_snapshots,
        "methodology": {
            "cvvd": "Cross-Venue Volume Discrepancy",
            "sii": "Sector Inflow Index",
            "var": "Historical daily-return simulation",
            "nvt": "Market cap estimate / 24h volume",
        },
    }


async def export_signed_research(provided_key: str) -> dict[str, Any]:
    """B2B signed research export for acquisition conversations."""
    from whale_tracker import InstitutionalDataExporter

    exporter = InstitutionalDataExporter()
    if not exporter.authorize(provided_key):
        raise PermissionError("Invalid B2B API key.")

    report = await build_research_lab_report()
    payload = {
        "product": "BLACKDARK Research Lab Export",
        "feed_version": config.B2B_FEED_VERSION,
        "generated_at": _utcnow_iso(),
        "report": report,
    }
    payload["signature"] = exporter.sign_payload(
        {k: v for k, v in payload.items() if k != "signature"}
    )
    return payload
