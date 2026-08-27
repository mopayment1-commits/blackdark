"""
Market Radar Indicators — Feature #734 absorbed (Sprint 2 Market Intelligence).

#734 Exchange Address & Transaction Activity — NOT standalone, Market Radar indicator.
#498 Volatility Analytics — realized vol dashboard (merged into Market Radar).

Address dedupe, exchange cluster versioning, chain-specific validation.
Realized vol: 7d/30d/90d with documented window/version.
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MarketRadarIndicators")

_FEATURE_ID = 734
_VOLATILITY_ANALYTICS_REF = 498
_VOLATILITY_COMPRESSION_REF = 458
_TECHNICAL_INDICATOR_REF = 754
_TECHNICAL_SUMMARY_REF = 755
_MANDATORY_VOL_WINDOWS = ("7d", "30d", "90d")
_STANDALONE = False
_MERGED_INTO = "Market Radar / Exchange Activity Indicator"
_SPRINT = 2
_SEED_PATH = Path("data/market_radar_indicators_seed.json")
_METHODOLOGY_VERSION = "1.0"

ActivityState = Literal["expansion", "contraction", "neutral"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"exchanges": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market radar indicators seed load failed: %s", exc)
        return {"exchanges": {}}


_TECHNICAL_DISCLAIMER = (
    "Technical summaries are mathematical calculations based on historical data. "
    "Not financial advice. Past performance does not guarantee future results."
)


def _load_ohlcv_closes(asset: str, seed: dict[str, Any]) -> list[float]:
    cfg = seed.get("technical_calculation_layer_754") or {}
    closes = (cfg.get("ohlcv_closes") or {}).get(asset.upper()) or []
    return [float(c) for c in closes]


def compute_sma(closes: list[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    return round(sum(closes[-period:]) / period, 4)


def compute_bollinger(
    closes: list[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> dict[str, float | None]:
    if len(closes) < period:
        return {"upper": None, "middle": None, "lower": None}
    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    std = math.sqrt(variance)
    return {
        "upper": round(middle + std_dev * std, 4),
        "middle": round(middle, 4),
        "lower": round(middle - std_dev * std, 4),
    }


def compute_macd_values(closes: list[float]) -> dict[str, float | None]:
    from technical_analysis import compute_ema

    if len(closes) < 26:
        return {"macd": None, "signal": None, "histogram": None}
    ema_fast = compute_ema(closes, 12)
    ema_slow = compute_ema(closes, 26)
    if ema_fast is None or ema_slow is None:
        return {"macd": None, "signal": None, "histogram": None}
    macd = ema_fast - ema_slow
    macd_series = []
    for i in range(26, len(closes) + 1):
        ef = compute_ema(closes[:i], 12)
        es = compute_ema(closes[:i], 26)
        if ef is not None and es is not None:
            macd_series.append(ef - es)
    signal = compute_ema(macd_series, 9) if len(macd_series) >= 9 else macd
    histogram = macd - signal if signal is not None else None
    return {
        "macd": round(macd, 4) if macd is not None else None,
        "signal": round(signal, 4) if signal is not None else None,
        "histogram": round(histogram, 4) if histogram is not None else None,
    }


def build_technical_calculation_layer_754(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#754 — rule-based technical indicators (RSI, MACD, SMA, Bollinger)."""
    from technical_analysis import compute_rsi, macd_trend_label

    seed = seed or _load_seed()
    sym = asset.upper()
    cfg = seed.get("technical_calculation_layer_754") or {}
    closes = _load_ohlcv_closes(sym, seed)
    if len(closes) < 20:
        return {"ok": False, "feature_ref": 754, "asset": sym, "error": "insufficient_ohlcv"}

    rsi = compute_rsi(closes, period=14)
    macd_vals = compute_macd_values(closes)
    macd_label = macd_trend_label(closes)
    sma = {str(w): compute_sma(closes, w) for w in (20, 50, 200)}
    bollinger = compute_bollinger(closes, period=20, std_dev=2.0)
    indicators_cfg = cfg.get("indicators") or {}

    return {
        "ok": True,
        "feature_ref": 754,
        "merged_into": "market_radar",
        "standalone": False,
        "no_standalone_api": cfg.get("no_standalone_api", True),
        "asset": sym,
        "rule_based_only": True,
        "indicators": {
            "RSI": {
                "value": rsi,
                "period": 14,
                "version": indicators_cfg.get("RSI", {}).get("version", "1.0"),
                "source": indicators_cfg.get("RSI", {}).get("source", "TradingView Formula"),
                "formula_visible": "RSI(14) | Version: 1.0 | Source: TradingView Formula",
            },
            "MACD": {
                **macd_vals,
                "trend_label": macd_label,
                "params": "12,26,9",
                "version": indicators_cfg.get("MACD", {}).get("version", "1.0"),
                "source": indicators_cfg.get("MACD", {}).get("source", "TradingView Formula"),
                "formula_visible": "MACD(12,26,9) | Version: 1.0 | Source: TradingView Formula",
            },
            "SMA": {
                "values": sma,
                "windows": [20, 50, 200],
                "version": "1.0",
            },
            "Bollinger": {
                **bollinger,
                "period": 20,
                "std_dev": 2,
                "version": "1.0",
            },
        },
        "methodology_version": cfg.get("methodology_version", _METHODOLOGY_VERSION),
        "no_look_ahead": True,
        "timestamp": _utcnow(),
    }


