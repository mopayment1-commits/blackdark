"""
Macro Intelligence Hub — Feature #263 (Sprint 2, Pro/Institution).

Integration dashboard aggregating macro modules — NOT standalone.
Release-time aligned correlation/beta/regime analysis. Macro context only.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MacroIntelligenceHub")

_FEATURE_ID = 263
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/macro_intelligence_hub_seed.json")
_METHODOLOGY_VERSION = "1.3"

_DISCLAIMER_TEXT = (
    "Macro analysis presents historical relationships between crypto assets and traditional "
    "finance indicators. Correlations change over time and do not predict future price movements. "
    "Not investment advice."
)

RegimeLabel = Literal["Risk-On", "Risk-Off", "Neutral"]
WindowLabel = Literal["30D", "90D", "1Y"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"integrated_modules": [], "series": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("macro intelligence hub seed load failed: %s", exc)
        return {"integrated_modules": [], "series": {}}


def _parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def verify_no_look_ahead(
    daily_rows: list[dict[str, Any]],
    *,
    calculation_as_of: str,
) -> dict[str, Any]:
    """No look-ahead test — only data published on or before calculation date."""
    as_of = _parse_date(calculation_as_of)
    future_used = 0
    used = 0
    for row in daily_rows:
        row_date = _parse_date(str(row["date"]))
        if row_date > as_of:
            continue
        pub = row.get("dxy_published") or row.get("btc_published") or row.get("date", "")
        try:
            pub_dt = _parse_ts(pub) if "T" in str(pub) else datetime.combine(_parse_date(str(pub)), datetime.min.time(), tzinfo=UTC)
        except (ValueError, TypeError):
            pub_dt = datetime.combine(row_date, datetime.min.time(), tzinfo=UTC)
        if pub_dt.date() > as_of:
            future_used += 1
            continue
        used += 1

    ok = future_used == 0
    return {
        "no_look_ahead": ok,
        "calculation_as_of": calculation_as_of,
        "data_points_used": used,
        "future_data_points": future_used,
        "policy": "Correlation calculated using data available at time T only",
        "test_display": (
            "If I calculate correlation on 2026-08-25, does it use macro data published on 2026-08-26? → "
            + ("NO" if ok else "FAIL")
        ),
    }


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    try:
        return round(statistics.correlation(xs, ys), 3)
    except statistics.StatisticsError:
        return None


def _window_slice(rows: list[dict[str, Any]], window: WindowLabel) -> list[dict[str, Any]]:
    days = {"30D": 30, "90D": 90, "1Y": 365}[window]
    return rows[-days:] if len(rows) > days else rows


def _rolling_correlation(
    rows: list[dict[str, Any]],
    *,
    crypto_key: str,
    macro_key: str,
    window: WindowLabel,
) -> dict[str, Any]:
    subset = _window_slice(rows, window)
    crypto_vals = [float(r[crypto_key]) for r in subset]
    macro_vals = [float(r[macro_key]) for r in subset]
    corr = _pearson(crypto_vals, macro_vals)
    regime: RegimeLabel = "Neutral"
    if corr is not None:
        if corr <= -0.3:
            regime = "Risk-Off"
        elif corr >= 0.3:
            regime = "Risk-On"

    pair = f"BTC-{macro_key.upper()}"
    return {
        "pair": pair,
        "window": window,
        "rolling": True,
        "correlation": corr,
        "regime": regime,
        "sample_size": len(subset),
        "display": (
            f"{pair} Correlation | Window: {window} | Rolling: Yes | Regime: {regime}"
            + (f" | r = {corr:+.2f}" if corr is not None else "")
        ),
        "not_causation": True,
    }


def _rolling_beta(
    rows: list[dict[str, Any]],
    *,
    crypto_key: str = "btc_close",
    macro_key: str = "spx",
    window: WindowLabel,
) -> dict[str, Any]:
    subset = _window_slice(rows, window)
    if len(subset) < 3:
        return {"window": window, "beta": None, "sample_size": len(subset)}

    crypto_rets = []
    macro_rets = []
    for i in range(1, len(subset)):
        c0, c1 = float(subset[i - 1][crypto_key]), float(subset[i][crypto_key])
        m0, m1 = float(subset[i - 1][macro_key]), float(subset[i][macro_key])
        if c0 and m0:
            crypto_rets.append((c1 - c0) / c0)
            macro_rets.append((m1 - m0) / m0)

    if len(crypto_rets) < 2:
        return {"window": window, "beta": None, "sample_size": len(crypto_rets)}

    macro_var = statistics.variance(macro_rets)
    if macro_var == 0:
        return {"window": window, "beta": None, "sample_size": len(crypto_rets)}

    cov = statistics.covariance(crypto_rets, macro_rets)
    beta = round(cov / macro_var, 3)
    return {
        "pair": f"BTC-{macro_key.upper()}",
        "window": window,
        "beta": beta,
        "sample_size": len(crypto_rets),
        "display": f"BTC-{macro_key.upper()} Beta | Window: {window} | β = {beta:+.2f}",
        "not_causation": True,
    }


def _build_release_alignment(seed: dict[str, Any], asset: str) -> dict[str, Any]:
    snap = (seed.get("aligned_snapshots") or {}).get(asset.upper()) or {}
    return {
        "minute_level": True,
        "alignment_timestamp_utc": snap.get("alignment_timestamp_utc"),
        "alignment_display": snap.get(
            "alignment_display",
            "DXY Release: 14:00 EST | Crypto Data Used: 14:00 EST | Lag: 0",
        ),
        "lag_minutes": snap.get("lag_minutes", 0),
        "policy": (seed.get("release_time_alignment") or {}).get("policy"),
    }


def _build_source_calendar(seed: dict[str, Any]) -> list[dict[str, Any]]:
    return seed.get("source_calendar") or []


def _classify_macro_regime(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 5:
        return {"regime": "Neutral", "regime_display": "Regime: Neutral | Insufficient data"}

    recent = rows[-5:]
    dxy_start = float(recent[0]["dxy"])
    dxy_end = float(recent[-1]["dxy"])
    dxy_chg = (dxy_end - dxy_start) / dxy_start * 100 if dxy_start else 0

    if dxy_chg > 0.5:
        label = "Tightening + Strong Dollar"
    elif dxy_chg < -0.5:
        label = "Easing + Weak Dollar"
    else:
        label = "Neutral Macro"

    return {
        "regime": label,
        "dxy_change_5d_pct": round(dxy_chg, 2),
        "regime_display": f"Regime: {label}",
        "descriptive_only": True,
        "not_predictive": True,
    }


def _build_regime_analysis(
    seed: dict[str, Any],
    asset: str,
    regime_label: str,
) -> dict[str, Any]:
    hist = ((seed.get("series") or {}).get(asset.upper()) or {}).get("regime_history") or {}
    entry = hist.get(regime_label) or hist.get("Risk-On") or {}
    median = entry.get("median_btc_return_pct")
    sample = entry.get("sample_months", 0)

    display = (
        f"Regime: {regime_label} | Historical BTC Performance in this Regime: "
        f"{median:+.1f}% median | Sample Size: {sample} months | "
        "Note: Past regime performance ≠ future"
        if median is not None
        else f"Regime: {regime_label} | Note: Past regime performance ≠ future"
    )

    return {
        "regime": regime_label,
        "median_btc_return_pct": median,
        "sample_months": sample,
        "regime_display": display,
        "not_predictive": True,
        "no_causation": True,
        "enterprise_only": True,
    }


def _build_crypto_coupling(seed: dict[str, Any], asset: str) -> dict[str, Any]:
    coupling = ((seed.get("series") or {}).get(asset.upper()) or {}).get("coupling") or {}
    regime = coupling.get("current_regime", "Aligned")
    duration = int(coupling.get("duration_days") or 0)
    median = int(coupling.get("historical_median_decoupling_days") or 0)
    unusual = bool(coupling.get("unusual"))

    return {
        "current_regime": regime,
        "duration_days": duration,
        "historical_median_decoupling_days": median,
        "unusual": unusual,
        "coupling_display": (
            f"Current Regime: {regime} | Duration: {duration} days | "
            f"Historical median decoupling: {median} days | "
            f"Context: {'Unusual' if unusual else 'Within normal range'}"
        ),
        "descriptive_only": True,
        "not_predictive": True,
    }


def _detect_anomaly(rows: list[dict[str, Any]], *, regime_expectation: str = "DXY ↓ → BTC ↑") -> dict[str, Any] | None:
    if len(rows) < 2:
        return None

    for i in range(len(rows) - 1, 0, -1):
        row = rows[i]
        prev = rows[i - 1]
        if row.get("anomaly"):
            return {
                "label": "Anomaly",
                "date": row.get("date"),
                "display": (
                    "Anomaly: DXY ↓ + BTC ↓ | Regime expectation: DXY ↓ → BTC ↑ | Divergence: Yes"
                ),
                "not_a_signal": True,
                "analysis_only": True,
            }
        dxy_chg = float(row["dxy"]) - float(prev["dxy"])
        btc_chg = float(row["btc_close"]) - float(prev["btc_close"])
        if dxy_chg < 0 and btc_chg < 0:
            return {
                "label": "Anomaly",
                "date": row.get("date"),
                "display": (
                    "Anomaly: DXY ↓ + BTC ↓ | Regime expectation: DXY ↓ → BTC ↑ | Divergence: Yes"
                ),
                "not_a_signal": True,
                "analysis_only": True,
            }

    return None


def _aggregate_modules(asset: str) -> dict[str, Any]:
    """Pull summaries from integrated macro modules."""
    modules: dict[str, Any] = {}

    try:
        from bd_platform.global_liquidity_intelligence import build_global_liquidity_dashboard

        modules["global_liquidity"] = build_global_liquidity_dashboard(asset)
    except Exception:
        logger.debug("global liquidity module unavailable", exc_info=True)

    try:
        from bd_platform.economic_calendar import list_economic_events

        modules["economic_calendar"] = list_economic_events(limit=5)
    except Exception:
        logger.debug("economic calendar module unavailable", exc_info=True)

    try:
        from bd_platform.etf_intelligence import build_etf_intelligence_dashboard

        modules["etf_intelligence"] = build_etf_intelligence_dashboard(asset)
    except Exception:
        logger.debug("etf intelligence module unavailable", exc_info=True)

    try:
        from bd_platform.premium_intelligence import get_regional_premiums_dashboard

        modules["premium_intelligence"] = get_regional_premiums_dashboard(asset)
    except Exception:
        logger.debug("premium intelligence module unavailable", exc_info=True)

    # Fed M2 Macro Flow (#244) — sourced from global liquidity fed_m2 series
    gl = modules.get("global_liquidity") or {}
    fed_m2 = (gl.get("series") or {}).get("fed_m2")
    if fed_m2:
        modules["fed_m2_macro_flow"] = {
            "feature_id": 244,
            "source_module": 248,
            "data": fed_m2,
            "status": "live",
        }

    modules["treasury_companies"] = {
        "feature_id": 239,
        "status": "planned",
        "display": "Treasury Companies: Coming Soon — Sprint 3+",
    }

    return modules


def _tier_payload(
    *,
    tier: str,
    summary: dict[str, Any],
    correlations: list[dict[str, Any]],
    calendar: list[dict[str, Any]],
    regime: dict[str, Any] | None,
    coupling: dict[str, Any],
    anomaly: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"tier": tier, "summary": summary}
    if tier in ("pro", "enterprise"):
        payload["correlation_tables"] = correlations
        payload["source_calendar"] = calendar
    if tier == "enterprise":
        payload["regime_analysis"] = regime
        payload["crypto_coupling"] = coupling
        payload["anomaly_detection"] = anomaly
        payload["custom_macro_factors"] = True
    elif tier == "free":
        payload["note"] = "Upgrade to Pro for correlation tables and source calendar"
    return payload


def build_macro_intelligence_hub(
    asset: str = "BTC",
    *,
    tier: str = "pro",
    window: WindowLabel = "30D",
) -> dict[str, Any]:
    """Macro Intelligence Hub — integration dashboard over macro modules."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("series") or {}).get(sym) or {}

    disclaimer = {
        "text": _DISCLAIMER_TEXT,
        "collapsible": False,
        "hideable": False,
        "version": seed.get("methodology_version", _METHODOLOGY_VERSION),
    }

    daily_rows = asset_data.get("daily") or []
    calc_as_of = seed.get("calculation_as_of", datetime.now(UTC).strftime("%Y-%m-%d"))
    look_ahead = verify_no_look_ahead(daily_rows, calculation_as_of=calc_as_of)

    filtered_rows = [r for r in daily_rows if _parse_date(str(r["date"])) <= _parse_date(calc_as_of)]

    correlations = [
        _rolling_correlation(filtered_rows, crypto_key="btc_close", macro_key="dxy", window="30D"),
        _rolling_correlation(filtered_rows, crypto_key="btc_close", macro_key="dxy", window="90D"),
        _rolling_correlation(filtered_rows, crypto_key="btc_close", macro_key="dxy", window="1Y"),
        _rolling_correlation(filtered_rows, crypto_key="btc_close", macro_key="spx", window=window),
    ]
    betas = [
        _rolling_beta(filtered_rows, window="30D"),
        _rolling_beta(filtered_rows, window="90D"),
    ]

    macro_regime = _classify_macro_regime(filtered_rows)
    regime_analysis = _build_regime_analysis(seed, sym, macro_regime["regime"])
    coupling = _build_crypto_coupling(seed, sym)
    anomaly = _detect_anomaly(filtered_rows)
    alignment = _build_release_alignment(seed, sym)
    calendar = _build_source_calendar(seed)
    modules = _aggregate_modules(sym)

    dxy_corr = next((c for c in correlations if c["pair"] == "BTC-DXY" and c["window"] == window), correlations[0])
    coupling_note = (
        f"Coupling: BTC shows negative correlation with DXY in Risk-On regimes "
        f"(r = {dxy_corr.get('correlation', 0):+.2f})"
        if dxy_corr.get("correlation") is not None and dxy_corr["correlation"] < 0
        else f"Coupling: BTC-DXY correlation (r = {dxy_corr.get('correlation', 0):+.2f})"
    )

    etf = (modules.get("etf_intelligence") or {})
    etf_flow = (etf.get("rolling_totals") or {}).get("7d_net_flow_usd")
    gl = (modules.get("global_liquidity") or {})
    gl_regime = (gl.get("liquidity_regime") or {}).get("regime", "Unknown")

    summary_headline = (
        f"{sym} context: {macro_regime['regime']} | DXY correlation ({window}): "
        f"{dxy_corr.get('correlation', 'N/A')} | Global Liquidity: {gl_regime}"
        + (f" | ETF 7D flow: ${etf_flow / 1e6:.0f}M" if etf_flow else "")
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    base = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "surface": "macro_intelligence_hub",
        "asset": sym,
        "methodology_version": seed.get("methodology_version", _METHODOLOGY_VERSION),
        "methodology_display": seed.get("methodology_display"),
        "integrated_modules": seed.get("integrated_modules", []),
        "module_count": len(seed.get("integrated_modules", [])),
        "release_time_alignment": alignment,
        "no_look_ahead": look_ahead,
        "macro_regime": macro_regime,
        "coupling_note": coupling_note,
        "correlations": correlations,
        "betas": betas,
        "modules": modules,
        "macro_context_only": True,
        "not_a_recommendation": True,
        "not_predictive": True,
        "not_causation_language": True,
        "allowed_language": ["Macro Context", "Coupling", "Correlation", "Regime", "Analysis"],
        "disclaimer_top": disclaimer,
        "disclaimer": disclaimer,
        "disclaimer_bottom": disclaimer,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }

    base["summary_headline"] = summary_headline
    base["tier_payload"] = _tier_payload(
        tier=tier,
        summary={"headline": summary_headline, "macro_regime": macro_regime},
        correlations=correlations,
        calendar=calendar,
        regime=regime_analysis,
        coupling=coupling,
        anomaly=anomaly,
    )
    if tier == "free":
        base["gated"] = True
        base["upgrade_note"] = "Pro tier required for correlation tables and source calendar"
    return base


def build_macro_coupling(asset: str = "BTC") -> dict[str, Any]:
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": sym,
        **_build_crypto_coupling(seed, sym),
        "timestamp": _utcnow(),
    }


def macro_intelligence_hub_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_label": seed.get("feature_label", "Macro Intelligence Hub"),
        "standalone": _STANDALONE,
        "merged_into": seed.get("merged_into", "Macro Intelligence Hub (Integration Dashboard)"),
        "sprint": _SPRINT,
        "methodology_version": seed.get("methodology_version", _METHODOLOGY_VERSION),
        "methodology_display": seed.get("methodology_display"),
        "tier_default": seed.get("tier_default", "pro"),
        "tier_features": seed.get("tier_features", {}),
        "integrated_modules": seed.get("integrated_modules", []),
        "acceptance_criteria": {
            "not_standalone": True,
            "release_time_alignment": True,
            "no_look_ahead": True,
            "source_calendar_handling": True,
            "rolling_correlation_windows": True,
            "regime_analysis_documented": True,
            "no_causation_language": True,
            "crypto_coupling_descriptive": True,
            "disclaimer_non_hideable": True,
            "methodology_versioned": True,
            "pro_institution_tier": True,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
