"""
On-Chain Metrics Suite — Feature #750 Realized Cap Model merged (Sprint 2).

NOT standalone — Realized Cap integrated into On-Chain Intelligence suite.
True network value via realized cap, realized price, MVRV, and alerts.
Competitor reference: Glassnode Realized Cap methodology.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.OnChainMetricsSuite")

_FEATURE_IDS = [745, 750]
_FEATURE_ID = 750
_FEATURE_ID_MDIA = 745
_MERGED_INTO = "On-Chain Metrics Suite"
_STANDALONE = False
_SEED_PATH = Path("data/onchain_metrics_seed.json")
_SLA_MS = 2000
_ACCURACY_TARGET_PCT = 95
_UPTIME_TARGET_PCT = 99


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"methodology": {}, "supply_estimates": {}, "alert_thresholds": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("onchain metrics seed load failed: %s", exc)
        return {"methodology": {}, "supply_estimates": {}, "alert_thresholds": {}}


def _format_usd(value: float) -> str:
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    return f"${value:,.0f}"


def _build_alerts(
    asset: str,
    mvrv_z: float,
    mvrv_ratio: float,
    thresholds: dict[str, Any],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    z_hot = float(thresholds.get("mvrv_z_overheated") or 2.0)
    z_cold = float(thresholds.get("mvrv_z_undervalued") or -1.0)

    if mvrv_z >= z_hot:
        alerts.append({
            "level": "high",
            "code": "REALIZED_CAP_OVERHEATED",
            "message": f"{asset} MVRV Z-Score {mvrv_z:.2f} — market cap exceeds realized cap significantly",
            "display": f"Alert: Network value overheated | MVRV Z: {mvrv_z:.2f}",
        })
    elif mvrv_z <= z_cold:
        alerts.append({
            "level": "medium",
            "code": "REALIZED_CAP_UNDERVALUED",
            "message": f"{asset} MVRV Z-Score {mvrv_z:.2f} — true network value below market cap",
            "display": f"Alert: Potential undervaluation | MVRV Z: {mvrv_z:.2f}",
        })

    if mvrv_ratio > 3.5:
        alerts.append({
            "level": "high",
            "code": "MVRV_EXTREME",
            "message": f"{asset} MVRV ratio {mvrv_ratio:.2f} — historically elevated",
            "display": f"Alert: MVRV {mvrv_ratio:.2f} — extreme zone",
        })

    return alerts


def _mdia_regime(mdia_days: float, baseline_days: float) -> str:
    ratio = mdia_days / baseline_days if baseline_days > 0 else 1.0
    if ratio >= 1.15:
        return "mature"
    if ratio <= 0.85:
        return "young"
    return "neutral"


async def compute_mdia(asset: str = "BTC") -> dict[str, Any]:
    """Mean Dollar Invested Age — merged #745, not standalone."""
    t0 = time.perf_counter()
    seed = _load_seed()
    mdia_meta = seed.get("mdia_methodology") or {}
    chain_coverage_all = mdia_meta.get("chain_coverage") or {}
    sym = asset.upper().replace("/USDT", "")
    chain_info = chain_coverage_all.get(sym, {})
    supported = bool(chain_info.get("supported", False))

    from bd_platform.onchain_advanced import compute_advanced_metrics

    metrics = await compute_advanced_metrics(sym)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if metrics.get("error"):
        return {
            "ok": False,
            "feature_id": _FEATURE_ID_MDIA,
            "error": metrics["error"],
            "chain_coverage": chain_info,
            "sla_met": elapsed_ms <= _SLA_MS,
            "latency_ms": elapsed_ms,
            "timestamp": _utcnow(),
        }

    if not supported:
        return {
            "ok": True,
            "feature_id": _FEATURE_ID_MDIA,
            "standalone": _STANDALONE,
            "merged_into": _MERGED_INTO,
            "asset": sym,
            "model": "mean_dollar_invested_age",
            "supported": False,
            "chain_coverage": chain_info,
            "valuation_methodology": mdia_meta.get("valuation_methodology"),
            "time_alignment": mdia_meta.get("time_alignment"),
            "disclaimer": "Chain coverage not yet supported for this asset.",
            "sla_met": elapsed_ms <= _SLA_MS,
            "latency_ms": elapsed_ms,
            "timestamp": _utcnow(),
        }

    hodl = metrics.get("hodl_waves") or {}
    price = float(metrics.get("price") or 0)
    short_avg = float(hodl.get("short_term_7d_avg") or price)
    long_avg = float(hodl.get("long_term_90d_avg") or price)
    baseline_days = float((mdia_meta.get("baselines") or {}).get(sym, 180))

    if price > 0 and long_avg > 0:
        hold_ratio = min(1.5, max(0.5, short_avg / long_avg))
        mdia_days = round(baseline_days * hold_ratio, 1)
    else:
        mdia_days = baseline_days

    mdia_years = round(mdia_days / 365, 2)
    regime = _mdia_regime(mdia_days, baseline_days)
    time_alignment = mdia_meta.get("time_alignment") or {}

    return {
        "ok": True,
        "feature_id": _FEATURE_ID_MDIA,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "model": "mean_dollar_invested_age",
        "competitor_reference": mdia_meta.get("competitor_reference", "Glassnode Mean Dollar Invested Age"),
        "mdia_days": mdia_days,
        "mdia_years": mdia_years,
        "mdia_trend": regime,
        "mdia_display": f"MDIA: {mdia_days:.0f} days ({mdia_years:.1f}y) | Regime: {regime}",
        "valuation_methodology": mdia_meta.get("valuation_methodology"),
        "methodology_display": mdia_meta.get("valuation_methodology"),
        "proxy_note": mdia_meta.get("proxy_note"),
        "time_alignment": {
            **time_alignment,
            "snapshot_utc": _utcnow(),
            "aligned_with_suite_metrics": time_alignment.get(
                "aligns_with_suite_metrics",
                ["realized_cap", "mvrv", "hodl_waves"],
            ),
        },
        "chain_coverage": chain_info,
        "chain_coverage_explicit": True,
        "hodl_waves": hodl,
        "regime": regime,
        "sla_met": elapsed_ms <= _SLA_MS,
        "latency_ms": elapsed_ms,
        "not_a_prediction": True,
        "disclaimer": "MDIA proxy unless Glassnode/Santiment UTXO data configured.",
        "timestamp": _utcnow(),
    }