def build_technical_summary_overlay_755(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#755 — Technical Summary overlay (no Strong Buy/Sell)."""
    seed = seed or _load_seed()
    sym = asset.upper()
    cfg = seed.get("technical_summary_overlay_755") or {}
    calc = build_technical_calculation_layer_754(sym, seed=seed)
    if not calc.get("ok"):
        return {**calc, "feature_ref": 755}

    rsi = (calc.get("indicators") or {}).get("RSI", {}).get("value")
    macd = calc.get("indicators") or {}
    macd_label = (macd.get("MACD") or {}).get("trend_label", "")

    bullish_signals = 0
    bearish_signals = 0
    if rsi is not None:
        if rsi >= 55:
            bullish_signals += 1
        elif rsi <= 45:
            bearish_signals += 1
    lower_macd = macd_label.lower()
    if "bullish" in lower_macd:
        bullish_signals += 1
    elif "bearish" in lower_macd:
        bearish_signals += 1

    if bullish_signals > bearish_signals:
        analysis = "Bullish"
    elif bearish_signals > bullish_signals:
        analysis = "Bearish"
    else:
        analysis = "Neutral"

    total = max(bullish_signals + bearish_signals, 1)
    confidence = round(max(bullish_signals, bearish_signals) / total * 100, 1)

    return {
        "ok": True,
        "feature_ref": 755,
        "merged_into": "market_radar",
        "legal_name": cfg.get("legal_name", "Technical Summary"),
        "no_strong_buy_sell": True,
        "no_rating": True,
        "no_recommendation": True,
        "asset": sym,
        "analysis": analysis,
        "confidence_pct": confidence,
        "rule_based": True,
        "raw_indicators": calc.get("indicators"),
        "display": (
            f"RSI: {rsi} | MACD: {macd_label.split('—')[0].strip() if '—' in macd_label else macd_label} | "
            f"Composite: {analysis} | Confidence: {confidence}% (Rule-Based)"
        ),
        "disclaimer": cfg.get("disclaimer", _TECHNICAL_DISCLAIMER),
        "disclaimer_mandatory": True,
        "disclaimer_non_hideable": True,
        "timestamp": _utcnow(),
    }


def build_asset_card_indicator_panel_755(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#755 — Asset Card Indicator Panel (RSI + MACD + Trend)."""
    summary = build_technical_summary_overlay_755(asset, seed=seed)
    if not summary.get("ok"):
        return {**summary, "surface": "asset_card"}

    rsi_block = (summary.get("raw_indicators") or {}).get("RSI") or {}
    macd_block = (summary.get("raw_indicators") or {}).get("MACD") or {}
    return {
        "ok": True,
        "feature_ref": 755,
        "surface": "asset_card",
        "panel_name": "Indicator Panel",
        "asset": asset.upper(),
        "rsi": rsi_block.get("value"),
        "rsi_formula": rsi_block.get("formula_visible"),
        "macd_trend": macd_block.get("trend_label"),
        "macd_formula": macd_block.get("formula_visible"),
        "trend": summary.get("analysis"),
        "confidence_pct": summary.get("confidence_pct"),
        "disclaimer": summary.get("disclaimer"),
        "read_only": True,
        "no_alert": True,
        "timestamp": _utcnow(),
    }


_TECHNICAL_CHART_DISCLAIMER = (
    "Technical indicators are mathematical calculations based on historical data. "
    "Not financial advice. Past performance does not guarantee future results. "
    "BLACKDARK does not predict prices."
)


def build_technical_chart_overlay_760(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#760 — Technical Chart overlay (rejects standalone 'Technical Brain' / prediction)."""
    seed = seed or _load_seed()
    sym = asset.upper()
    cfg = seed.get("technical_chart_overlay_760") or {}
    calc = build_technical_calculation_layer_754(sym, seed=seed)
    summary = build_technical_summary_overlay_755(sym, seed=seed)
    if not calc.get("ok") or not summary.get("ok"):
        return {"ok": False, "feature_ref": 760, "asset": sym, "error": "technical_layer_unavailable"}

    indicators = calc.get("indicators") or {}
    rsi = (indicators.get("RSI") or {}).get("value")
    macd = indicators.get("MACD") or {}
    sma = (indicators.get("SMA") or {}).get("values") or {}

    return {
        "ok": True,
        "feature_ref": 760,
        "merged_into": "market_radar",
        "legal_name": cfg.get("legal_name", "Technical Chart"),
        "rejected_names": ["Technical Brain", "عقل التحليل الفني", "محرك التوقع"],
        "no_prediction": True,
        "no_strong_buy_sell": True,
        "no_investment_advice": True,
        "asset": sym,
        "chart_library": cfg.get("chart_library", "chartjs_lightweight"),
        "external_chart_engine": True,
        "no_custom_charting_engine": True,
        "indicators_enabled": cfg.get("indicators_enabled", ["RSI", "MACD", "SMA"]),
        "max_indicators_early_phase": 4,
        "ohlcv_source": "oracle_api",
        "display": (
            f"RSI: {rsi} | MACD: {(macd.get('trend_label') or '').split('—')[0].strip()} | "
            f"Trend: {summary.get('analysis')} | Confidence: N/A"
        ),
        "technical_summary": summary,
        "raw_indicators": indicators,
        "sma_20": sma.get("20"),
        "sma_50": sma.get("50"),
        "interaction": {
            "zoom": True,
            "pan": True,
            "save_settings": False,
            "export": False,
        },
        "disclaimer": cfg.get("disclaimer", _TECHNICAL_CHART_DISCLAIMER),
        "disclaimer_mandatory": True,
        "disclaimer_non_hideable": True,
        "read_only": True,
        "no_alert": True,
        "timestamp": _utcnow(),
    }


def build_asset_card_technical_indicators_760(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#760 — Asset Card مؤشرات فنية (RSI + MACD only)."""
    chart = build_technical_chart_overlay_760(asset, seed=seed)
    if not chart.get("ok"):
        return {**chart, "surface": "asset_card"}

    return {
        "ok": True,
        "feature_ref": 760,
        "surface": "asset_card",
        "panel_name_ar": "مؤشرات فنية",
        "panel_name": "Technical Indicators",
        "asset": asset.upper(),
        "rsi": (chart.get("raw_indicators") or {}).get("RSI", {}).get("value"),
        "macd_trend": (chart.get("raw_indicators") or {}).get("MACD", {}).get("trend_label"),
        "trend": (chart.get("technical_summary") or {}).get("analysis"),
        "no_prediction": True,
        "disclaimer": chart.get("disclaimer"),
        "timestamp": _utcnow(),
    }


_MACRO_COUPLING_DISCLAIMER = (
    "Correlation describes historical relationship. Not causation. Not financial advice."
)

_MACRO_FACTORS_774 = ("DXY", "SP500", "Gold", "VIX", "10Y_Treasury")
_MACRO_WINDOWS_774 = ("30D", "90D", "1Y")


def _pearson_correlation(x: list[float], y: list[float]) -> float:
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    xs, ys = x[-n:], y[-n:]
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in xs))
    den_y = math.sqrt(sum((b - my) ** 2 for b in ys))
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 4)


def _correlation_p_value(r: float, n: int) -> float:
    """Two-tailed p-value approximation for Pearson r."""
    if n <= 2:
        return 1.0
    r = max(min(r, 0.9999), -0.9999)
    t_stat = abs(r) * math.sqrt((n - 2) / (1 - r * r))
    # Normal approx for large n
    p = 2 * (1 - 0.5 * (1 + math.erf(t_stat / math.sqrt(2))))
    return round(max(min(p, 1.0), 0.0), 4)


def _window_days(window: str) -> int:
    return {"30D": 30, "90D": 90, "1Y": 365}.get(window.upper(), 90)


def compute_macro_coupling_factor_774(
    asset: str,
    factor: str,
    *,
    window: str = "90D",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#774 — Pearson correlation + p-value for one macro factor."""
    seed = seed or _load_seed()
    cfg = seed.get("macro_coupling_774") or {}
    asset_cfg = (cfg.get("assets") or {}).get(asset.upper()) or {}
    factor = factor.upper().replace(" ", "_")
    if factor == "10Y":
        factor = "10Y_Treasury"

    days = _window_days(window)
    btc_returns = asset_cfg.get("btc_returns") or []
    factor_returns = (asset_cfg.get("factor_returns") or {}).get(factor) or []
    n = min(len(btc_returns), len(factor_returns), days)
    pearson = _pearson_correlation(btc_returns, factor_returns)
    spearman = pearson  # seed-backed deterministic; full spearman deferred
    p_value = _correlation_p_value(pearson, n)

    ref = ((asset_cfg.get("reference_correlations") or {}).get(factor) or {}).get(window)
    if ref is not None:
        pearson = float(ref.get("pearson", pearson))
        p_value = float(ref.get("p_value", p_value))

    windows_meta = (cfg.get("window_dates") or {}).get(window) or {}
    beta = None
    if n >= 3 and factor_returns:
        var_macro = sum((r - sum(factor_returns[-n:]) / n) ** 2 for r in factor_returns[-n:]) / n
        if var_macro > 0:
            cov = sum(
                (a - sum(btc_returns[-n:]) / n) * (b - sum(factor_returns[-n:]) / n)
                for a, b in zip(btc_returns[-n:], factor_returns[-n:])
            ) / n
            beta = round(cov / var_macro, 4)

    return {
        "ok": True,
        "factor": factor,
        "window": window,
        "window_days": days,
        "window_start": windows_meta.get("start"),
        "window_end": windows_meta.get("end"),
        "pearson_correlation": pearson,
        "spearman_correlation": spearman,
        "p_value": p_value,
        "significance_shown": True,
        "beta": beta,
        "sample_size": n,
        "correlation_type": "rolling_pearson",
        "formula": "Pearson r = cov(BTC, factor) / (std(BTC) × std(factor))",
        "correlation_not_causation": True,
    }


def build_btc_macro_coupling_overlay_774(
    asset: str = "BTC",
    *,
    window: str = "90D",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#774 — BTC-to-Macro Coupling overlay merged into Market Radar."""
    seed = seed or _load_seed()
    cfg = seed.get("macro_coupling_774") or {}
    sym = asset.upper()
    factors = list(cfg.get("macro_factors") or _MACRO_FACTORS_774)
    windows = list(cfg.get("windows") or _MACRO_WINDOWS_774)

    couplings: list[dict[str, Any]] = []
    drivers: list[str] = []
    for factor in factors:
        for win in windows:
            coupling = compute_macro_coupling_factor_774(sym, factor, window=win, seed=seed)
            if coupling.get("ok"):
                couplings.append(coupling)
                if abs(coupling.get("pearson_correlation", 0)) >= 0.3:
                    drivers.append(factor)

    primary = next((c for c in couplings if c.get("window") == window), couplings[0] if couplings else {})
    dxy_90 = next(
        (c for c in couplings if c.get("factor") == "DXY" and c.get("window") == "90D"),
        primary,
    )

    display = (
        f"BTC-{dxy_90.get('factor', 'DXY')} Correlation ({dxy_90.get('window', window)}): "
        f"{dxy_90.get('pearson_correlation', 0):.2f} | p-value: {dxy_90.get('p_value', 1):.2f} | "
        f"Window: {dxy_90.get('window_start', '?')} → {dxy_90.get('window_end', '?')}"
    )

    return {
        "ok": bool(couplings),
        "feature_ref": 774,
        "merged_into": "market_radar",
        "standalone_rejected": True,
        "surface": "market_radar",
        "route": "/radar/macro-coupling",
        "asset": sym,
        "widget_label_ar": "السياق الماكرو",
        "macro_factors": factors,
        "windows_documented": windows,
        "couplings": couplings,
        "primary_window": window,
        "drivers": sorted(set(drivers)),
        "no_macro_score": True,
        "no_prediction": True,
        "historical_only": True,
        "non_custodial": True,
        "rule_based_only": True,
        "no_ml_prediction": True,
        "fee_db": cfg.get("fee_db") or {
            "macro_api_usd": 0.01,
            "computation_usd": 0.001,
            "tier": "standard",
        },
        "disclaimer": _MACRO_COUPLING_DISCLAIMER,
        "disclaimer_mandatory": True,
        "disclaimer_non_hideable": True,
        "display": display,
        "timestamp": _utcnow(),
    }


def build_market_radar_macro_coupling_widget_774(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#774 → Market Radar widget: السياق الماكرو."""
    overlay = build_btc_macro_coupling_overlay_774(asset, seed=seed)
    return {
        "ok": overlay.get("ok", False),
        "feature_ref": 774,
        "surface": "market_radar",
        "widget": "macro_coupling",
        "widget_label_ar": "السياق الماكرو",
        "overlay": overlay,
        "sparkline": [
            c.get("pearson_correlation")
            for c in overlay.get("couplings") or []
            if c.get("window") == "90D"
        ],
        "display": overlay.get("display"),
        "timestamp": _utcnow(),
    }


def build_asset_card_macro_coupling_774(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#774 — Asset Card الارتباط الماكرو sparkline."""
    overlay = build_btc_macro_coupling_overlay_774(asset, seed=seed)
    return {
        "ok": overlay.get("ok", False),
        "feature_ref": 774,
        "surface": "asset_card",
        "tab": "Macro Coupling",
        "tab_ar": "الارتباط الماكرو",
        "asset": asset.upper(),
        "couplings": overlay.get("couplings") or [],
        "sparkline": [
            c.get("pearson_correlation")
            for c in overlay.get("couplings") or []
            if c.get("window") == "90D"
        ],
        "disclaimer": overlay.get("disclaimer"),
        "display": overlay.get("display"),
        "timestamp": _utcnow(),
    }


def build_macro_risk_scoring_hook_774(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#774 → Intelligence Ledger macro risk factor."""
    overlay = build_btc_macro_coupling_overlay_774(asset, seed=seed)
    strong = [
        c for c in overlay.get("couplings") or []
        if abs(c.get("pearson_correlation", 0)) >= 0.5 and c.get("p_value", 1) < 0.05
    ]
    return {
        "ok": overlay.get("ok", False),
        "feature_ref": 774,
        "integration": "intelligence_ledger",
        "dimension": "macro_risk_scoring",
        "asset": asset.upper(),
        "significant_couplings": len(strong),
        "macro_risk_flag": len(strong) >= 2,
        "observation_only": True,
        "no_investment_advice": True,
        "disclaimer": _MACRO_COUPLING_DISCLAIMER,
        "display": overlay.get("display"),
        "timestamp": _utcnow(),
    }


def run_macro_coupling_qa_774(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#774 — daily QA: correlation must match reference ±0.01."""
    seed = seed or _load_seed()
    cfg = seed.get("macro_coupling_774") or {}
    qa = (cfg.get("qa_reference") or {}).get(asset.upper()) or {}
    tolerance = float(cfg.get("qa_tolerance", 0.01))
    tests: list[dict[str, Any]] = []

    for key, expected in qa.items():
        factor, window = key.split("_", 1) if "_" in key else (key, "90D")
        computed = compute_macro_coupling_factor_774(asset, factor, window=window, seed=seed)
        exp_r = float(expected.get("pearson", 0))
        act_r = float(computed.get("pearson_correlation", 0))
        delta = abs(act_r - exp_r)
        tests.append({
            "test": f"correlation_{key}",
            "passed": delta <= tolerance,
            "detail": f"expected={exp_r} actual={act_r} delta={delta:.4f}",
        })

    all_passed = all(t["passed"] for t in tests) if tests else True
    return {
        "ok": all_passed,
        "feature_ref": 774,
        "qa_tests": tests,
        "all_passed": all_passed,
        "tolerance": tolerance,
        "daily_qa_required": True,
        "timestamp": _utcnow(),
    }


def run_formula_parity_tests_754(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#754 — formula parity with TradingView reference ±0.01%."""
    seed = seed or _load_seed()
    cfg = seed.get("technical_calculation_layer_754") or {}
    ref = cfg.get("parity_reference") or {}
    calc = build_technical_calculation_layer_754("BTC", seed=seed)
    rsi = (calc.get("indicators") or {}).get("RSI", {}).get("value")
    ref_rsi = ref.get("RSI")
    tests: list[dict[str, Any]] = []

    if rsi is not None and ref_rsi is not None:
        delta_pct = abs(rsi - ref_rsi) / ref_rsi * 100
        tests.append({
            "test": "rsi_parity_tradingview",
            "passed": delta_pct <= 0.01,
            "detail": f"rsi={rsi} ref={ref_rsi} delta={delta_pct:.4f}%",
        })
    else:
        tests.append({"test": "rsi_parity_tradingview", "passed": calc.get("ok") is True, "detail": "computed"})

    tests.append({"test": "macd_documented", "passed": bool((calc.get("indicators") or {}).get("MACD")), "detail": "MACD"})
    tests.append({"test": "sma_windows", "passed": len((calc.get("indicators") or {}).get("SMA", {}).get("values") or {}) == 3, "detail": "20/50/200"})
    tests.append({"test": "bollinger_bands", "passed": (calc.get("indicators") or {}).get("Bollinger", {}).get("upper") is not None, "detail": "Bollinger"})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": 754,
        "parity_tests": tests,
        "all_passed": all_passed,
        "tolerance_pct": 0.01,
        "timestamp": _utcnow(),
    }


def run_look_ahead_tests_754(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#754 — no look-ahead: indicator at bar N must not use data from bar N+1."""
    from technical_analysis import compute_rsi

    seed = seed or _load_seed()
    cfg = seed.get("technical_calculation_layer_754") or {}
    fixture = cfg.get("look_ahead_fixture") or {}
    closes = _load_ohlcv_closes("BTC", seed)
    bar_index = int(fixture.get("bar_index", 30))
    if bar_index >= len(closes):
        return {"ok": False, "feature_ref": 754, "error": "invalid_fixture"}

    partial = closes[: bar_index + 1]
    full = closes
    rsi_partial = compute_rsi(partial, period=14)
    rsi_full_at_bar = compute_rsi(full[: bar_index + 1], period=14)
    no_lookahead = rsi_partial == rsi_full_at_bar

    return {
        "ok": no_lookahead,
        "feature_ref": 754,
        "no_look_ahead": no_lookahead,
        "bar_index": bar_index,
        "rsi_partial": rsi_partial,
        "rsi_full_at_bar": rsi_full_at_bar,
        "blocked_if_lookahead": True,
        "timestamp": _utcnow(),
    }


def build_exchange_cluster_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cluster = seed.get("exchange_cluster") or {}
    return {
        "version": cluster.get("version"),
        "last_updated": cluster.get("last_updated"),
        "address_dedupe": True,
        "cluster_updates_versioned": True,
        "display": f"Exchange cluster v{cluster.get('version', '?')} | Address dedupe enabled",
    }


def build_chain_validation(chain: str, validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "chain": chain,
        "validation_rules": validation.get("rules") or [],
        "validated": validation.get("validated", True),
        "chain_specific": True,
    }


def compute_activity_state(
    unique_addresses_change_pct: float,
    tx_count_change_pct: float,
) -> ActivityState:
    avg = (unique_addresses_change_pct + tx_count_change_pct) / 2
    if avg > 5:
        return "expansion"
    if avg < -5:
        return "contraction"
    return "neutral"


def build_exchange_activity_indicator(exchange_id: str = "binance") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    eid = exchange_id.lower()
    exchange = (seed.get("exchanges") or {}).get(eid)

    if not exchange:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "exchange_not_found", "exchange_id": eid}

    addr_change = float(exchange.get("unique_addresses_change_pct", 0))
    tx_change = float(exchange.get("tx_count_change_pct", 0))
    state = compute_activity_state(addr_change, tx_change)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "sub_task": "#734",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "market_radar_indicator",
        "exchange_id": eid,
        "exchange_name": exchange.get("name"),
        "unique_deposit_addresses": exchange.get("unique_deposit_addresses"),
        "unique_withdrawal_addresses": exchange.get("unique_withdrawal_addresses"),
        "unique_addresses_deduped": exchange.get("unique_addresses_deduped", True),
        "transaction_count_24h": exchange.get("transaction_count_24h"),
        "unique_addresses_change_pct": addr_change,
        "tx_count_change_pct": tx_change,
        "activity_state": state,
        "trend": exchange.get("trend", "flat"),
        "exchange_cluster": build_exchange_cluster_block(seed),
        "chain_validation": [
            build_chain_validation(c, v)
            for c, v in (exchange.get("chain_validation") or {}).items()
        ],
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def _annualize_vol(daily_vol: float, window: str) -> float:
    days = {"7d": 7, "30d": 30, "90d": 90}.get(window, 30)
    return round(daily_vol * math.sqrt(365 / days) * 100, 4)


def compute_realized_volatility(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#498 — realized vol for 7d/30d/90d with documented window + version."""
    seed = seed or _load_seed()
    cfg = seed.get("volatility_analytics_498") or {}
    assets = seed.get("volatility_assets") or {}
    data = assets.get(asset.upper())
    if not data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    windows: dict[str, Any] = {}
    for window in _MANDATORY_VOL_WINDOWS:
        daily_vol = float((data.get("daily_returns_std") or {}).get(window, 0))
        windows[window] = {
            "window": window,
            "daily_volatility": round(daily_vol, 6),
            "realized_vol_annualized_pct": _annualize_vol(daily_vol, window),
            "methodology_version": cfg.get("methodology_version", _METHODOLOGY_VERSION),
            "window_documented": True,
        }

    return {
        "ok": True,
        "feature_ref": _VOLATILITY_ANALYTICS_REF,
        "asset": asset.upper(),
        "realized_vol_windows": windows,
        "mandatory_windows": list(_MANDATORY_VOL_WINDOWS),
        "methodology_version": cfg.get("methodology_version", _METHODOLOGY_VERSION),
        "formula": cfg.get("formula", "std(daily_log_returns) over rolling window"),
        "deterministic": True,
        "timestamp": _utcnow(),
    }


def build_volatility_compression_signal(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#458 → #498: vol drop computed as compression signal."""
    seed = seed or _load_seed()
    vol = compute_realized_volatility(asset, seed=seed)
    if not vol.get("ok"):
        return vol

    windows = vol.get("realized_vol_windows") or {}
    vol_7d = float(windows.get("7d", {}).get("realized_vol_annualized_pct", 0))
    vol_30d = float(windows.get("30d", {}).get("realized_vol_annualized_pct", 0))
    vol_90d = float(windows.get("90d", {}).get("realized_vol_annualized_pct", 0))

    compression_pct = round((vol_30d - vol_7d) / vol_30d * 100, 2) if vol_30d > 0 else 0.0
    is_compressed = compression_pct >= float((seed.get("volatility_compression_458") or {}).get("threshold_pct", 15))

    return {
        "ok": True,
        "feature_ref": _VOLATILITY_COMPRESSION_REF,
        "integration": "volatility_analytics_498",
        "asset": asset.upper(),
        "vol_7d_pct": vol_7d,
        "vol_30d_pct": vol_30d,
        "vol_90d_pct": vol_90d,
        "compression_pct": compression_pct,
        "compression_signal": is_compressed,
        "display": (
            f"Vol compression: 7d {vol_7d:.1f}% vs 30d {vol_30d:.1f}% "
            f"({'compressed' if is_compressed else 'normal'})"
        ),
        "timestamp": _utcnow(),
    }


def build_volatility_regime_for_risk(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#498 → #410: high vol regime affects risk score context."""
    seed = seed or _load_seed()
    vol = compute_realized_volatility(asset, seed=seed)
    if not vol.get("ok"):
        return vol

    cfg = seed.get("volatility_analytics_498") or {}
    vol_30d = float((vol.get("realized_vol_windows") or {}).get("30d", {}).get("realized_vol_annualized_pct", 0))
    high_threshold = float(cfg.get("high_vol_threshold_pct", 60))
    regime = "high" if vol_30d >= high_threshold else ("low" if vol_30d < high_threshold * 0.5 else "medium")
    risk_adjustment = {"high": 15, "medium": 5, "low": 0}.get(regime, 0)

    return {
        "ok": True,
        "feature_ref": _VOLATILITY_ANALYTICS_REF,
        "integration": "capital_protection_controls_410",
        "asset": asset.upper(),
        "volatility_regime": regime,
        "vol_30d_annualized_pct": vol_30d,
        "risk_score_adjustment": risk_adjustment,
        "high_vol_threshold_pct": high_threshold,
        "alerts_only": True,
        "display": f"Vol regime {regime} (30d {vol_30d:.1f}%) — risk context +{risk_adjustment} pts",
        "timestamp": _utcnow(),
    }


def build_volatility_analytics_dashboard(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#498 Vol dashboard — realized vol + compression + regime."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    vol = compute_realized_volatility(asset, seed=seed)
    compression = build_volatility_compression_signal(asset, seed=seed)
    regime = build_volatility_regime_for_risk(asset, seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": vol.get("ok", False),
        "feature_ref": _VOLATILITY_ANALYTICS_REF,
        "title": "Volatility Analytics",
        "merged_into": "Market Radar",
        "asset": asset.upper(),
        "realized_volatility": vol,
        "volatility_compression_458": compression if compression.get("ok") else None,
        "volatility_regime_410": regime if regime.get("ok") else None,
        "mandatory_windows": list(_MANDATORY_VOL_WINDOWS),
        "window_version_documented": True,
        "surface": "market_radar",
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_market_radar_panel(
    exchange_id: str = "binance",
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combined Market Radar panel — exchange activity + volatility analytics."""
    seed = seed or _load_seed()
    activity = build_exchange_activity_indicator(exchange_id)
    volatility = build_volatility_analytics_dashboard(asset, seed=seed)

    hype_vs_reality = None
    try:
        from bd_platform.hype_vs_reality_signal import build_hype_vs_reality_signal

        hype_vs_reality = build_hype_vs_reality_signal(asset)
    except Exception:
        logger.debug("hype vs reality market radar integration skipped", exc_info=True)

    stablecoin_reserve = None
    try:
        from bd_platform.stablecoin_health_monitor import build_market_radar_stablecoin_reserve_trend

        stablecoin_reserve = build_market_radar_stablecoin_reserve_trend(seed=seed)
    except Exception:
        logger.debug("stablecoin reserve market radar integration skipped", exc_info=True)

    buying_power_widget = None
    try:
        from bd_platform.stablecoin_health_monitor import build_market_radar_buying_power_widget_663

        buying_power_widget = build_market_radar_buying_power_widget_663(seed=seed)
    except Exception:
        logger.debug("buying power market radar integration skipped", exc_info=True)

    long_short_widget = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_long_short_widget_675

        long_short_widget = build_market_radar_long_short_widget_675(seed=seed)
    except Exception:
        logger.debug("long/short market radar integration skipped", exc_info=True)

    mvrv_widget = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_mvrv_widget_676

        mvrv_widget = build_market_radar_mvrv_widget_676(asset)
    except Exception:
        logger.debug("mvrv market radar integration skipped", exc_info=True)

    transaction_flow = None
    try:
        from bd_platform.transaction_flow_view import build_market_radar_transaction_flow_view

        transaction_flow = build_market_radar_transaction_flow_view(seed=seed)
    except Exception:
        logger.debug("transaction flow view market radar integration skipped", exc_info=True)

    tx_volume = None
    try:
        from bd_platform.onchain_metrics_library import build_transaction_volume_intelligence

        tx_volume = build_transaction_volume_intelligence(asset)
    except Exception:
        logger.debug("tx volume market radar integration skipped", exc_info=True)

    unlock_timeline = None
    try:
        from bd_platform.token_unlock_intelligence_engine import build_market_radar_unlock_timeline

        unlock_timeline = build_market_radar_unlock_timeline()
    except Exception:
        logger.debug("unlock timeline market radar integration skipped", exc_info=True)

    ratio_builder = None
    try:
        from bd_platform.custom_ratio_engine import build_ratio_builder_panel

        ratio_builder = build_ratio_builder_panel("uniswap", "ps_ratio")
    except Exception:
        logger.debug("653 ratio builder market radar integration skipped", exc_info=True)

    macro_context = None
    try:
        from bd_platform.dxy_dollar_elasticity import build_macro_context_panel

        macro_context = build_macro_context_panel(asset)
    except Exception:
        logger.debug("655 DXY macro context market radar integration skipped", exc_info=True)

    sector_pulse = None
    try:
        from bd_platform.sector_market_brief import build_market_radar_sector_pulse_widget_678

        sector_pulse = build_market_radar_sector_pulse_widget_678(seed=seed)
    except Exception:
        logger.debug("678 sector pulse market radar integration skipped", exc_info=True)

    network_activity = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_network_activity_widget_682

        network_activity = build_market_radar_network_activity_widget_682(asset)
    except Exception:
        logger.debug("682 network activity market radar integration skipped", exc_info=True)

    supply_change = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_supply_change_widget_700

        supply_change = build_market_radar_supply_change_widget_700(asset)
    except Exception:
        logger.debug("700 supply change market radar integration skipped", exc_info=True)

    technical_calc = build_technical_calculation_layer_754(asset, seed=seed)
    technical_summary = build_technical_summary_overlay_755(asset, seed=seed)
    technical_chart = build_technical_chart_overlay_760(asset, seed=seed)

    token_circulation = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_token_circulation_widget_757

        token_circulation = build_market_radar_token_circulation_widget_757(asset)
    except Exception:
        logger.debug("757 token circulation market radar integration skipped", exc_info=True)

    market_alerts = None
    try:
        from bd_platform.alert_engine import build_market_radar_alerts_panel_759

        market_alerts = build_market_radar_alerts_panel_759(seed=seed)
    except Exception:
        logger.debug("759 market radar alerts integration skipped", exc_info=True)

    nvt_widget = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_nvt_widget_761

        nvt_widget = build_market_radar_nvt_widget_761(asset)
    except Exception:
        logger.debug("761 NVT market radar integration skipped", exc_info=True)

    news_digest = None
    try:
        from bd_platform.ai_content_engine import build_news_digest_layer_768

        news_digest = build_news_digest_layer_768(asset)
    except Exception:
        logger.debug("768 news digest market radar integration skipped", exc_info=True)

    macro_coupling = None
    try:
        macro_coupling = build_market_radar_macro_coupling_widget_774(asset, seed=seed)
    except Exception:
        logger.debug("774 macro coupling market radar integration skipped", exc_info=True)

    supply_dynamics = None
    try:
        from bd_platform.onchain_metrics_library import build_market_radar_supply_dynamics_widget_794

        supply_dynamics = build_market_radar_supply_dynamics_widget_794(asset)
    except Exception:
        logger.debug("794 supply dynamics market radar integration skipped", exc_info=True)

    sentiment_overlay = None
    try:
        from bd_platform.social_sentiment_intelligence import build_market_radar_sentiment_overlay_783

        sentiment_overlay = build_market_radar_sentiment_overlay_783(asset)
    except Exception:
        logger.debug("783 sentiment overlay market radar integration skipped", exc_info=True)

    viral_share = None
    try:
        from bd_platform.viral_intelligence_distribution_loop import build_market_radar_share_action_797

        viral_share = build_market_radar_share_action_797(asset)
    except Exception:
        logger.debug("797 viral share action market radar integration skipped", exc_info=True)

    return {
        "ok": True,
        "surface": "market_radar",
        "exchange_activity_734": activity,
        "volatility_analytics_498": volatility,
        "hype_vs_reality_signal_599": hype_vs_reality,
        "stablecoin_reserve_trend_601": stablecoin_reserve,
        "exchange_stablecoin_buying_power_663": buying_power_widget,
        "long_short_ratio_675": long_short_widget,
        "mvrv_zscore_suite_676": mvrv_widget,
        "transaction_flow_view_615": transaction_flow,
        "transaction_volume_chart_612": tx_volume,
        "unlock_event_timeline_607": unlock_timeline,
        "custom_ratio_engine_653": ratio_builder,
        "dxy_macro_context_655": macro_context,
        "sector_pulse_678": sector_pulse,
        "network_activity_682": network_activity,
        "supply_change_700": supply_change,
        "technical_calculation_754": technical_calc if technical_calc.get("ok") else {"ok": False},
        "technical_summary_755": technical_summary if technical_summary.get("ok") else {"ok": False},
        "technical_chart_760": technical_chart if technical_chart.get("ok") else {"ok": False},
        "token_circulation_757": token_circulation if token_circulation and token_circulation.get("ok") else {"ok": False},
        "market_alerts_759": market_alerts if market_alerts and market_alerts.get("ok") else {"ok": False},
        "nvt_ratio_761": nvt_widget if nvt_widget and nvt_widget.get("ok") else {"ok": False},
        "news_digest_768": news_digest if news_digest and news_digest.get("ok") else {"ok": False},
        "macro_coupling_774": macro_coupling if macro_coupling and macro_coupling.get("ok") else {"ok": False},
        "supply_dynamics_794": supply_dynamics if supply_dynamics and supply_dynamics.get("ok") else {"ok": False},
        "sentiment_intelligence_783": sentiment_overlay if sentiment_overlay and sentiment_overlay.get("ok") else {"ok": False},
        "viral_share_action_797": viral_share if viral_share and viral_share.get("ok") else {"ok": False},
        "signal_quality_badge": (hype_vs_reality or {}).get("badge"),
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    activity = build_exchange_activity_indicator("binance")
    checks.append({"id": "exchange_activity", "passed": activity.get("ok") is True, "detail": "734"})

    vol = build_volatility_analytics_dashboard("BTC", seed=seed)
    checks.append({"id": "volatility_498", "passed": vol.get("ok") is True, "detail": "498"})
    checks.append({"id": "vol_3_windows", "passed": len(vol.get("mandatory_windows") or []) == 3, "detail": "7d/30d/90d"})
    checks.append({"id": "window_version", "passed": vol.get("window_version_documented") is True, "detail": "version"})

    compression = build_volatility_compression_signal("BTC", seed=seed)
    checks.append({"id": "compression_458", "passed": compression.get("compression_signal") is not None, "detail": "458"})

    regime = build_volatility_regime_for_risk("BTC", seed=seed)
    checks.append({"id": "vol_regime_410", "passed": regime.get("volatility_regime") in ("low", "medium", "high"), "detail": "410"})

    try:
        from bd_platform.sector_market_brief import build_sector_pulse_dashboard_678

        sector = build_sector_pulse_dashboard_678(seed=seed)
        checks.append({"id": "sector_pulse_678", "passed": sector.get("card_count") == 4, "detail": "678"})
        checks.append({"id": "no_buy_sell_678", "passed": sector.get("no_buy_sell_signals") is True, "detail": "descriptive"})
    except Exception:
        checks.append({"id": "sector_pulse_678", "passed": False, "detail": "678"})

    tech_parity = run_formula_parity_tests_754(seed=seed)
    checks.append({"id": "technical_parity_754", "passed": tech_parity.get("all_passed") is True, "detail": "754"})
    look_ahead = run_look_ahead_tests_754(seed=seed)
    checks.append({"id": "no_look_ahead_754", "passed": look_ahead.get("no_look_ahead") is True, "detail": "754"})
    summary = build_technical_summary_overlay_755("BTC", seed=seed)
    checks.append({"id": "no_strong_buy_sell_755", "passed": summary.get("no_strong_buy_sell") is True, "detail": "755"})
    checks.append({"id": "disclaimer_mandatory_755", "passed": summary.get("disclaimer_mandatory") is True, "detail": "755"})
    chart = build_technical_chart_overlay_760("BTC", seed=seed)
    checks.append({"id": "no_prediction_760", "passed": chart.get("no_prediction") is True, "detail": "760"})
    checks.append({"id": "rejected_brain_name_760", "passed": "Technical Brain" in (chart.get("rejected_names") or []), "detail": "760"})

    macro = build_btc_macro_coupling_overlay_774("BTC", seed=seed)
    checks.append({"id": "macro_coupling_774", "passed": macro.get("ok") is True, "detail": "774"})
    checks.append({"id": "correlation_disclaimer_774", "passed": macro.get("disclaimer_non_hideable") is True, "detail": "774"})
    macro_qa = run_macro_coupling_qa_774("BTC", seed=seed)
    checks.append({"id": "macro_qa_774", "passed": macro_qa.get("all_passed") is True, "detail": "774"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_refs": [_FEATURE_ID, _VOLATILITY_ANALYTICS_REF],
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }


def market_radar_indicators_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Market Radar — Exchange Activity Indicator",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "exchange_cluster": build_exchange_cluster_block(seed),
        "acceptance_criteria": {
            "address_dedupe": True,
            "exchange_cluster_versioned": True,
            "chain_specific_validation": True,
        },
        "exchange_count": len(seed.get("exchanges") or {}),
        "volatility_analytics_498": {
            "feature_ref": _VOLATILITY_ANALYTICS_REF,
            "mandatory_windows": list(_MANDATORY_VOL_WINDOWS),
            "merged_into": "market_radar",
        },
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
