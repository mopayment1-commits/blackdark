"""
ETF Intelligence Module — Features #210 + #240 merged (Sprint 2).

Spot ETF market data (#210) + flow intelligence (#240) in one macro context layer.
Analysis only — NOT buy/sell recommendations.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

logger = logging.getLogger("BLACKDARK.ETFIntelligence")

_FEATURE_IDS = (210, 240)
_MERGED_INTO = "ETF Intelligence Module"
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/etf_intelligence_seed.json")
_EST = ZoneInfo("America/New_York")

_DISCLAIMER_TEXT = (
    "ETF flow data based on issuer disclosures. Correlation with crypto prices is historical, "
    "not predictive. Not investment advice."
)

RegimeLabel = Literal["Inflow-Driven", "Price-Driven", "Divergent"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "sources": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("etf intelligence seed load failed: %s", exc)
        return {"assets": {}, "sources": []}


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _format_usd(value: float, *, signed: bool = False) -> str:
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        text = f"${abs_val / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        text = f"${abs_val / 1_000_000:.0f}M"
    else:
        text = f"${abs_val:,.0f}"
    if signed and value < 0:
        return f"-{text}"
    if signed and value > 0:
        return f"+{text}"
    return text


def _valid_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in records if r.get("status") == "valid"]


def _missing_day_display(record: dict[str, Any]) -> str:
    reason = record.get("reason", "US Market Closed")
    last_valid = record.get("last_valid", "N/A")
    next_expected = record.get("next_expected", "N/A")
    return f"Holiday (US Market Closed): No data | Last Valid: {last_valid} | Next Expected: {next_expected}"


def _build_source_mapping(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for src in sources:
        mapped.append({
            "name": src.get("name"),
            "url": src.get("url"),
            "verified": bool(src.get("verified")),
            "last_verified": src.get("last_verified"),
            "data_type": src.get("data_type"),
            "source_display": src.get("source_display") or (
                f"Source: {src.get('name')} | URL: {src.get('url')} | "
                f"Verified: {'Yes' if src.get('verified') else 'No'} | "
                f"Last Verified: {src.get('last_verified', 'N/A')}"
            ),
        })
    return mapped


def _timezone_alignment_block(seed: dict[str, Any]) -> dict[str, Any]:
    tz = seed.get("timezone_alignment") or {}
    return {
        "etf_flow": tz.get("etf_flow", "Daily close 16:00 EST"),
        "crypto_market": tz.get("crypto_market", "24H UTC"),
        "alignment": tz.get("alignment", "EST close + 1H lag"),
        "alignment_display": tz.get(
            "alignment_display",
            "ETF Flow: Daily close 16:00 EST | Crypto Market: 24H UTC | Alignment: EST close + 1H lag",
        ),
        "etf_close_est": "16:00 EST",
        "crypto_reference": "24H UTC close aligned to ETF reporting window + 1H lag",
    }


def _aligned_crypto_price(
    flow_date: str,
    prices: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Align crypto price to ETF flow date — EST close + 1H lag uses same calendar date."""
    price_map = {p["date"]: p for p in prices}
    d = _parse_date(flow_date)
    # ETF reports T close; crypto aligned to T (post 16:00 EST + 1H = 17:00 EST ≈ same UTC day close)
    if flow_date in price_map:
        row = price_map[flow_date]
        est_close = datetime(d.year, d.month, d.day, 16, 0, tzinfo=_EST)
        aligned_at = (est_close + timedelta(hours=1)).astimezone(UTC)
        return {
            **row,
            "aligned_to_etf_date": flow_date,
            "alignment_method": "EST close + 1H lag",
            "etf_close_est": est_close.isoformat(),
            "crypto_aligned_utc": aligned_at.isoformat(),
        }
    return None