async def compute_realized_cap(asset: str = "BTC") -> dict[str, Any]:
    """Realized Cap Model — true network value (merged #750, not standalone)."""
    t0 = time.perf_counter()
    seed = _load_seed()
    methodology = seed.get("methodology") or {}
    supply_data = (seed.get("supply_estimates") or {}).get(asset.upper(), {})
    thresholds = seed.get("alert_thresholds") or {}

    from bd_platform.onchain_advanced import compute_advanced_metrics

    sym = asset.upper().replace("/USDT", "")
    metrics = await compute_advanced_metrics(sym)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if metrics.get("error"):
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": metrics["error"],
            "sla_met": elapsed_ms <= _SLA_MS,
            "latency_ms": elapsed_ms,
            "timestamp": _utcnow(),
        }

    price = float(metrics.get("price") or 0)
    supply = int(supply_data.get("circulating") or {"BTC": 19_800_000, "ETH": 120_000_000}.get(sym, 100_000_000))
    mvrv_ratio = float(metrics.get("mvrv", {}).get("ratio") or 1)
    mvrv_z = float(metrics.get("mvrv", {}).get("z_score") or 0)
    realized_price = price / mvrv_ratio if mvrv_ratio > 0 else price
    realized_cap = realized_price * supply
    market_cap = price * supply

    alerts = _build_alerts(sym, mvrv_z, mvrv_ratio, thresholds)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "model": "realized_cap",
        "competitor_reference": methodology.get("competitor_reference", "Glassnode Realized Cap"),
        "spot_price": round(price, 2),
        "realized_price": round(realized_price, 2),
        "realized_cap_usd": round(realized_cap, 0),
        "market_cap_usd": round(market_cap, 0),
        "circulating_supply": supply,
        "mvrv_ratio": round(mvrv_ratio, 3),
        "mvrv_z_score": round(mvrv_z, 3),
        "true_network_value_display": (
            f"Realized Cap: {_format_usd(realized_cap)} | "
            f"Realized Price: ${realized_price:,.0f} | "
            f"Market Cap: {_format_usd(market_cap)}"
        ),
        "methodology_display": (
            f"Methodology {methodology.get('version', 'v1.0')}: "
            f"{methodology.get('description', '')}"
        ),
        "source_line": f"Source: {', '.join(methodology.get('data_sources', ['Binance klines']))} | Supply: {supply_data.get('source', 'estimate')}",
        "alerts": alerts,
        "alert_count": len(alerts),
        "sla_met": elapsed_ms <= _SLA_MS,
        "latency_ms": elapsed_ms,
        "accuracy_target_pct": _ACCURACY_TARGET_PCT,
        "uptime_target_pct": _UPTIME_TARGET_PCT,
        "not_a_prediction": True,
        "disclaimer": "On-chain proxies unless Glassnode/Santiment API configured.",
        "timestamp": _utcnow(),
    }