def _compute_rolling_totals(valid: list[dict[str, Any]], *, as_of: str | None = None) -> dict[str, Any]:
    methodology = "Sum of daily net flows (Creation - Redemption)"
    if not valid:
        return {
            "7d_net_flow_usd": 0,
            "30d_net_flow_usd": 0,
            "ytd_net_flow_usd": 0,
            "7d_display": "7D Net Flow: $0",
            "30d_display": "30D Net Flow: $0",
            "ytd_display": "YTD Net Flow: $0",
            "methodology": methodology,
            "rolling_display": f"7D Net Flow: $0 | 30D: $0 | YTD: $0 | Methodology: {methodology}",
            "valid_days_used": {"7d": 0, "30d": 0, "ytd": 0},
        }

    if as_of:
        cutoff = _parse_date(as_of)
        valid = [r for r in valid if _parse_date(r["date"]) <= cutoff]

    sorted_records = sorted(valid, key=lambda r: r["date"])
    latest = sorted_records[-1]
    latest_date = _parse_date(latest["date"])

    def _sum_window(days: int) -> tuple[float, int]:
        start = latest_date - timedelta(days=days - 1)
        window = [r for r in sorted_records if _parse_date(r["date"]) >= start]
        total = sum(float(r.get("net_flow_usd") or 0) for r in window)
        return total, len(window)

    def _sum_ytd() -> tuple[float, int]:
        year_start = date(latest_date.year, 1, 1)
        window = [r for r in sorted_records if _parse_date(r["date"]) >= year_start]
        total = sum(float(r.get("net_flow_usd") or 0) for r in window)
        return total, len(window)

    net_7d, days_7 = _sum_window(7)
    net_30d, days_30 = _sum_window(30)
    net_ytd, days_ytd = _sum_ytd()

    return {
        "7d_net_flow_usd": net_7d,
        "30d_net_flow_usd": net_30d,
        "ytd_net_flow_usd": net_ytd,
        "7d_display": f"7D Net Flow: {_format_usd(net_7d, signed=True)}",
        "30d_display": f"30D Net Flow: {_format_usd(net_30d, signed=True)}",
        "ytd_display": f"YTD Net Flow: {_format_usd(net_ytd, signed=True)}",
        "methodology": methodology,
        "rolling_display": (
            f"7D Net Flow: {_format_usd(net_7d, signed=True)} | "
            f"30D: {_format_usd(net_30d, signed=True)} | "
            f"YTD: {_format_usd(net_ytd, signed=True)} | "
            f"Methodology: {methodology}"
        ),
        "valid_days_used": {"7d": days_7, "30d": days_30, "ytd": days_ytd},
        "as_of": latest["date"],
    }


def _price_change_pct(prices: list[dict[str, Any]], days: int) -> float:
    if len(prices) < 2:
        return 0.0
    sorted_prices = sorted(prices, key=lambda p: p["date"])
    if len(sorted_prices) < days:
        window = sorted_prices
    else:
        window = sorted_prices[-days:]
    start = float(window[0].get("close_usd") or 0)
    end = float(window[-1].get("close_usd") or 0)
    if start <= 0:
        return 0.0
    return round((end - start) / start * 100, 2)


def _pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    try:
        return round(statistics.correlation(xs, ys), 3)
    except statistics.StatisticsError:
        return None


def _build_flow_price_pairs(
    valid_flows: list[dict[str, Any]],
    prices: list[dict[str, Any]],
    *,
    window: int = 30,
) -> list[tuple[float, float]]:
    price_map = {p["date"]: float(p.get("close_usd") or 0) for p in prices}
    sorted_flows = sorted(valid_flows, key=lambda r: r["date"])[-window:]
    pairs: list[tuple[float, float]] = []
    for i in range(1, len(sorted_flows)):
        prev = sorted_flows[i - 1]
        curr = sorted_flows[i]
        prev_price = price_map.get(prev["date"])
        curr_price = price_map.get(curr["date"])
        if prev_price and curr_price and prev_price > 0:
            price_chg = (curr_price - prev_price) / prev_price * 100
            flow = float(curr.get("net_flow_usd") or 0)
            pairs.append((flow, price_chg))
    return pairs