async def get_onchain_metrics_suite(asset: str = "BTC") -> dict[str, Any]:
    """Full On-Chain Metrics Suite — realized cap + MVRV + NUPL + SOPR + alerts."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")

    from bd_platform.onchain_advanced import compute_advanced_metrics
    from bd_platform.mvrv_realignment import compute_mvrv_realignment

    realized = await compute_realized_cap(sym)
    mdia = await compute_mdia(sym)
    advanced = await compute_advanced_metrics(sym)
    realignment = await compute_mvrv_realignment(sym)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    all_alerts = list(realized.get("alerts") or [])
    all_alerts.extend(realignment.get("alerts") or [])

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "suite": "on_chain_intelligence",
        "sprint": 2,
        "asset": sym,
        "realized_cap": realized,
        "mdia": mdia,
        "mvrv": advanced.get("mvrv"),
        "nupl_proxy": advanced.get("nupl_proxy"),
        "sopr_proxy": advanced.get("sopr_proxy"),
        "puell_proxy": advanced.get("puell_proxy"),
        "hodl_waves": advanced.get("hodl_waves"),
        "mvrv_realignment": {
            "signal": realignment.get("realignment_signal"),
            "regime": realignment.get("regime"),
            "z_score": realignment.get("z_score"),
        },
        "alerts": all_alerts,
        "alert_count": len(all_alerts),
        "sla_met": elapsed_ms <= _SLA_MS,
        "latency_ms": elapsed_ms,
        "accuracy_target_pct": _ACCURACY_TARGET_PCT,
        "uptime_target_pct": _UPTIME_TARGET_PCT,
        "integrated_metrics": [
            "realized_cap", "mdia", "mvrv", "nupl", "sopr", "puell", "hodl_waves",
        ],
        "timestamp": _utcnow(),
    }


def get_methodology() -> dict[str, Any]:
    seed = _load_seed()
    methodology = seed.get("methodology") or {}
    mdia_methodology = seed.get("mdia_methodology") or {}
    return {
        "ok": True,
        "feature_ids": _FEATURE_IDS,
        "merged_into": _MERGED_INTO,
        "methodology": methodology,
        "mdia_methodology": mdia_methodology,
        "competitor_reference": methodology.get("competitor_reference"),
        "accuracy_target_pct": _ACCURACY_TARGET_PCT,
        "display": (
            f"{methodology.get('competitor_reference')}: "
            f"{methodology.get('description')}"
        ),
        "timestamp": _utcnow(),
    }


def onchain_metrics_suite_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": _FEATURE_IDS,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "On-Chain Metrics Suite",
        "sprint": 2,
        "realized_cap_model": True,
        "mdia_model": True,
        "competitor_reference": "Glassnode Realized Cap / MDIA",
        "valuation_methodology_documented": True,
        "time_alignment_documented": True,
        "chain_coverage_explicit": True,
        "sla_response_ms": _SLA_MS,
        "accuracy_target_pct": _ACCURACY_TARGET_PCT,
        "uptime_target_pct": _UPTIME_TARGET_PCT,
        "methodology_version": (seed.get("methodology") or {}).get("version"),
        "integrated_metrics": [
            "realized_cap", "realized_price", "mdia", "mvrv", "nupl", "sopr", "puell", "hodl_waves",
        ],
        "related_modules": ["onchain_advanced", "mvrv_realignment"],
        "timestamp": _utcnow(),
    }