def _classify_regime(
    net_flow_7d: float,
    price_change_7d: float,
    correlation_30d: float | None,
) -> RegimeLabel:
    if correlation_30d is None:
        correlation_30d = 0.0

    flow_sign = 1 if net_flow_7d > 0 else -1 if net_flow_7d < 0 else 0
    price_sign = 1 if price_change_7d > 0 else -1 if price_change_7d < 0 else 0

    if flow_sign != 0 and price_sign != 0 and flow_sign != price_sign:
        return "Divergent"
    if abs(correlation_30d) < 0.15:
        return "Divergent"
    if net_flow_7d > 0 and price_change_7d > 0 and correlation_30d >= 0.25:
        return "Inflow-Driven"
    if net_flow_7d < 0 and price_change_7d < 0 and correlation_30d >= 0.25:
        return "Inflow-Driven"
    return "Price-Driven"


def _triangle_interpretation(
    aum_usd: float,
    daily_flow_usd: float,
    price_change_pct: float,
) -> str:
    aum_disp = _format_usd(aum_usd)
    flow_disp = _format_usd(daily_flow_usd, signed=True)
    price_disp = f"{price_change_pct:+.2f}%"

    if daily_flow_usd > 0 and price_change_pct < 0:
        interp = "Inflow absorbed by price drop = distribution pressure"
    elif daily_flow_usd > 0 and price_change_pct > 0:
        interp = "Inflow coinciding with price rise = demand-supported context"
    elif daily_flow_usd < 0 and price_change_pct > 0:
        interp = "Outflow amid price rise = profit-taking context"
    elif daily_flow_usd < 0 and price_change_pct < 0:
        interp = "Outflow with price decline = risk-off alignment"
    else:
        interp = "Neutral flow-price alignment"

    return (
        f"AUM: {aum_disp} | Daily Flow: {flow_disp} | Price Change: {price_disp} | "
        f"Interpretation: {interp}"
    )


def _largest_inflow_context(valid: list[dict[str, Any]], window: int = 30) -> str | None:
    if not valid:
        return None
    sorted_records = sorted(valid, key=lambda r: r["date"])[-window:]
    if not sorted_records:
        return None
    latest = sorted_records[-1]
    latest_flow = float(latest.get("net_flow_usd") or 0)
    if latest_flow <= 0:
        return None
    max_flow = max(float(r.get("net_flow_usd") or 0) for r in sorted_records)
    if latest_flow >= max_flow:
        return f"Inflow: {_format_usd(latest_flow, signed=True)} | Context: Largest in {window} days"
    return f"Inflow: {_format_usd(latest_flow, signed=True)} | Context: Below {window}D peak"


def _process_missing_days(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("status") == "valid":
            processed.append({
                **rec,
                "missing": False,
                "net_flow_display": _format_usd(float(rec.get("net_flow_usd") or 0), signed=True),
            })
        else:
            processed.append({
                "date": rec.get("date"),
                "status": rec.get("status", "missing"),
                "missing": True,
                "interpolated": False,
                "reason": rec.get("reason", "US Market Closed"),
                "missing_display": _missing_day_display(rec),
                "last_valid": rec.get("last_valid"),
                "next_expected": rec.get("next_expected"),
            })
    return processed


def build_etf_flow_series(asset: str = "BTC") -> dict[str, Any]:
    """Normalized daily ETF flows with missing-day handling."""
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)
    if not asset_data:
        return {"ok": False, "feature_ids": list(_FEATURE_IDS), "error": "asset_not_configured", "asset": sym}

    records = _process_missing_days(asset_data.get("daily_records") or [])
    valid = _valid_records(asset_data.get("daily_records") or [])
    rolling = _compute_rolling_totals(valid)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "asset": sym,
        "spot_etfs": asset_data.get("spot_etfs", []),
        "daily_flows": records,
        "valid_day_count": len(valid),
        "missing_day_count": len(records) - len(valid),
        "missing_day_policy": seed.get("missing_day_policy", "No interpolation"),
        "rolling_totals": rolling,
        "sources": _build_source_mapping(seed.get("sources") or []),
        "timezone_alignment": _timezone_alignment_block(seed),
        "not_a_recommendation": True,
        "timestamp": _utcnow(),
    }


def build_etf_market_context(asset: str = "BTC") -> dict[str, Any]:
    """Divergence/correlation engine — flow vs price regime."""
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)
    if not asset_data:
        return {"ok": False, "feature_ids": list(_FEATURE_IDS), "error": "asset_not_configured", "asset": sym}

    valid = _valid_records(asset_data.get("daily_records") or [])
    prices = asset_data.get("crypto_prices") or []
    rolling = _compute_rolling_totals(valid)

    price_latest = sorted(prices, key=lambda p: p["date"])[-1] if prices else {}
    price_usd = float(price_latest.get("close_usd") or 0)

    pairs = _build_flow_price_pairs(valid, prices, window=30)
    flows = [p[0] for p in pairs]
    chgs = [p[1] for p in pairs]
    corr = _pearson_correlation(flows, chgs)

    price_chg_7d = _price_change_pct(prices, 7)
    price_chg_30d = _price_change_pct(prices, 30)
    regime = _classify_regime(rolling["7d_net_flow_usd"], price_chg_7d, corr)

    corr_pct = round((corr or 0) * 100, 1)
    context_display = (
        f"BTC Price: ${_format_usd(price_usd).lstrip('$')} | "
        f"Flow-BTC Correlation (30D): {corr_pct}% | Regime: {regime}"
    )

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "asset": sym,
        "btc_price_usd": price_usd,
        "price_change_7d_pct": price_chg_7d,
        "price_change_30d_pct": price_chg_30d,
        "flow_btc_correlation_30d": corr,
        "flow_btc_correlation_30d_pct": corr_pct,
        "regime": regime,
        "regime_labels": ["Inflow-Driven", "Price-Driven", "Divergent"],
        "context_display": context_display,
        "rolling_totals": rolling,
        "pair_count": len(pairs),
        "divergence_engine": "Rule-based correlation + sign alignment",
        "not_a_recommendation": True,
        "not_buy_signal": True,
        "timestamp": _utcnow(),
    }


def build_etf_intelligence_dashboard(asset: str = "BTC") -> dict[str, Any]:
    """Unified ETF Intelligence dashboard — flows + AUM + price triangle + market context."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)

    disclaimer = {
        "text": _DISCLAIMER_TEXT,
        "collapsible": False,
        "hideable": False,
        "version": seed.get("module_version", "1.0"),
    }

    if not asset_data:
        return {
            "ok": False,
            "feature_ids": list(_FEATURE_IDS),
            "error": "asset_not_configured",
            "asset": sym,
            "disclaimer_top": disclaimer,
            "disclaimer_bottom": disclaimer,
        }

    valid = _valid_records(asset_data.get("daily_records") or [])
    prices = asset_data.get("crypto_prices") or []
    latest_flow = sorted(valid, key=lambda r: r["date"])[-1] if valid else {}
    latest_price = sorted(prices, key=lambda p: p["date"])[-1] if prices else {}

    rolling = _compute_rolling_totals(valid)
    market_ctx = build_etf_market_context(sym)
    flow_series = build_etf_flow_series(sym)

    aum_usd = float(latest_flow.get("aum_usd") or 0)
    daily_flow = float(latest_flow.get("net_flow_usd") or 0)
    price_chg_1d = 0.0
    if len(prices) >= 2:
        sorted_p = sorted(prices, key=lambda p: p["date"])
        prev_p = float(sorted_p[-2].get("close_usd") or 0)
        curr_p = float(sorted_p[-1].get("close_usd") or 0)
        if prev_p > 0:
            price_chg_1d = round((curr_p - prev_p) / prev_p * 100, 2)

    triangle = {
        "aum_usd": aum_usd,
        "aum_display": _format_usd(aum_usd),
        "daily_flow_usd": daily_flow,
        "daily_flow_display": _format_usd(daily_flow, signed=True),
        "price_change_1d_pct": price_chg_1d,
        "price_change_display": f"{price_chg_1d:+.2f}%",
        "triangle_display": _triangle_interpretation(aum_usd, daily_flow, price_chg_1d),
        "as_of": latest_flow.get("date"),
        "price_as_of": latest_price.get("date"),
    }

    inflow_context = _largest_inflow_context(valid)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "feature_label": seed.get("feature_label", "ETF Intelligence Module"),
        "standalone": _STANDALONE,
        "merged_features": seed.get("merged_features", ["#210 ETF Data", "#240 ETF Flow Intelligence"]),
        "surface": "etf_intelligence_dashboard",
        "asset": sym,
        "module_version": seed.get("module_version", "1.0"),
        "module_version_display": (
            f"ETF Intelligence v{seed.get('module_version', '1.0')} | "
            f"Methodology: Rule-Based | Last Updated: {seed.get('last_updated', 'N/A')}"
        ),
        "spot_etfs": asset_data.get("spot_etfs", []),
        "sources": _build_source_mapping(seed.get("sources") or []),
        "timezone_alignment": _timezone_alignment_block(seed),
        "rolling_totals": rolling,
        "flow_series": {
            "daily_flows": flow_series.get("daily_flows", [])[-14:],
            "missing_day_policy": flow_series.get("missing_day_policy"),
            "valid_day_count": flow_series.get("valid_day_count"),
            "missing_day_count": flow_series.get("missing_day_count"),
        },
        "market_context": market_ctx,
        "aum_flow_price_triangle": triangle,
        "inflow_context": inflow_context,
        "latest_daily_flow": {
            "date": latest_flow.get("date"),
            "creation_usd": latest_flow.get("creation_usd"),
            "redemption_usd": latest_flow.get("redemption_usd"),
            "net_flow_usd": daily_flow,
            "net_flow_display": _format_usd(daily_flow, signed=True),
            "aum_usd": aum_usd,
            "aligned_crypto": _aligned_crypto_price(latest_flow.get("date", ""), prices),
        },
        "macro_context_only": True,
        "not_a_recommendation": True,
        "not_buy_sell_signal": True,
        "allowed_language": ["Context", "Analysis", "Inflow", "Outflow", "Regime", "Correlation"],
        "pro_tier": seed.get("tier", "pro") == "pro",
        "disclaimer_top": disclaimer,
        "disclaimer": disclaimer,
        "disclaimer_bottom": disclaimer,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def etf_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "feature_label": seed.get("feature_label", "ETF Intelligence Module"),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "merged_features": seed.get("merged_features", ["#210 ETF Data", "#240 ETF Flow Intelligence"]),
        "sprint": _SPRINT,
        "module_version": seed.get("module_version", "1.0"),
        "tier": seed.get("tier", "pro"),
        "sources": _build_source_mapping(seed.get("sources") or []),
        "timezone_alignment": _timezone_alignment_block(seed),
        "rolling_methodology": seed.get("rolling_methodology"),
        "missing_day_policy": seed.get("missing_day_policy"),
        "integrated_surfaces": ["Market Radar"],
        "assets_configured": list((seed.get("assets") or {}).keys()),
        "acceptance_criteria": {
            "official_source_mapping": True,
            "timezone_alignment": True,
            "missing_day_handling": True,
            "rolling_totals_methodology": True,
            "market_context_divergence": True,
            "aum_flow_price_triangle": True,
            "disclaimer_non_hideable": True,
            "not_recommendation": True,
            "merged_210_240": True,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
